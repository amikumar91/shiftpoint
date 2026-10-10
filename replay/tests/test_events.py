import json
from collections import Counter

import pytest
from shiftpoint_replay.download import DEFAULT_DEST, FILENAME
from shiftpoint_replay.events import step_signals, turns_from_messages
from shiftpoint_replay.twinrouterbench import Message, ToolCall, load_trajectories


def call(id_: str, name: str, **args: str) -> ToolCall:
    return ToolCall(id=id_, name=name, arguments=json.dumps(args))


def test_bash_calls_are_classified_with_outcomes() -> None:
    messages = [
        Message("system", "agent"),
        Message("user", "fix it"),
        Message(
            "assistant",
            "",
            (
                call("1", "bash", command="sed -n '1,9p' /testbed/a.py"),
                call("2", "bash", command="python repro.py"),
            ),
        ),
        Message("tool", "<returncode>0</returncode>\n<output>x</output>", tool_call_id="1"),
        Message("tool", "<returncode>1</returncode>\n<output>boom</output>", tool_call_id="2"),
    ]

    (turn,) = turns_from_messages(messages)

    assert [a.kind for a in turn.actions] == ["read", "run"]
    assert turn.actions[0].paths == {"a.py"}
    assert [a.ok for a in turn.actions] == [True, False]


def test_named_tools_and_missing_results() -> None:
    messages = [
        Message("assistant", "", (call("r", "read", path="src/x.py"),)),
        Message("assistant", "", (call("w", "write", file_path="src/y.py"),)),
        Message("assistant", "thinking"),
    ]

    turns = turns_from_messages(messages)

    assert [[a.kind for a in t.actions] for t in turns] == [["read"], ["edit"], []]
    assert turns[0].actions[0].ok is None


REAL_BANK = DEFAULT_DEST / FILENAME


@pytest.mark.skipif(not REAL_BANK.exists(), reason="dataset not downloaded")
def test_real_swe_commands_are_mostly_classified() -> None:
    swe = [t for t in load_trajectories(REAL_BANK) if t.benchmark == "swebench"]
    kinds = Counter(
        a.kind
        for t in swe
        for turn in turns_from_messages(t.steps[-1].messages)
        for a in turn.actions
    )

    assert kinds["other"] / sum(kinds.values()) < 0.05
    assert kinds["edit"] > 0 and kinds["run"] > 0

    for t in swe:
        counts = [step_signals(s).actions for s in t.steps]
        assert counts == sorted(counts)
