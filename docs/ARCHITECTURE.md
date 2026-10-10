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
| Signal | Meaning |
|---|---|
| plan_committed | plan mode exited, or a todo/plan written and stable for N turns |
| exploration_decay | new files read per turn trending toward 0 |
| rw_flip | write/edit calls overtake read/search calls |
| first_verify | first test/build/lint command |
| user_go | user confirms after a plan |
| touch_set_stable | set of edited paths stops growing |
| failure_streak | consecutive failed tool calls or test runs |
| out_of_set_touch | edit outside the touch set |

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
