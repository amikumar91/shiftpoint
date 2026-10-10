import pytest
from shiftpoint_core.bash import classify_command

EDIT_HEREDOC = """cd /testbed && python - <<'PY'
from pathlib import Path
path = Path('django/forms/models.py')
text = path.read_text()
path.write_text(text.replace("a", "b"))
PY"""

RUN_HEREDOC = """cd /testbed && python - <<'PY'
from flask import Blueprint
print(Blueprint('a.b', __name__))
PY"""

REPRO_FILE = """cat <<EOF > reproduce_issue.py
if a > b:
    print("x")
EOF"""


@pytest.mark.parametrize(
    ("command", "kind", "paths"),
    [
        (
            "cd /testbed && sed -n '1,260p' astropy/modeling/separable.py",
            "read",
            {"astropy/modeling/separable.py"},
        ),
        ("sed -n '470,540p' /testbed/sympy/core/function.py", "read", {"sympy/core/function.py"}),
        ("cat ./django/http/response.py | head -100", "read", {"django/http/response.py"}),
        (
            'cd /testbed && grep -R "def doit" -n sympy | grep -i KroneckerDelta | head -20',
            "search",
            set(),
        ),
        ('find /testbed -type f -name "*.py" | grep -i validator', "search", set()),
        (EDIT_HEREDOC, "edit", {"django/forms/models.py"}),
        (RUN_HEREDOC, "run", set()),
        ("cd /testbed && python reproduce_issue.py", "run", {"reproduce_issue.py"}),
        (REPRO_FILE, "edit", {"reproduce_issue.py"}),
        ("sed -i 's/old/new/' src/pkg/mod.py", "edit", {"src/pkg/mod.py"}),
        ("cd /testbed && python -m pytest tests/test_mod.py -q", "test", {"tests/test_mod.py"}),
        (
            "cd /testbed && git diff -- django/utils/dateparse.py > patch.txt",
            "read",
            {"django/utils/dateparse.py"},
        ),
        (
            "mkdir -p pkg\ncat <<'PY' > pkg/__init__.py\nx = 1 > 0\nPY\nls pkg",
            "edit",
            {"pkg/__init__.py"},
        ),
        ("pip install -e .", "other", set()),
        ("ls 2>/dev/null", "search", set()),
    ],
)
def test_classify_command(command: str, kind: str, paths: set[str]) -> None:
    action = classify_command(command, root="/testbed")

    assert action.kind == kind
    assert action.paths == paths


def test_chain_takes_strongest_kind() -> None:
    command = "cd /testbed && grep -n foo a.py && python -m pytest -q"
    assert classify_command(command).kind == "test"


def test_without_root_paths_stay_absolute() -> None:
    assert classify_command("cat /testbed/a.py").paths == {"/testbed/a.py"}
