import shiftpoint_core


def test_version_is_exposed() -> None:
    assert shiftpoint_core.__version__ == "0.0.0"
