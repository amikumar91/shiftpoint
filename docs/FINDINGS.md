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

## F1. TwinRouterBench data audit (2026-10-10)
Measured on the pinned question bank; details in [DATASETS.md](DATASETS.md).

**F1.1 The D10 label ("a `high` step within the next k steps") is also
degenerate.** (Contradicts D10.)
It is positive for 69% of SWE steps at k=1 and 78% at k=3–5. "Always
predict high" catches every high step at 78% accuracy, which leaves little
for a lock detector to improve on.

**F1.2 High-tier work starts before any plausible lock point.**
The first `high` step is step 2 or 3 in 32 of 40 trajectories, and step 1 is
usually `low` (25/40). The scope-lock idea assumed a long exploration phase
before critical work. That phase barely exists in these traces.

**F1.3 Trajectories are short and tool-poor.**
Trajectories have 4–13 model calls, and the only tool is `bash`, so every
signal has to be inferred from shell command text. PinchBench has only one
`high` step, so it can't support a high-tier analysis.

**F1.4 SWE labels are weak labels.**
The dataset notes call them "weak-label routing supervision data rather
than strict ground truth", so per-step results carry label noise on top of
the small sample.

**What still discriminates:** the current-step tier (50% high, so not
degenerate), and the tail of each trajectory. 22% of steps have no `high`
step left, and the high share falls to 31/99 in the final third. These point
to two better-posed questions: (a) do scope signals improve per-step tier
prediction over position alone, and (b) can they identify when the critical
phase is *over*? D10 needs revisiting before baselines run.
