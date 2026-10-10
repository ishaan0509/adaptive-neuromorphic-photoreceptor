# Final research assessment — Python held-out study and RTL operand isolation

**Date:** 2026-10-10
**Project:** ISCAS 2027 digital neuromorphic photoreceptor

## Executive assessment

The Python experiment provides preliminary evidence that a per-current first-order sensitivity trigger can trade fewer current-function calls for low observed voltage error on the tested provisional model. At a 10 μV maximum-observed-error selection target, the selected sensitivity configuration outperformed the accumulated voltage-proxy configuration on maximum/RMS error and Python call reduction across six deterministic held-out traces. The proxy had lower pooled MAE. This is a finite result, not a formal error bound, generalization guarantee, biological result, or hardware measurement.

The adaptive RTL has been modified to isolate the inputs of all six combinational ionic-current modules between accepted refreshes. It still uses the existing **group-wide RTL refresh policy**, not the per-current sensitivity scheduler selected in Python. Therefore the held-out accuracy results do not validate the modified RTL algorithm. No Verilog simulation, compilation, synthesis, timing, implementation, activity, or power tool was run.

## Python-verified evidence

### Experiment setup

- Full-update reference and candidate start from the same default initial state and use the same provisional-model parameters, stimulus samples, and time grid for each case.
- Training: the existing nine fixed stimuli; held-out: six deterministic waveforms with changed step timings, a double pulse, triangular ramp, rapid pulse train, and chirped illumination.
- Selection target: maximum **observed** voltage difference no greater than 10 μV on every training stimulus. The held-out set did not select configuration values.
- Selected per-current sensitivity: `current_error_threshold=1e-14 A`, `max_interval=16`.
- Selected accumulated voltage proxy: `voltage_error_budget=1e-6 V`, `max_interval=16`.
- Voltage error compares post-initial states, `V[1:]`; current error compares the currents at sample `i` actually applied to the transition producing state sample `i+1`, `I[0:-1]`.
- RMS and MAE are pooled over all post-initial voltage samples for each reported split/policy. Threshold exceedance uses strict `abs(error) > tolerance`.
- Python evaluation counts are actual calls to `_current_and_gradient`, made only in the `if refresh[name]` path. The runner checks the count against its refresh mask. These counts are not an RTL activity metric.

### Selected configuration results

| Policy | Split | Max observed voltage error and worst input | Pooled RMS | Pooled MAE | Samples over 10 / 50 / 100 μV | Python current evaluations | Reduction |
|---|---|---|---:|---:|---:|---:|---:|
| Per-current sensitivity, `1e-14 A`, max 16 | Training (9 stimuli) | 1.39259 μV, abrupt transitions | 0.16298 μV | 0.07661 μV | 0 / 0 / 0 | 228,302 / 540,054 | 57.73% |
| Accumulated voltage proxy, `1e-6 V`, max 16 | Training (9 stimuli) | 7.21549 μV, periodic | 0.34871 μV | 0.09583 μV | 0 / 0 / 0 | 257,166 / 540,054 | 52.38% |
| Per-current sensitivity, `1e-14 A`, max 16 | Held-out (6 stimuli) | 1.48659 μV, triangle ramp | 0.21603 μV | 0.08455 μV | 0 / 0 / 0 | 222,934 / 360,036 | 38.08% |
| Accumulated voltage proxy, `1e-6 V`, max 16 | Held-out (6 stimuli) | 6.97410 μV, chirped light | 0.31175 μV | 0.04978 μV | 0 / 0 / 0 | 241,224 / 360,036 | 33.00% |

Both selected policies met the finite 10 μV observed-error criterion on both sampled splits. Held-out sensitivity produced lower maximum and RMS error and 5.08 percentage points more Python call reduction; accumulated proxy produced lower held-out MAE. This result is directionally supportive of further testing the sensitivity heuristic, not proof of superiority outside these traces.

### Existing 54-case sweep

The existing nine-stimulus × three-budget × two-interval sweep remains available at `results/metrics/area_followup_python/empirical_budget_sweep.csv`. It was regenerated after correcting current-error alignment to use applied currents from sample `i` for the transition to sample `i+1`. The previously documented voltage-error results and evaluation reductions are unchanged. The sweep remains evidence about Python function execution only.

## Static RTL findings and implementation changes

### Files modified

- `sources_1/new/photoreceptor_adaptive.v`
- `sources_1/new/photoreceptor_top.v`
- `sources_1/new/current_update_scheduler.v`
- `sim_1/new/tb_photoreceptor_adaptive.v`
- `sim_1/new/tb_photoreceptor_comparison.v`
- `sim_1/new/tb_photoreceptor_baseline_trace.v`

### Gating structure

`OPERAND_ISOLATION_ENABLE` defaults to 1 in the adaptive module and is exposed through the top-level wrapper. For each refresh-sensitive current input, a mux selects the live pre-edge state when `refresh_all` is asserted; otherwise it selects a reset-initialized operand snapshot. The six current calculations therefore see stable voltage/gate/calcium operands between refreshes. Snapshots and cached currents update together on `valid_in && refresh_all`. The scheduler forces refresh at the first accepted sample; invalid cycles leave state and snapshots unchanged. `OPERAND_ISOLATION_ENABLE=0` bypasses operand isolation for an adaptive comparison. `ADAPTIVE_ENABLE=0` still selects the unchanged baseline.

The photocurrent remains live, and gate/calcium/membrane state updates are unchanged. The six current modules still exist as combinational logic; input isolation is intended to limit transitions through them while operands are held. Whether this reduces mapped switching or power, and whether the added registers/muxes worsen area/timing, can only be answered by user-run Vivado reports.

The current RTL scheduler was not replaced by the Python sensitivity scheduler. It remains a group refresh with initialization, light-difference, voltage-excursion, heuristic budget, and max-age triggers. Do not ascribe the Python policy’s measured errors to RTL.

The 16-bit age counter clamps requested max intervals above 65,536 samples and saturates instead of rolling over. The 32-bit recomputation counter saturates instead of wrapping. Static source checks verify connections and reset/refresh assignments; they are not HDL compilation.

### Python reference vectors and testbenches

Five additional 40-cycle, signed Q16.24 baseline traces were generated for alternating, held-out step, held-out double-pulse, held-out ramp, and held-out rapid-pulse inputs in `results/rtl_reference_vectors/`. `tb_photoreceptor_baseline_trace.v` now reads these alongside the existing dark, step, and pulse vectors. `tb_photoreceptor_adaptive.v` adds checks for refresh-time live operands, invalid-cycle isolation, and held snapshot behavior. `tb_photoreceptor_comparison.v` distinguishes adaptive recomputation-path samples from currents actually applied at the pre-edge update.

## Verification executed

- Full Python suite: **52 passed**.
- Held-out policy experiment: completed, output schema and selected configurations recorded in JSON metadata.
- Existing budget sweep: 54 cases regenerated.
- Five added baseline Q16.24 CSV vectors exported from `BaselineFixedPoint`.
- Static text/source checks cover current-instance operand connections, snapshot reset/refresh updates, interval clamp/saturation, and counter saturation.
- No HDL compiler, Vivado, simulation, synthesis, implementation, timing, or power analysis was run.

## Historical user-reported hardware context only

The user previously reported a baseline top-level result of 16,348 LUTs, 283 FFs, 71 DSPs, 125 I/O blocks, and estimated total power 0.863 W; the adaptive result was 28,226 LUTs, 701 FFs, 71 DSPs, 125 I/O blocks, and estimated total power 0.899 W. The reports had low power confidence; adaptive LUT usage exceeded the reported 20,800-LUT capacity; substantial timing violations were also previously reported. Raw reports/settings were not independently reviewed. These are historical results from earlier sources/configurations and must not be attributed to the modified RTL.

## Limitations and unresolved work

1. Manually run all listed Vivado testbenches against current sources and investigate any failures. No testbench PASS is claimed for these edits.
2. Confirm the project’s Vivado filesets include the expected sources and that selected tops/parameters are correct.
3. Test `OPERAND_ISOLATION_ENABLE=1` and `=0` under the same adaptive scheduler/input vectors, and compare against `ADAPTIVE_ENABLE=0`.
4. Add or implement an RTL policy corresponding to per-current sensitivity only after fixed-point scaling, overflow, timing, and resource effects are specified and independently validated. The current Python result cannot be used as that validation.
5. Obtain matched hierarchical LUT/FF/DSP, timing, and activity-driven power reports for baseline, adaptive without isolation, and adaptive with isolation; verify the FPGA part and capacity. Refresh counters and Python call counts do not prove activity or power savings.
6. Broaden input amplitude/timing and invalid/reset stream testing; finite held-out success does not prove a bound.
7. Biological fidelity to Appendix B remains unresolved. The provisional current/state equations, unused `i_ca_pA_q` in `calcium_dynamics.v`, and source-paper input/calcium ambiguities remain explicit limitations.
8. Research novelty is not established; the focused literature search is preliminary.

## Research conclusion

The finite Python experiment supports continued investigation of a sensitivity-based selective-current heuristic on a provisional engineering model. It does **not** establish a guaranteed voltage controller, actual hardware activity reduction, power reduction, timing closure, FPGA feasibility, biological validity, or research novelty. The RTL work establishes only a candidate operand-isolation structure awaiting manual verification and hardware measurement.
