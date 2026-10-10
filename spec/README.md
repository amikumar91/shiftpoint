# scope.* event format, v0 (draft)

This format is the plugin's own log schema, written down (D12). It becomes a
proposed standard only after one external router consumes it.

Events are JSONL records. When exported to OTel they become span events
alongside `gen_ai.*`; we never set `gen_ai.*` attributes ourselves (D5).

## Event types
| event | when |
|---|---|
| scope.exploring | session start, or after unlock |
| scope.locked | detector enters LOCKED |
| scope.drift | a drift signal fired |
| scope.unlocked | returned to EXPLORING |
| scope.done | task finished |
| route.recommended | the floor policy evaluated a subagent launch (any mode) |
| route.applied | the adapter actually changed a subagent's tier |
| outcome.recorded | subagent or task outcome observed |

## Common fields
```json
{
  "spec_version": "0.1",
  "event": "scope.locked",
  "session_id": "string",
  "turn": 14,
  "ts": "RFC3339",
  "harness": "claude-code",
  "state": "LOCKED",
  "signals": {"plan_committed": true, "exploration_decay": 0.82, "rw_flip": true},
  "confidence": 0.87
}
```

## scope.locked extra fields
```json
{"touch_set": {"paths_hashed": ["..."], "modules": 3},
 "critical_phases_ahead": ["edit", "test_fix"]}
```

## route.recommended
```json
{"subagent_kind": "edit|test_fix|explore|other",
 "requested_tier": "mid", "recommended_tier": "high",
 "floor_applied": true, "mode": "shadow"}
```

Tiers: `low | mid | mid_high | high` (D14).

Open questions:
- Do we need a richer scope card (task_type, reversibility, novelty)? It is
  deferred until consumers ask for it.
- Upstream path: an integration PR first, OTel GenAI SIG later.
