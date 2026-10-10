# Architecture

Deliberately small: no LLM in the loop, and only one lever.

```
harness events ──► Signal extractor ──► Lock detector ──► Floor policy ──► Subagent tier (PreToolUse: Agent)
 (hooks /            (pure functions)    (state machine)    (code)                 │
  transcripts /                                │                                    ▼
  bench prefixes)                              └──────► scope.* JSONL ◄──── Outcome logger
```

The same `packages/core` runs offline over TwinRouterBench prefixes and local
transcripts (replay), and live inside the Claude Code plugin.

## 1. Signal extractor (pure functions over an event stream)
A session is a list of `Turn`s, one per model call. Each turn holds `Action`s
of kind `read | search | edit | test | run | other`, with touched paths and
success when known (`shiftpoint_core.events`). Agents that work through a
single shell tool are mapped to actions by a regex-level command classifier
(`shiftpoint_core.bash`). On TwinRouterBench SWE it leaves only 6 of 389
commands as `other`, all of them `pip install`.

`shiftpoint_core.signals.extract(turns)` computes:

| Signal | Meaning |
|---|---|
| exploration_decay | 1 − (recent new-file rate ÷ peak new-file rate); 0 = still discovering |
| rw_flip | edits outnumber reads + searches over the last 2 turns |
| has_edit, turns_since_first_edit | whether and how long ago editing started |
| first_verify | a test or run happened after the first edit |
| touch_set_size, touch_set_stable | distinct edited paths; no new edited path in the last turn |
| out_of_set_touch | new edited paths introduced after the first verify |
| failure_streak | consecutive failed actions at the end |
| counts | turns, actions, reads, searches, edits, tests, runs, files_seen |

Harness-only signals (not observable in recorded benchmarks, added by the
plugin): `plan_committed` (plan mode exited or a stable todo list) and
`user_go` (user confirms after a plan).

## 2. Lock detector (state machine with hysteresis)
`EXPLORING → LOCKED → (DRIFTING → EXPLORING)`, `LOCKED → DONE`.
- EXPLORING→LOCKED when the weighted signal score is ≥ θ for k consecutive turns.
- LOCKED→DRIFTING on out_of_set_touch, failure_streak ≥ m, or a new user goal.
- A minimum dwell time between transitions prevents flapping.
- θ and the weights are hand-set. A logistic fit is allowed only on a
  held-out split.

## 3. Floor policy (deterministic)
- Between LOCKED and DONE, subagents doing edit or test-fix work get
  `tier ≥ floor` (default `high`).
- Before lock, or for read-only subagents (search/explore), the requested
  model is left alone. shiftpoint only *raises* tiers, unless a downgrade
  rule is backed by replay or shadow-mode evidence (D7).
- Low confidence means no change.
- Modes: `shadow` (default; log only) → `act`.
- The main conversation's model is never changed (D11).

## 4. Outcome logger
For each decision: signals, state, the subagent's requested vs recommended
tier, the tier applied, token cost, and outcome (subagent success, tests,
reverts, rework turns). Stored as local JSONL with hashed paths and no content
(D6). These logs are the `scope.*` format (D12).

## Tier vocabulary
TwinRouterBench tiers `low | mid | mid_high | high` (D14). The plugin maps
them to concrete models through user config, so model names never appear in
the core.

## Repo layout
```
packages/core/          signals/, detector/, policy/, log/ (pyright strict)
replay/                 offline evaluation: bench loader, labels, baselines
adapters/claude-code/   shiftpoint-floor plugin
spec/                   scope.* event format
docs/
```
