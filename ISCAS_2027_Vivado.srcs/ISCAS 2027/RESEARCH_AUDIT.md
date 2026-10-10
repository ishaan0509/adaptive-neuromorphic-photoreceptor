# Research audit

## Scope and evidence classes

This audit describes the current files in `sources_1/new/`, `sim_1/new/`, and `ISCAS 2027/`. It distinguishes source inspection, Python execution, and user-reported Vivado output. No HDL tool was run for this update.

## Current engineering model

- Default RTL data is signed 40-bit Q16.24. The Python cycle reference in `baseline_fixed_point.py` models wrapped assignments and arithmetic shifts.
- The full-update design is `photoreceptor_baseline.v`; the selectable wrapper is `photoreceptor_top.v` (`ADAPTIVE_ENABLE=0` selects baseline, nonzero selects adaptive).
- The baseline updates voltage, five gates, and three calcium states on valid samples. The adaptive design preserves those state updates but caches the six ionic current terms. Photocurrent remains live.
- Adaptive refresh is group-wide, triggered by initialization, light difference, voltage excursion, proxy budget exhaustion, or maximum interval. Reset clears cache-valid state; invalid cycles hold state/counters/cache.
- The six adaptive current modules remain combinational, but input operand-isolation muxes now select last-refresh snapshots between refreshes by default. RTL refresh/recomputation counters are not switching or power measurements.
- `calcium_dynamics.v` has an `i_ca_pA_q` input that is not used. Its omission is a known provisional approximation, not paper-derived behavior.
- The Appendix B implementation is separate. Its optical input `J_hv(t)`, B.2/B.9 calcium relationship, and `E_Ca` logarithm base remain unresolved, so neither implementation is biologically validated.

## Latest user-reported implementation measurements

The user supplied screenshots for top-level baseline (`ADAPTIVE_ENABLE=0`) and adaptive (`ADAPTIVE_ENABLE=1`). Reported values are recorded in [IMPLEMENTATION_RESULTS.md](./IMPLEMENTATION_RESULTS.md). The power estimate confidence is marked low. Adaptive's reported LUT count exceeds the 20,800-LUT capacity; its reported dynamic and total power estimates are higher than baseline. These are evidence from the supplied screenshots, not independently inspected report files.

An earlier baseline count of 27,673 LUTs conflicts with the latest screenshot's 16,348. They are separate runs and must not be compared as if settings were identical.

## Python adaptive experiment

`discrete_time_model.py` computes an ionic-current function only when that current is selected for refresh, so its counts represent actual Python function calls avoided. This does not model RTL switching. The 2026-10-10 run of `run_adaptive_experiments.py` covered nine existing stimuli and four policies; the generated 36-row output is `results/metrics/area_followup_python/adaptive_experiments.csv`.

The periodic policy failed a 1 V numerical runaway guard for 7/9 stimuli. The threshold and empirical-budget policies completed those stimuli, but no error tolerance was specified before evaluation and no tolerance-exceedance rate was computed. The empirical budget's proxy remained near its 10 μV configured threshold while observed trajectory error reached 51.58 μV. This counterexample rules out describing that proxy as a bound.

## Empirical-budget sensitivity sweep

The Python-only sweep in `run_budget_sweep.py` completed 54 combinations: nine fixed stimuli × three trigger values (1, 10, 100 μV) × two maximum cache ages (4, 16 samples), at 1 s and 0.1 ms resolution. All cases remained within the model's numerical guard. Full results and run configuration are in `results/metrics/area_followup_python/empirical_budget_sweep.csv` and `budget_sweep_metadata.json`.

Comparisons use 10,000 post-initial state samples per stimulus. Baseline current-function evaluation denominator is six terms × 10,001 grid points = 60,006 per stimulus, or 540,054 across nine stimuli. Across the sweep, the 1 μV trigger configuration's maximum observed voltage difference was 7.21549 μV and had no samples above the prespecified 10/50/100 μV cutoffs; weighted Python function-evaluation reduction was 48.96% (max interval 4) or 52.38% (16). At 10 μV trigger, maximum observed voltage difference was 51.50652/51.57906 μV and 5,780/5,903 of 90,000 samples exceeded 10 μV; reductions were 61.68%/65.72%. At 100 μV trigger, the maximum observed discrepancy was 301.89304/308.30578 μV, with 34,386/40,283 samples exceeding 10 μV, and reductions were 73.99%/79.15%, for max intervals 4/16 respectively.

The trigger is an empirical scheduler input, not a hard trajectory-error tolerance or proven upper bound. The counts are Python model function executions, not RTL switching activity or measured energy. The sweep uses one fixed stimulus amplitude/timing set and does not model RTL reset/invalid cycles. It is evidence for a sensitivity trade-off on a provisional model only, not biological validation or hardware power savings.

## Deterministic held-out scheduler comparison (2026-10-10)

The fixed observed-error target was 10 μV. Two policies were tuned only on the original nine training stimuli; six deterministic held-out cases were not used to choose thresholds. Identical default state, sample times, model parameters, and input trace were provided to each full-update reference and adaptive candidate.

| Selected policy and training parameters | Training worst max error | Training pooled RMS / MAE | Training function-call reduction | Held-out worst max error (stimulus) | Held-out pooled RMS / MAE | Held-out function-call reduction | Held-out samples over 10/50/100 μV |
|---|---:|---:|---:|---:|---:|---:|---:|
| Per-current sensitivity (`1e-14 A`, max 16) | 1.39259 μV | 0.16298 / 0.07661 μV | 57.73% | 1.48659 μV (triangle ramp) | 0.21603 / 0.08455 μV | 38.08% | 0 / 0 / 0 |
| Accumulated voltage proxy (`1e-6 V`, max 16) | 7.21549 μV | 0.34871 / 0.09583 μV | 52.38% | 6.97410 μV (chirped light) | 0.31175 / 0.04978 μV | 33.00% | 0 / 0 / 0 |

The 10 μV target is a finite empirical selection criterion, not an error bound. On these samples, sensitivity had lower maximum/RMS error and higher function-call reduction; the proxy had lower MAE. No unseen-stimulus guarantee follows.

The counted Python operations are genuinely skipped: `simulate_discrete` calls `_current_and_gradient` only inside `if refresh[name]`, and the exported evaluation count equals `refresh_mask.sum()`. This software control flow is not equivalent to RTL switching. The new RTL adds operand isolation around the prior global-refresh scheduler; it does not implement the Python per-current sensitivity policy. Consequently, these Python accuracy results do not validate current RTL behavior.

Outputs: `results/metrics/heldout_scheduler/heldout_scheduler_results.csv`, `heldout_scheduler_metadata.json`, and `heldout_scheduler_tradeoff.png`.

## Latest Python validation and remaining audit gaps

- The full Python suite passed 52 tests after the held-out tests and RTL static-structure checks were added.
- The budget sweep was rerun and validated as 54 rows (nine stimuli × three triggers × two max intervals), all with `OK` status and finite metrics. Each row accounts for exactly 10,000 post-initial samples; aggregate sample-threshold counts use that same denominator.
- The held-out results contain 180 training rows (20 configurations × nine stimuli) and 12 held-out rows (two selected policies × six stimuli). Both selected policies met the training target; held-out output has no failures and finite numeric metrics.
- Five new 40-cycle baseline Q16.24 vectors were generated for alternating, held-out step, double pulse, ramp, and rapid pulse stimuli. The baseline trace bench now includes these five alongside the three existing vectors; it has not been run.
- Static source inspection confirms each of the six current instances consumes muxed operands. In default isolation mode, operands are live only on refresh and otherwise come from reset-initialized registers updated on valid refreshes. No RTL switching or power measurement is available.
- The scheduler age counter now saturates and clamps intervals above 65,536 accepted samples; the recomputation counter saturates. These are static changes only and remain subject to user HDL compilation/simulation.
- The follow-up experiment runner completed and preserved the pre-existing `adaptive_experiments.csv` by writing into `results/metrics/area_followup_python/`.
- No current Vivado simulation result for the edited arithmetic RTL was supplied in this turn.
- The latest utilization and power source reports, part number, implementation constraints, SAIF/VCD/activity assumptions, timing report, and run logs are unavailable.
- Existing experiments do not sweep a systematic grid of input amplitudes or model Python reset/invalid RTL semantics as an input stream. Held-out waveforms vary step/pulse timing and input shapes; the sensitivity trigger grid selected one configuration on training stimuli only. This remains a limited finite test.
- Literature review here is an initial, non-systematic comparison; it cannot establish novelty.

## Scientific conclusion

Evidence supports only a limited Python comparison of selective-current policies on the provisional model, plus static inspection of new operand isolation. It does not validate the changed RTL, prove an error bound, demonstrate FPGA activity/power benefit, establish feasibility, biological fidelity, or research novelty. Historical user-reported power/resource values predate operand isolation and must not be attributed to the modified sources.
