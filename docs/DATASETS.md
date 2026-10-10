# Datasets

## TwinRouterBench static question bank
- Source: [Amorph/TwinRouterBench](https://huggingface.co/datasets/Amorph/TwinRouterBench),
  `question_bank.jsonl`. Apache-2.0. Paper: [arXiv:2605.18859](https://arxiv.org/abs/2605.18859).
- Pinned revision `c2907f006455d9d3b4bf69472a527536c7baa195`.
  SHA-256 `7e2870b5e2e5c801f6444c05a4311c9c9010e965016f6938f0bb5abc226252d0`.
- Fetch: `uv run python -m shiftpoint_replay.download` (writes `data/twinrouterbench/`, gitignored).
- Load: `shiftpoint_replay.twinrouterbench.load_trajectories(path)`.

### Record schema (one line = one model call, "step")
| field | type | notes |
|---|---|---|
| `id` | str | unique per record |
| `benchmark` | str | `swebench`, `pinchbench`, `bfcl`, `mtrag`, `qmsum` |
| `scenario` | str | e.g. `code_swe`, `general_agent` |
| `instance_id` | str | trajectory id within a benchmark |
| `step_index` | int | 1-based; complete `1..total_steps` for every multi-step trajectory |
| `total_steps` | int | |
| `messages` | list | router-visible prefix (OpenAI chat format) |
| `target_tier` / `target_tier_id` | str / int | `low=0, mid=1, mid_high=2, high=3` |
| `functions` | list | BFCL only |
| `benchmark_display`, `benchmark_subset`, `benchmark_version`, `pipeline_stage`, `collector`, `collected_at`, `notes` | metadata | |

Message fields: `role` (`system|user|assistant|tool`) and `content` (a string,
null, or a list of `{"type": "text", "text": ...}` parts, with
`cache_control` on PinchBench). Assistant messages have `tool_calls` as
`[{id, type, function: {name, arguments: <JSON string>}}]` and may also carry
`index` and `function_call: null`. Tool messages have `tool_call_id`.

### Quirks
- **SWE-bench** (40 trajectories, 336 steps, 4–13 steps each)
  - Collected with Codex.
  - The only tool is `bash`, so reads, edits and tests all appear as shell
    commands (`sed -n`, `sed -i`, Python heredocs, `pytest`).
  - Step k's messages are an exact prefix of step k+1's.
  - The dataset notes describe these labels as "weak-label routing
    supervision data rather than strict ground truth" (`degradation_search_done`).
- **PinchBench** (12 trajectories, 48 steps)
  - Tools: `read`, `exec`, `write`, `edit`.
  - Prefixes are **not** monotonic across steps.
  - Only 1 step is labelled `high`.
- `bfcl`, `mtrag`, `qmsum` are single-turn or RAG records, not agent trajectories.

### SWE label distribution
| | value |
|---|---|
| tiers | high 168, low 94, mid_high 41, mid 33 |
| step-1 tier | low 25, mid_high 7, mid 5, high 3 |
| first `high` step | step 1: 3, step 2: 22, step 3: 10, step 4: 3, step 9: 1, never: 1 |
| high share by trajectory third | 60/127, 77/110, 31/99 |
| steps with a `high` within the next k steps | k=0: 50%, k=1: 69%, k=3: 78%, k=5: 78% |
