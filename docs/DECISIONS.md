# Decisions (ADR-lite)

D1: Apache-2.0. Maximizes adoption by routers and vendors.
D2: Python core first (offline evaluation is data-heavy, iteration is fast). Port later if needed.
D3: Shadow mode is the default. Trust before automation.
D4: ~~The scorer is pluggable; no hard dependency on Jev or any hosted model.~~
    Superseded by D9: no scorer plugin system. The detector is hand-tuned or
    logistic, with no hosted-model dependency.
D5: Own `scope.*` namespace; align with `gen_ai.*`, don't extend it.
D6: Privacy by default: hashed paths, no content capture unless opted in.
D7: Never downgrade on low confidence; critical phases get a tier floor.
    The plugin only raises tiers until evidence supports a downgrade rule.
D8: Metric of record is cost per accepted task, not cost per call.

## 2026-10-10: refocus for open-source impact
D9: Scope narrowed. shiftpoint is a signal and evidence project, not a router.
    Out of scope: main-conversation swaps, scorer backends, ScopeBench,
    gateway adapters. Reason: routing is commoditizing (Not Diamond, SAAR,
    Switchyard, Accenture), and platform risk is high. See RESEARCH.md.
D10: Offline-evaluation hypothesis reframed from "remaining-peak tier" to "a high-tier
    step within the next k steps". Reason: SWE high steps sit mid-trajectory,
    after the lock point. Remaining-peak would be `high` both at turn 1 and at
    lock, so the comparison couldn't discriminate. always-high and
    position-only become required baselines, and every metric includes cost.
D11: The only lever is the subagent tier at launch (PreToolUse on Agent).
    We never change the main conversation's model. Reason: cache recompute
    rarely pays back (8–291 requests), and PreModelSwitch can only
    allow/deny, not rewrite.
D12: The spec follows the implementation. v0 is the plugin's log schema.
    Standardization only after one external integration.
D13: Every phase publishes something: a write-up, a dataset, a plugin, or a PR.
    Negative results get published with equal effort.
D14: Tier vocabulary is TwinRouterBench's `low | mid | mid_high | high`.
    Mapping to concrete models is user config.
