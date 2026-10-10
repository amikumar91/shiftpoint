import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from shiftpoint_core.tiers import Tier
from shiftpoint_replay.download import DEFAULT_DEST, FILENAME
from shiftpoint_replay.twinrouterbench import (
    SchemaError,
    iter_steps,
    load_trajectories,
    parse_step,
)

SYSTEM = {"role": "system", "content": "You are an agent."}
USER = {"role": "user", "content": [{"type": "text", "text": "Fix the bug."}]}
CALL = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": "c1",
            "type": "function",
            "function": {"name": "bash", "arguments": '{"command":"ls"}'},
        }
    ],
}
RESULT = {"role": "tool", "tool_call_id": "c1", "content": "README.md"}


def record(
    instance: str = "repo__1",
    step: int = 1,
    total: int = 2,
    tier: str = "high",
    tier_id: int = 3,
    benchmark: str = "swebench",
    messages: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": f"{instance}-{step}",
        "benchmark": benchmark,
        "instance_id": instance,
        "step_index": step,
        "total_steps": total,
        "target_tier": tier,
        "target_tier_id": tier_id,
        "messages": messages if messages is not None else [SYSTEM, USER],
    }


def write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def test_parse_step_normalizes_messages() -> None:
    step = parse_step(record(messages=[SYSTEM, USER, CALL, RESULT]))

    assert step.tier is Tier.HIGH
    assert [m.role for m in step.messages] == ["system", "user", "assistant", "tool"]
    assert step.messages[1].content == "Fix the bug."
    assert step.messages[2].content == ""
    assert step.messages[2].tool_calls[0].name == "bash"
    assert step.messages[2].tool_calls[0].arguments == '{"command":"ls"}'
    assert step.messages[3].tool_call_id == "c1"


def test_tier_label_and_id_must_agree() -> None:
    with pytest.raises(SchemaError, match="does not match id"):
        parse_step(record(tier="high", tier_id=1))


def test_unknown_role_rejected() -> None:
    with pytest.raises(SchemaError, match="unknown role"):
        parse_step(record(messages=[{"role": "narrator", "content": "x"}]))


def test_invalid_json_reports_line(tmp_path: Path) -> None:
    path = tmp_path / "bank.jsonl"
    path.write_text(json.dumps(record()) + "\n{not json\n", encoding="utf-8")

    with pytest.raises(SchemaError, match=r"bank\.jsonl:2"):
        list(iter_steps(path))


def test_load_trajectories_groups_sorts_and_filters(tmp_path: Path) -> None:
    path = write_jsonl(
        tmp_path / "bank.jsonl",
        [
            record("b__2", step=2, tier="low", tier_id=0),
            record("b__2", step=1),
            record("a__1", step=1, total=1, tier="mid", tier_id=1),
            record("q", step=1, total=1, benchmark="qmsum"),
        ],
    )

    trajectories = load_trajectories(path)

    assert [t.instance_id for t in trajectories] == ["a__1", "b__2"]
    assert trajectories[1].tiers == (Tier.HIGH, Tier.LOW)


def test_missing_step_rejected(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "bank.jsonl", [record(step=1, total=3), record(step=3, total=3)])

    with pytest.raises(SchemaError, match="inconsistent"):
        load_trajectories(path)


REAL_BANK = DEFAULT_DEST / FILENAME


@pytest.mark.skipif(not REAL_BANK.exists(), reason="dataset not downloaded")
def test_real_bank_matches_published_counts() -> None:
    trajectories = load_trajectories(REAL_BANK)
    swe = [t for t in trajectories if t.benchmark == "swebench"]
    pinch = [t for t in trajectories if t.benchmark == "pinchbench"]

    assert len(swe) == 40
    assert sum(len(t.steps) for t in swe) == 336
    assert len(pinch) == 12
    assert Counter(s.tier for t in swe for s in t.steps)[Tier.HIGH] == 168
