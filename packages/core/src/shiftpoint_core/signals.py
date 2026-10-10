"""Scope signals computed from a session's turns (no LLM, no content).

See docs/ARCHITECTURE.md for what each signal is meant to capture.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from shiftpoint_core.events import Turn

# Turns considered "recent" for decay and read/write balance.
RECENT_TURNS = 2


@dataclass(frozen=True, slots=True)
class Signals:
    turns: int
    actions: int
    reads: int
    searches: int
    edits: int
    tests: int
    runs: int
    files_seen: int  # distinct paths read or searched
    new_files_recent: int  # paths first seen in the last RECENT_TURNS turns
    exploration_decay: float  # 0 = still discovering at peak rate, 1 = stopped
    rw_flip: bool  # recent edits outnumber recent reads + searches
    has_edit: bool
    first_verify: bool  # a test or run happened after the first edit
    touch_set_size: int  # distinct edited paths
    touch_set_stable: bool  # edits exist and the last turn added no new edited path
    out_of_set_touch: int  # new edited paths introduced after the first verify
    failure_streak: int  # consecutive failed actions at the end
    turns_since_first_edit: int  # -1 before any edit

    def as_dict(self) -> dict[str, int | float | bool]:
        return asdict(self)


def extract(turns: Sequence[Turn]) -> Signals:
    """Compute signals over all turns so far (the prefix before the next call)."""
    counts = {"read": 0, "search": 0, "edit": 0, "test": 0, "run": 0, "other": 0}
    seen: set[str] = set()
    new_per_turn: list[int] = []
    touch: set[str] = set()
    first_edit_turn = -1
    verified = False
    out_of_set = 0
    last_turn_new_edit = False
    outcomes: list[bool] = []

    for i, turn in enumerate(turns):
        new_here = 0
        last_turn_new_edit = False
        for action in turn.actions:
            counts[action.kind] += 1
            if action.ok is not None:
                outcomes.append(action.ok)
            if action.kind in ("read", "search"):
                fresh = action.paths - seen
                new_here += len(fresh)
                seen |= fresh
            elif action.kind == "edit":
                if first_edit_turn < 0:
                    first_edit_turn = i
                fresh = action.paths - touch
                if fresh:
                    last_turn_new_edit = True
                    if verified:
                        out_of_set += len(fresh)
                touch |= fresh
            elif action.kind in ("test", "run") and first_edit_turn >= 0:
                verified = True
        new_per_turn.append(new_here)

    recent = turns[-RECENT_TURNS:]
    recent_edits = sum(1 for t in recent for a in t.actions if a.kind == "edit")
    recent_reads = sum(1 for t in recent for a in t.actions if a.kind in ("read", "search"))
    new_recent = sum(new_per_turn[-RECENT_TURNS:])
    peak = max(new_per_turn, default=0)
    if peak == 0:
        decay = 0.0
    else:
        recent_rate = new_recent / max(1, min(RECENT_TURNS, len(new_per_turn)))
        decay = max(0.0, 1.0 - recent_rate / peak)

    streak = 0
    for ok in reversed(outcomes):
        if ok:
            break
        streak += 1

    return Signals(
        turns=len(turns),
        actions=sum(counts.values()),
        reads=counts["read"],
        searches=counts["search"],
        edits=counts["edit"],
        tests=counts["test"],
        runs=counts["run"],
        files_seen=len(seen),
        new_files_recent=new_recent,
        exploration_decay=round(decay, 4),
        rw_flip=recent_edits > recent_reads,
        has_edit=first_edit_turn >= 0,
        first_verify=verified,
        touch_set_size=len(touch),
        touch_set_stable=bool(touch) and not last_turn_new_edit,
        out_of_set_touch=out_of_set,
        failure_streak=streak,
        turns_since_first_edit=len(turns) - 1 - first_edit_turn if first_edit_turn >= 0 else -1,
    )
