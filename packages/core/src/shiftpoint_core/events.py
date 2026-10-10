"""Harness-agnostic view of an agent session: turns made of tool actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# read: inspect known files; search: locate files/symbols; edit: change files;
# test: run a test suite; run: execute code/scripts; other: anything else.
ActionKind = Literal["read", "search", "edit", "test", "run", "other"]


@dataclass(frozen=True, slots=True)
class Action:
    kind: ActionKind
    paths: frozenset[str] = frozenset()
    ok: bool | None = None  # None when the outcome is unknown


@dataclass(frozen=True, slots=True)
class Turn:
    """The tool actions issued by one model call."""

    actions: tuple[Action, ...] = ()
