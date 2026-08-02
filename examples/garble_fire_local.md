# Garbleworks closed loop against blockjail + stegoff

## Gap this closes

Garbleworks `optimize` / `bandit_self_improve` need a **fire + score** target.
Regex gates are not HTTP models. The fit is **local_fn**:

1. Compose / evolve seeds (Garbleworks or `closed_loop.py`)
2. `fire_local` → `blockjail.gate_target:gate_probe`
3. Adjudicate: `attr_true:ok` ⇒ **dual bypass** (attacker win)
4. `log_attempt` updates bandit posteriors

## Setup

```powershell
$env:GARBLEWORKS_LOCAL_FN_ALLOW = "blockjail."
# optional: root for import
$root = "C:\Code\blockjail\src"
```

Callable:

| Spec | Meaning |
|---|---|
| `blockjail.gate_target:gate_probe` | Dual gate (blockjail + stegoff) |
| `blockjail.gate_target:gate_probe_blockjail_only` | blockjail only |

Success mode for attacker: `attr_true:ok`  
(`ok=True` when payload is **allowed** through the gate.)

## Local closed loop (no MCP)

```powershell
cd C:\Code\blockjail
py -3.12 examples\closed_loop.py --budget 40 --rounds 3
```

Writes `examples/bypass_results/closed-loop-latest.{json,md}`.

## Garbleworks MCP fire (one shot)

```
fire_local(
  payload="<attack text>",
  callable_spec="blockjail.gate_target:gate_probe",
  root="C:/Code/blockjail/src",
  success="attr_true:ok",
  technique="past_tense",
  op="closed_loop",
  log=true,
)
```

## Full MCP loop recipe

1. `start_run(objective=..., kind="injection", target="local:blockjail+stegoff")`
2. `evolve_seeds(objective=..., reps=3, expanded=true)` → basket
3. For each seed: `fire_local(..., run_id=..., technique=strategy)`
4. `sample_next_move(target_type="local_fn")` → pick next arm
5. Mutate winners with encode wraps; re-fire
6. `attempt_stats(group_by="technique")` → leaderboard
7. Patch blockjail/stegoff for any high-signal dual bypasses; re-run

`optimize` with HTTP judge is **not** required for gate hunting. Local_fn +
`attr_true:ok` is the correct fitness for this target class.
