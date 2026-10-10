"""Convert recorded chat messages into shiftpoint turns and signals."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import cast

from shiftpoint_core.bash import classify_command
from shiftpoint_core.events import Action, ActionKind, Turn
from shiftpoint_core.signals import Signals, extract

from shiftpoint_replay.twinrouterbench import Message, Step, ToolCall

_RETURNCODE = re.compile(r"^\s*<returncode>(-?\d+)</returncode>")
_SHELL_TOOLS = frozenset({"bash", "exec", "shell"})
_NAMED_TOOLS: dict[str, ActionKind] = {
    "read": "read",
    "write": "edit",
    "edit": "edit",
    "grep": "search",
    "glob": "search",
}
_PATH_KEYS = ("path", "file_path", "filename")

# SWE-bench trajectories run inside /testbed.
DEFAULT_ROOT = "/testbed"


def _arguments(call: ToolCall) -> dict[str, object]:
    try:
        parsed: object = json.loads(call.arguments)
    except json.JSONDecodeError:
        return {}
    return cast(dict[str, object], parsed) if isinstance(parsed, dict) else {}


def _outcome(result: Message | None) -> bool | None:
    if result is None:
        return None
    match = _RETURNCODE.match(result.content)
    if match:
        return match.group(1) == "0"
    if result.content.lstrip().startswith("<exception>"):
        return False
    return None


def _action(call: ToolCall, result: Message | None, root: str | None) -> Action:
    args = _arguments(call)
    ok = _outcome(result)
    command = args.get("command")
    if call.name in _SHELL_TOOLS and isinstance(command, str):
        classified = classify_command(command, root)
        return Action(classified.kind, classified.paths, ok)
    kind = _NAMED_TOOLS.get(call.name, "other")
    paths = frozenset(v for k in _PATH_KEYS if isinstance(v := args.get(k), str))
    return Action(kind, paths, ok)


def turns_from_messages(messages: Sequence[Message], root: str | None = DEFAULT_ROOT) -> list[Turn]:
    """One turn per assistant message, with outcomes joined from tool results."""
    results = {m.tool_call_id: m for m in messages if m.role == "tool" and m.tool_call_id}
    return [
        Turn(tuple(_action(c, results.get(c.id), root) for c in m.tool_calls))
        for m in messages
        if m.role == "assistant"
    ]


def step_signals(step: Step, root: str | None = DEFAULT_ROOT) -> Signals:
    """Signals visible to a router at this step (its message prefix only)."""
    return extract(turns_from_messages(step.messages, root))
