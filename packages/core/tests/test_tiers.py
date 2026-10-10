import pytest
from shiftpoint_core.tiers import Tier


def test_tiers_are_ordered() -> None:
    assert Tier.LOW < Tier.MID < Tier.MID_HIGH < Tier.HIGH


@pytest.mark.parametrize("tier", list(Tier))
def test_label_round_trips(tier: Tier) -> None:
    assert Tier.from_label(tier.label) is tier


def test_unknown_label_raises() -> None:
    with pytest.raises(ValueError, match="unknown tier"):
        Tier.from_label("ultra")
