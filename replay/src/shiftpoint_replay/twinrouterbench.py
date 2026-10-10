"""Loader for the TwinRouterBench static question bank.

Dataset: https://huggingface.co/datasets/Amorph/TwinRouterBench (Apache-2.0).
Each record is one model call ("step") of an agent trajectory: the
router-visible message prefix plus the execution-verified target tier.
Schema notes and quirks: docs/DATASETS.md.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Collection, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from shiftpoint_core.tiers import Tier

Role = Literal["system", "user", "assistant", "tool"]
_ROLES: frozenset[str] = frozenset({"system", "user", "assistant", "tool"})

# Benchmarks whose records form multi-step agent trajectories.
MULTI_STEP_BENCHMARKS: tuple[str, ...] = ("swebench", "pinchbench")


class SchemaError(ValueError):
    """A record does not match the expected question-bank schema."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: str  # raw JSON string, as emitted by the agent


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str  # text parts joined with newlines; "" when absent
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None


@dataclass(frozen=True, slots=True)
class Step:
    id: str
    benchmark: str
    instance_id: str
    step_index: int  # 1-based
    total_steps: int
    tier: Tier
    messages: tuple[Message, ...]


@dataclass(frozen=True, slots=True)
class Trajectory:
    benchmark: str
    instance_id: str
    steps: tuple[Step, ...]

    @property
    def tiers(self) -> tuple[Tier, ...]:
        return tuple(step.tier for step in self.steps)


def _as_dict(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SchemaError(f"{where}: expected object, got {type(value).__name__}")
    return cast(dict[str, object], value)


def _as_list(value: object, where: str) -> list[object]:
    if not isinstance(value, list):
        raise SchemaError(f"{where}: expected array, got {type(value).__name__}")
    return cast(list[object], value)


def _str(record: dict[str, object], key: str, where: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise SchemaError(f"{where}.{key}: expected string, got {type(value).__name__}")
    return value


def _int(record: dict[str, object], key: str, where: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SchemaError(f"{where}.{key}: expected integer, got {type(value).__name__}")
    return value


def _content(value: object, where: str) -> str:
    """Normalize message content: a string, null, or a list of typed parts."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    texts: list[str] = []
    for i, raw_part in enumerate(_as_list(value, where)):
        part = _as_dict(raw_part, f"{where}[{i}]")
        if part.get("type") == "text":
            texts.append(_str(part, "text", f"{where}[{i}]"))
    return "\n".join(texts)


def _tool_call(value: object, where: str) -> ToolCall:
    call = _as_dict(value, where)
    function = _as_dict(call.get("function"), f"{where}.function")
    return ToolCall(
        id=_str(call, "id", where),
        name=_str(function, "name", f"{where}.function"),
        arguments=_str(function, "arguments", f"{where}.function"),
    )


def _message(value: object, where: str) -> Message:
    msg = _as_dict(value, where)
    role = _str(msg, "role", where)
    if role not in _ROLES:
        raise SchemaError(f"{where}.role: unknown role {role!r}")
    raw_calls = msg.get("tool_calls")
    calls = (
        ()
        if raw_calls is None
        else tuple(
            _tool_call(c, f"{where}.tool_calls[{i}]")
            for i, c in enumerate(_as_list(raw_calls, f"{where}.tool_calls"))
        )
    )
    raw_call_id = msg.get("tool_call_id")
    if raw_call_id is not None and not isinstance(raw_call_id, str):
        raise SchemaError(f"{where}.tool_call_id: expected string")
    return Message(
        role=cast(Role, role),
        content=_content(msg.get("content"), f"{where}.content"),
        tool_calls=calls,
        tool_call_id=raw_call_id,
    )


def parse_step(value: object, where: str = "record") -> Step:
    """Parse one question-bank record into a :class:`Step`."""
    rec = _as_dict(value, where)
    try:
        tier = Tier.from_label(_str(rec, "target_tier", where))
    except ValueError as exc:
        raise SchemaError(f"{where}.target_tier: {exc}") from None
    tier_id = _int(rec, "target_tier_id", where)
    if tier_id != tier.value:
        raise SchemaError(f"{where}: target_tier {tier.label!r} does not match id {tier_id}")
    messages = tuple(
        _message(m, f"{where}.messages[{i}]")
        for i, m in enumerate(_as_list(rec.get("messages"), f"{where}.messages"))
    )
    return Step(
        id=_str(rec, "id", where),
        benchmark=_str(rec, "benchmark", where),
        instance_id=_str(rec, "instance_id", where),
        step_index=_int(rec, "step_index", where),
        total_steps=_int(rec, "total_steps", where),
        tier=tier,
        messages=messages,
    )


def iter_steps(path: Path) -> Iterator[Step]:
    """Yield every record in a question-bank JSONL file."""
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            where = f"{path.name}:{lineno}"
            try:
                raw: object = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SchemaError(f"{where}: invalid JSON ({exc.msg})") from None
            yield parse_step(raw, where)


def load_trajectories(
    path: Path, benchmarks: Collection[str] = MULTI_STEP_BENCHMARKS
) -> list[Trajectory]:
    """Group steps into trajectories, sorted by (benchmark, instance_id).

    Raises :class:`SchemaError` unless every trajectory has exactly the steps
    ``1..total_steps``.
    """
    grouped: defaultdict[tuple[str, str], list[Step]] = defaultdict(list)
    for step in iter_steps(path):
        if step.benchmark in benchmarks:
            grouped[(step.benchmark, step.instance_id)].append(step)

    trajectories: list[Trajectory] = []
    for (benchmark, instance_id), steps in sorted(grouped.items()):
        steps.sort(key=lambda s: s.step_index)
        expected = list(range(1, len(steps) + 1))
        indices = [s.step_index for s in steps]
        totals = {s.total_steps for s in steps}
        if indices != expected or totals != {len(steps)}:
            raise SchemaError(
                f"{benchmark}/{instance_id}: step indices {indices} "
                f"inconsistent with total_steps {sorted(totals)}"
            )
        trajectories.append(Trajectory(benchmark, instance_id, tuple(steps)))
    return trajectories
