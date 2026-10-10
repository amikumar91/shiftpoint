"""Classify shell commands into actions using cheap, regex-level rules.

Agents often do everything through one shell tool, so reads, edits and test
runs have to be recovered from command text. The rules favour precision on
edits and test runs; anything unrecognised is ``other``.
"""

from __future__ import annotations

import re

from shiftpoint_core.events import Action, ActionKind

# Strongest kind wins when a command chains several sub-commands.
_PRIORITY: dict[ActionKind, int] = {
    "edit": 5,
    "test": 4,
    "run": 3,
    "read": 2,
    "search": 1,
    "other": 0,
}

_EXT = (
    r"(?:py|pyi|pyx|c|h|cc|cpp|rs|go|java|js|jsx|ts|tsx"
    r"|rst|md|txt|cfg|ini|toml|json|ya?ml|html|css)"
)
_PATH = re.compile(rf"(?<![\w/.-])(?:\.{{0,2}}/)?(?:[\w.-]+/)*[\w-][\w.-]*\.{_EXT}\b")
# Files that record the agent's own output rather than project changes.
_SCRATCH = re.compile(r"(?:^|/)(?:patch\.txt|[\w.-]+\.(?:patch|diff))$")

_HEREDOC_PY = re.compile(r"^\s*(?:\w+=\S+\s+)*python[\d.]*\s+-\s*<<", re.MULTILINE)
_PY_WRITE = re.compile(
    r"\.write_text\(|\.write_bytes\(|open\([^)]*,\s*['\"](?:w|a|r\+)[^'\"]*['\"]|\.write\("
)
_PY_TARGET = re.compile(r"(?:Path|open)\(\s*['\"]([^'\"]+)['\"]")

_SED_INPLACE = re.compile(r"\bsed\s+(?:-\w*i\w*|--in-place)\b")
_PATCH = re.compile(r"\bapply_patch\b|\bgit\s+apply\b|\bpatch\s+-p\d")
_REDIRECT = re.compile(r"(?<![0-9&<])>>?\s*([^\s|&;<>]+)")
_TEST = re.compile(
    r"\bpytest\b|-m\s+(?:pytest|unittest)\b|\btox\b|\bnox\b|runtests\.py|manage\.py\s+test\b"
    r"|\bmake\s+(?:test|check)\b|\bcargo\s+test\b|\bgo\s+test\b|\bnpm\s+(?:run\s+)?test\b"
)
_RUN_HEAD = re.compile(r"^(?:\w+=\S+\s+)*(?:python[\d.]*|node|ruby|perl|bash|sh)\b")
_SEARCH_HEAD = re.compile(r"^(?:grep|egrep|rg|ag|find|ls|tree|fd|locate)\b")
_READ_HEAD = re.compile(
    r"^(?:cat|head|tail|less|more|nl|wc|awk|sed|bat|git\s+(?:diff|show|log|status|blame|grep))\b"
)
_CD_PREFIX = re.compile(r"^\s*cd\s+\S+\s*(?:&&|;)\s*")
_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\n)\s*")
_HEREDOC_OPEN = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc bodies (data, not commands), keeping the opening lines."""
    kept: list[str] = []
    terminator: str | None = None
    for line in command.split("\n"):
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            continue
        kept.append(line)
        match = _HEREDOC_OPEN.search(line)
        if match:
            terminator = match.group(1)
    return "\n".join(kept)


def _normalize(path: str, root: str | None) -> str:
    if root and path.startswith(root.rstrip("/") + "/"):
        path = path[len(root.rstrip("/")) + 1 :]
    while path.startswith("./"):
        path = path[2:]
    return path


def _paths(text: str, root: str | None) -> frozenset[str]:
    found = (_normalize(m.group(0), root) for m in _PATH.finditer(text))
    return frozenset(p for p in found if not _SCRATCH.search(p))


def _redirect_targets(segment: str, root: str | None) -> frozenset[str]:
    targets = (_normalize(t, root) for t in _REDIRECT.findall(segment))
    return frozenset(t for t in targets if t != "/dev/null" and not _SCRATCH.search(t))


def _segment_kind(segment: str) -> ActionKind:
    head = segment.split("|", 1)[0].strip()
    if _SED_INPLACE.search(segment) or _PATCH.search(segment):
        return "edit"
    if _TEST.search(segment):
        return "test"
    if _RUN_HEAD.match(head):
        return "run"
    if _SEARCH_HEAD.match(head):
        return "search"
    if _READ_HEAD.match(head):
        return "read"
    return "other"


def classify_command(command: str, root: str | None = None) -> Action:
    """Classify one shell command. ``root`` is stripped from absolute paths."""
    command = _CD_PREFIX.sub("", command.strip())

    if _HEREDOC_PY.search(command):
        if _PY_WRITE.search(command):
            targets = frozenset(
                _normalize(t, root) for t in _PY_TARGET.findall(command) if not _SCRATCH.search(t)
            )
            return Action("edit", targets or _paths(command, root))
        return Action("test" if _TEST.search(command) else "run", _paths(command, root))
    command = _strip_heredoc_bodies(command)

    best: ActionKind = "other"
    edited: set[str] = set()
    for segment in filter(None, _SPLIT.split(command)):
        kind = _segment_kind(segment)
        targets = _redirect_targets(segment, root)
        if targets and kind in ("other", "read", "run"):
            # e.g. `cat <<EOF > repro.py` or `echo x >> setup.cfg`
            kind = "edit"
            edited |= targets
        if _PRIORITY[kind] > _PRIORITY[best]:
            best = kind
    paths = frozenset(edited) if best == "edit" and edited else _paths(command, root)
    return Action(best, paths)
