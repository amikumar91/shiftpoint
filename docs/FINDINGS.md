# Findings

Results that confirm or contradict project hypotheses, negative ones included.

## F0. Pre-experiment desk findings (2026-10-10)

**F0.1 `PreModelSwitch` cannot rewrite the target model.** (Contradicts the
assumption that direct swap was a usable lever.)
It exists, but it only allows, denies, asks, or blocks.
https://code.claude.com/docs/en/hooks.md → D11.

**F0.2 Mid-session swaps rarely pay back.** (Contradicts "swap when savings >
re-cache cost" as a meaningful path.)
Payback takes 8–291 requests. For 51–80% of sessions over $100, staying on the
top model was cheaper. https://arxiv.org/html/2609.28919v1 → D11.

**F0.3 The original offline-evaluation label was likely degenerate.**
TwinRouterBench under-prediction peaks in the middle third of trajectories
(73%), on edit and test steps that come *after* a typical lock point. So the
"peak tier of remaining steps" is `high` at both turn 1 and lock, and
comparing baseline A with detector B would not discriminate.
https://arxiv.org/html/2605.18859 → D10.

**F0.4 Subagent tier is a viable, cache-free lever.** (Supports the idea.)
Subagents don't touch the parent's cache, and the Agent tool accepts `model`.
Hook rewrite of that field is still unverified.
