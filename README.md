# shiftpoint

> Routers decide *which* model. shiftpoint tells them *when* the task got hard.

## The problem
Agent sessions start with little context. The real shape of the task only
becomes clear after exploration and planning: which files, how risky, whether
it needs design judgment. Routers that score the first prompt guess too early,
and frontier models acting as routers under-route the steps that matter most.
On TwinRouterBench, Opus 4.6 as router picked the high tier for 7 of 147
verified-high SWE-bench steps and failed all 40 trajectories. The most
under-routed steps were mid-trajectory edits and test runs
([paper](https://arxiv.org/html/2605.18859)).

## The idea
Detect the **scope-lock moment** from cheap harness signals (plan committed,
exploration decaying, reads flipping to writes, first test run). At that point
the critical phase is usually still ahead. shiftpoint:

1. emits an open `scope.locked` event any router can consume, and
2. in Claude Code, sets a **tier floor on subagents launched after lock**, so
   critical work isn't handed to an under-powered model.

shiftpoint never changes the main conversation's model. Mid-session swaps
rebuild the prompt cache and rarely pay back
([Claude Code docs](https://code.claude.com/docs/en/prompt-caching.md),
[Abbasi et al. 2026](https://arxiv.org/html/2609.28919v1)). Subagents start
fresh conversations, so choosing their tier costs no cache.

## What this project is (and isn't)
- **Is:** an evidence-first open-source project. It runs a public experiment,
  ships a small Claude Code plugin, and offers an open signal format.
- **Isn't:** a router, a scorer marketplace, or a multi-harness gateway.
  Vendors are building those; we aim to be a signal they consume.

## Status
Early. The repo currently contains the core package skeleton and the design
docs. The `scope.*` event format is a v0 draft. Results, positive or
negative, are recorded in [docs/FINDINGS.md](docs/FINDINGS.md).

## Docs
- [docs/RESEARCH.md](docs/RESEARCH.md): evidence and prior art
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components and data flow
- [spec/README.md](spec/README.md): `scope.*` event format
- [docs/DATASETS.md](docs/DATASETS.md): dataset schemas and pins
- [docs/DECISIONS.md](docs/DECISIONS.md): design decisions
- [docs/FINDINGS.md](docs/FINDINGS.md): results

## Development
Requires [uv](https://docs.astral.sh/uv/).
```
uv sync
uv run python -m shiftpoint_replay.download   # TwinRouterBench, pinned + checksummed
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run pytest
```

## License
Apache-2.0
