# CLAUDE.md — shiftpoint

## What this project is
shiftpoint detects the moment an agent session's scope becomes clear
("scope lock"). It publishes evidence on whether that moment predicts
critical, high-tier work. In Claude Code, it sets a tier floor on subagents
launched after lock, and emits an open `scope.*` signal that routers can
consume. Routers decide *which* model; shiftpoint says *when* the task got hard.

Goal: open-source impact and credibility, not a commercial router (D9).

## Read in this order
1. README.md: pitch and scope
2. docs/RESEARCH.md: evidence, prior art, verified platform facts (do not re-research unless asked)
3. docs/FINDINGS.md: what we've learned so far, including negatives
4. docs/ARCHITECTURE.md: components and data flow
5. spec/README.md: scope.* event format (v0 draft = plugin log schema)
6. docs/DECISIONS.md: settled decisions; don't relitigate without flagging
7. docs/ROADMAP.md: phases and checklist (local only, if present; never committed)

## Hard scope limits (D9, D11)
- Never change the main conversation's model; the only lever is subagent tier at launch.
- No scorer plugin system, no gateway adapters, no benchmark suite.
- The plugin only raises tiers unless evidence supports a downgrade (D7).
- Current focus is the offline evaluation (TwinRouterBench replay). Don't build
  the plugin until it has a go result.

## Working rules
- Python 3.12, uv workspace, ruff, pytest, pyright (strict for packages/core).
- Before finishing a change, run:
  `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest`
- Spec changes go through spec/README.md + a DECISIONS.md entry.
- Privacy: never log prompt/file content by default. Hash paths; content is opt-in.
- Downloaded datasets live in `data/` (gitignored). Never commit them.
- Every claim in docs that came from outside sources links to the source.
- Pre-register go thresholds in DECISIONS.md before running the detector.
- If a result contradicts a hypothesis, record it in docs/FINDINGS.md before
  moving on. Negative results are valuable here.

## Git rules
- Commit only final docs and code. Plans, roadmaps and scratch notes are never
  committed (ROADMAP.md and docs/plans/ are excluded via .git/info/exclude).
- Commit messages are 2–3 lines max and crisp.
- No Claude co-author or attribution lines in commits or PRs.

## Platform facts
- [x] `PreModelSwitch` exists, but it is guard-only (allow/deny/ask/block, no rewrite). See FINDINGS F0.1.
- [x] Agent tool accepts `model` (sonnet/opus/haiku/fable)
- [ ] PreToolUse `updatedInput` rewrite of Agent `model` actually takes effect (needs a live test)
- [x] Transcripts at ~/.claude/projects/**/*.jsonl (written async; may lag current turn)
- [x] TwinRouterBench is Apache-2.0; data on HF `Amorph/TwinRouterBench`
- [ ] TwinRouterBench `question_bank.jsonl` field-level schema (document when building the loader)
- [x] Name `shiftpoint` free on PyPI and as amikumar91/shiftpoint (Oct 2026); npm unchecked
