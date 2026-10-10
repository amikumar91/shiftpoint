# Research summary (updated Oct 2026)

## Problem evidence
- Manifest deprecated its LLM router after 4 months. Prompt complexity was a
  poor signal because difficulty emerged during tool use, caching saved more
  than routing, and switching models hurt consistency. In the HN thread, one
  commenter said pinning models to subagent roles worked, because the
  orchestrator chooses with full task context.
  https://zeli.app/en/story/49126630
- TwinRouterBench ([paper](https://arxiv.org/html/2605.18859),
  [repo](https://github.com/CommonstackAI/TwinRouterBench),
  [data](https://huggingface.co/datasets/Amorph/TwinRouterBench), Apache-2.0):
  - Tiers: `low, mid, mid_high, high` (ids 0–3). Labels are execution-verified
    with a downgrade-and-cascade protocol.
  - Static track: 970 labelled prefixes across 520 instances. Multi-step
    workloads are SWE-bench (40 instances, 336 steps, median 9 steps/trace)
    and PinchBench (12 instances, 48 steps). Prefixes include full message
    history and tool outputs.
  - Opus 4.6 as router: 7/147 (4.8%) verified-high SWE steps predicted high;
    0/40 trajectories passed.
  - Under-prediction by position: 46% in the first third, 73% in the middle
    third, 53% in the last third. Core editing and test-running steps are the
    most under-predicted.
  - A trained router resolved 75/100 held-out cases for $25.66, versus 74/100
    for $54.73 with all-Opus (−53%).
- Routing collapse: as budget rises, routers drift to the most expensive
  model. https://arxiv.org/abs/2602.03478

## Switch economics
- Each model has its own prompt cache. A mid-session switch recomputes the
  full request. Subagents don't touch the parent's cache. Compaction rebuilds
  the conversation layer anyway.
  https://code.claude.com/docs/en/prompt-caching.md
- Abbasi, Aqrawi, Kwartler (Accenture, Sept 2026) emulated a 10k-seat
  enterprise:
  - A mid-task switch pays back only after 8–291 requests.
  - In 51–80% of real sessions over $100, staying on the top model was cheaper.
  - Savings were 14% with today's classifier labels and 21% with perfect labels.
  - 12.5% of moved turns were false downgrades.
  - Their router never changes a running conversation's model. It re-chooses
    at session start, new tasks, and subagent launch.

  https://arxiv.org/html/2609.28919v1

## Prior art
| Project | Does | Gap we target |
|---|---|---|
| Accenture cache-safe router (paper) | Jev labels; routes at session start, side lanes, subagent launch; "new task = re-choose" | no scope-lock detector; emulation only |
| Not Diamond Code | per-step routing that weighs KV-cache state and predicted cost/reward | closed; no open signal |
| vLLM Semantic Router SAAR | session memory, tool-loop hard locks, cache-aware switch pricing, `decision_drift_reset` | serving layer; phase is internal |
| NeMo Switchyard | stage/escalation/sticky routers from conversation signals | per-turn; no explicit lock event |
| OpenRouter Auto | sticky multi-turn routing | request level only |
| CodeRouter | per-request phase classes (plan/impl/test/docs) | vendor claims, unverified |
| Superpowers subagent-driven-dev | per-task tier heuristics | tier fixed at plan time |
| Claude Code `opusplan` | Opus in plan mode, Sonnet in execution | coarse; each toggle busts the cache |

Links: https://bito.ai/blog/best-ai-model-routers-for-coding-agents-in-2026/ ·
https://vllm.ai/blog/2026-06-02-session-aware-agentic-routing ·
https://docs.nvidia.com/nemo/switchyard/routing/overview.md ·
https://openrouter.ai/blog/announcements/introducing-the-new-auto-router/ ·
https://www.coderouter.io/blog/agent-router-alternative-guide-2026

**Takeaway:** The open gap is a harness-level, open signal for *when* the task
shape is known, plus evidence that it predicts critical phases. The routing
decision itself is commoditizing.

## Decision-model notes (Jev)
REFLEX: 72.7% fewer strong-model calls at 95% success; little advantage over
a cheap LLM cascade when routing is already easy.
https://arxiv.org/abs/2609.26532. Not a dependency (see D4).

## Claude Code facts (verified Oct 2026)
- `PreModelSwitch` exists. Input is `from_model`/`to_model`. It can allow,
  deny, ask, or block, but **cannot rewrite the target model.**
  https://code.claude.com/docs/en/hooks.md
- PreToolUse `updatedInput` replaces a tool's arguments before it runs.
  The Agent tool accepts `model` (sonnet/opus/haiku/fable). Whether a hook
  rewrite of `model` is honoured is still unverified.
- Transcripts live at `~/.claude/projects/**/*.jsonl` and are written
  asynchronously, so they can lag the current turn.
