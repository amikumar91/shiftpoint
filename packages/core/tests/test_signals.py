import pytest
from shiftpoint_core.events import Action, Turn
from shiftpoint_core.signals import extract


def read(*paths: str) -> Action:
    return Action("read", frozenset(paths), ok=True)


def edit(*paths: str) -> Action:
    return Action("edit", frozenset(paths), ok=True)


def run(ok: bool = True) -> Action:
    return Action("run", ok=ok)


def test_empty_prefix() -> None:
    s = extract([])

    assert s.turns == 0
    assert s.exploration_decay == 0.0
    assert not s.has_edit
    assert s.turns_since_first_edit == -1
    assert not s.touch_set_stable


def test_exploration_decay_uses_peak_discovery_rate() -> None:
    turns = [Turn((read("a", "b", "c"),)), Turn((read("a", "d"),)), Turn((read("b"),))]

    s = extract(turns)

    assert s.files_seen == 4
    assert s.new_files_recent == 1
    assert s.exploration_decay == pytest.approx(1 - 0.5 / 3, abs=1e-4)


def test_edit_then_verify_session() -> None:
    turns = [
        Turn((read("a.py"),)),
        Turn((edit("a.py"),)),
        Turn((run(),)),
        Turn((edit("b.py"), edit("a.py"))),
        Turn((run(ok=False), run(ok=False))),
    ]

    s = extract(turns)

    assert (s.reads, s.edits, s.runs) == (1, 3, 3)
    assert s.has_edit and s.first_verify
    assert s.touch_set_size == 2
    assert s.out_of_set_touch == 1
    assert s.touch_set_stable
    assert s.failure_streak == 2
    assert s.turns_since_first_edit == 3


def test_rw_flip_compares_recent_turns_only() -> None:
    turns = [Turn((read("a"), read("b"), read("c"))), Turn((edit("a"),)), Turn((edit("b"),))]

    assert extract(turns).rw_flip


def test_run_before_any_edit_is_not_verification() -> None:
    assert not extract([Turn((run(),))]).first_verify


def test_as_dict_is_flat() -> None:
    d = extract([Turn((read("a"),))]).as_dict()

    assert d["reads"] == 1
    assert all(isinstance(v, int | float | bool) for v in d.values())
