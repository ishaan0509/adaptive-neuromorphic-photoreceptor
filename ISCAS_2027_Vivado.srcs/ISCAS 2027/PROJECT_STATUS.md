# Project Status

## Research validity status: separate Appendix B equation implementation; biological validation blocked

The attached paper PDF was confirmed present and Appendix B was inspected using the supplied enlarged images for printed pages 8–10. A traceable equation/parameter transcription and implementation audit is in `PAPER_EQUATION_AUDIT.md`. This source review establishes that the existing Python and baseline RTL are materially different from the paper model; it does not establish biological fidelity.

The paper model now has a separate double-precision implementation, parameter/initial-condition module, equation tests, and a solver-convergence script. Its equations are a software transcription of Appendix B, not a validated reproduction: `J_hv(t)` has no source-defined units or stimulus waveform, the B.2/B.9 calcium coupling is unspecified, and the calcium reversal `log` base is unspecified. Consequently, the solver experiment uses an explicitly synthetic zero-input condition and both possible logarithm interpretations; it does not validate a published biological response. The provisional Python model, fixed-point reference, and RTL baseline remain unchanged.

### Phase 4A blocker investigation (2026-10-10)

- **`J_hv(t)`: BLOCKED.** Appendix B.2 (printed pp. 8–9) gives only its additive role in `dRh/dt`. Dimensional consistency requires units of `Rh/time`, but the source does not define Rh's units or give any optical-input conversion, stimulus amplitude, waveform, or timing. The Results figures/captions and summary tables report/reconstruct output behavior, not a numerical input series. The article's Data availability statement says data can be made available on request; no stimulus supplement was identified in available article metadata. A MATLAB input trace or author-supplied mapping is required.
- **B.2 vs B.9 calcium: PARTIALLY RESOLVED.** The equations use B.2 `Ca` in the phototransduction/cGMP and `Cab` binding subsystem, while B.9 `[Ca]s`/`[Ca]f` interact with diffusion, buffers, and the ionic/exchanger current source and feed B.5–B.7. The initial values differ (`Ca(0)=0.3` vs `[Ca]s(0)=[Ca]f(0)=0.0966`), and no equality, transfer equation, or conversion is given. Both groups are concentration-like and μM is supported by their parameter units, but anatomical mapping/coupling is not. Keep separate; complete coupled biological interpretation remains blocked.
- **`E_Ca` logarithm base: BLOCKED.** Appendix B.5 (printed p. 9) prints `-12.5 log([Ca]s/[Ca]0)` without a base. The cited Usui et al. (1996) reference is a horizontal-cell ionic-current model, and Kamiyama et al. (2009) is a rod-photoreceptor-network article; bibliographic records were checked, but their equation full texts were not available. The coefficient alone is not grounds to choose `ln` or `log10`. The float64 model continues to require an explicit branch.
- **Biological validation: BLOCKED.** The unresolved stimulus, calcium coupling, and `E_Ca` convention affect trajectories. No paper-defined response was run or compared with numerical reference data. Existing synthetic convergence results remain limited numerical checks only. Exact evidence and source locations are in `PAPER_EQUATION_AUDIT.md`.

Implemented items:
- consolidated parameter set in `photoreceptor_parameters.py`
- numerical helper functions in `numerical_methods.py`
- provisional continuous-time implementation in `photoreceptor_reference.py`
- Euler model with full, periodic, threshold-triggered, and empirical-budget cached-current policies in `discrete_time_model.py`
- reproducible experimental stimulus generation
- distinct solver-vs-Euler and Euler-vs-state-quantization metrics
- provisional trace plot generator and model documentation
- source-paper Appendix B equation transcription and Python/RTL discrepancy audit in `PAPER_EQUATION_AUDIT.md`
- separate double-precision Appendix B implementation in `paper_biological_model.py` with Appendix B parameter and initial-state transcription in `paper_biological_parameters.py`
- Python equation tests in `test_paper_biological_model.py`; the new focused test run passed 8 tests
- synthetic zero-input DOP853 step-size/tolerance convergence screening in `run_paper_model_convergence.py`; results are in `results/metrics/paper_model_solver_convergence.csv`
- static RTL review plus a corrected standalone fixed-point arithmetic primitive and scheduler

Python verification:
- Existing Python tests plus paper-model and adaptive-trace-metrics tests: latest `python -m pytest -q` reported 26 passed in 2.26 s.
- `compare_models.py` ran; its errors quantify the provisional equations only.
- `run_adaptive_experiments.py` ran and recorded scheduler outcomes. Periodic refresh at the tested interval diverged for several stimuli; it must not be considered an acceptable policy based on current results.
- The budget estimator is first-order empirical sensitivity tracking, not a mathematical bound.
- Uniform Q32.16 state quantization was explored as a rough SI-state quantization check only. It is not a complete fixed-point arithmetic model and does not match the current RTL format.
- On the provisional 1 s suite at `dt=1e-4 s`, threshold scheduling avoided about 54-92% of counted ionic-current formula evaluations depending on stimulus; the empirical-budget settings avoided about 38-89%. Some periodic cases became numerically unstable. These are current-function call counts, not total arithmetic savings or power estimates.
- The step-size convergence screen showed decreasing error as Euler `dt` was halved (from max voltage error 1.09 mV at `2e-4 s`, to 0.504 mV at `1e-4 s`, to 0.242 mV at `5e-5 s`) against the provisional fine-step solver trace. These are numerical-method checks for the old provisional equations only; they say nothing about the Appendix B model.
- The new source-equation implementation evaluates all transcribed Appendix B state derivatives and all nine B.1 membrane currents in float64. `J_hv(t)` and calcium `log` base are mandatory caller choices; B.2 and B.9 calcium state groups remain separate rather than being artificially identified.
- Focused paper-model tests: 8 passed. These test transcription-level equations, initial values, current aggregation, the five-state Ih conservation identity, voltage-rate removable singularities, custom parameter propagation, and explicit unresolved inputs. They do not establish source correctness beyond the transcribed pages or biological fidelity.
- Convergence screen: 5 ms synthetic zero-input run, with both natural-log and base-10 E_Ca branches. Maximum-step sweeps differed from the tighter DOP853 endpoint reference by at most 2.28e-13 across states. Tolerance sweeps ranged from 9.95e-14 to 1.35e-10; the largest error occurred with the deliberately loose base-10 case (`rtol=1e-5`). Per-state endpoint differences are exported. The aggregate maximum is across unlike units and is only a diagnostic, not a physical error norm. These are solver-consistency results under an assumed input and one of two unresolved log choices, not biological validation.
- One exploratory larger-step attempt failed when a solver trial state made `[Ca]s` non-positive, invalidating the logarithmic E_Ca expression. The convergence script now uses smaller maximum steps; the positivity failure is documented as a stability/domain constraint, not hidden with clipping.
- The article's figures and captions do not provide a numerical `J_hv` input series; Tables 1–2 provide model/value summaries rather than time-stamped input/output traces. Its Data availability statement says data will be made available on request. No biological-response plot or published-response comparison was generated.
- Diagnostic plots are explicitly labelled provisional and saved under `results/plots/`.

RTL verification:
- No HDL compile, simulation, waveform inspection, or synthesis was run, per user instruction.
- The existing `.xpr` file has empty design/simulation source lists and `TopModule=test`; the files are not confirmed registered with Vivado.
- User-confirmed Vivado result: `tb_fixed_point_math.v` PASS; `$finish called at time : 3 ns`.
- User-confirmed Vivado result: `tb_current_update_scheduler.v` PASS; `$finish called at time : 86 ns`.
- User-reported Vivado result (screenshot): `tb_phototransduction.v` PASS; `$finish` at 4 ns.
- User-reported Vivado result (screenshot): `tb_ionic_currents.v` PASS; `$finish` at 2 ns.
- User-reported Vivado result (screenshot): `tb_photoreceptor_baseline.v` PASS; `$finish` at 26 ns.
- User-reported XSim result: `tb_photoreceptor_baseline_trace.v` reported all 40 dark, 40 step, and 40 pulse post-edge rows matched the generated CSVs; final PASS and `$finish called at time : 1206 ns`.
- These Vivado results confirm that the corresponding assertions passed in the user's reported runs. They do not establish biological-model fidelity or accuracy beyond the checked vectors/scenario; the integrated baseline has not been broadly validated.
- Reworked the baseline RTL path to signed 40-bit Q16.24 engineering units: combinational phototransduction and six ionic currents, a 33-entry approximate sigmoid LUT and Euler gates, Euler calcium recovery/transfer, Euler membrane-voltage update, and a baseline top-level wrapper.
- Replaced `tb_phototransduction.v`, `tb_ionic_currents.v`, and `tb_photoreceptor_baseline.v` placeholder handshakes with fixed-point golden-vector/assertion checks and state/timing scenarios.
- The user-reported baseline and trace-test runs cover reset/current vectors and a 40-cycle dark, step, and pulse comparison against the generated raw-integer Python CSVs. This is evidence of agreement for the tested default RTL configuration and stimuli as reported by XSim, not broad parameter coverage or biological validation. The equations are provisional; the sigmoid LUT and fixed-point constants retain RTL approximations, and the calcium-current contribution is omitted. See `RTL_REVIEW.md`.
- Phase 5 adaptive RTL is now a separate 40-bit Q16.24 candidate; it does not alter `photoreceptor_baseline.v` or the passing baseline trace test. The new candidate and its benches are static-only until user-run Vivado results are supplied.
- Added `baseline_fixed_point.py`, which mirrors the default 40-bit Q16.24 RTL arithmetic, exact 33-word LUT/indexing, pre-edge calculations, asynchronous reset values, and valid/idle ordering.
- Added deterministic 40-cycle dark, step, and pulse inputs plus a CSV exporter for signed raw-Q cycle values and exported `baseline_dark_q16_24.csv`, `baseline_step_q16_24.csv`, and `baseline_pulse_q16_24.csv`.
- Added `tb_photoreceptor_baseline_trace.v`, which reads those three CSVs, drives each stimulus row in Vivado, and compares every observable post-edge state/current/status output.
- User-reported XSim output now shows PASS for all 40 rows in each scenario and final `$finish` at 1206 ns. The run demonstrates that XSim accepted the signed-decimal CSV parsing and reported exact matches; the assistant did not independently inspect simulator waveforms or raw logs.
- Added Python-only tests for arithmetic boundaries, LUT behavior, reset/valid/idle semantics, trajectory generation, and CSV export. No HDL tools were run.
- The reference intentionally mirrors the RTL's unused `i_ca_pA_q` port (zero calcium-current contribution) and exact LUT/constant approximations. User-reported XSim output confirms all three generated CSV scenarios matched in the stated default configuration; no agreement outside those vectors is claimed. See `RTL_FIXED_POINT_REFERENCE.md`.
- Source audit finding: the baseline's direct light gain, generic gate LUT, single-state gates, omitted external currents, simplified calcium states and provisional constants/initial conditions do not match Appendix B. The calcium-current term is explicitly present in the paper's B.9 shell-calcium equation; its omission is not paper-supported even if it is below one RTL LSB.
- The sigmoid LUT and Q16.24 wrapping/truncation are implementation choices absent from the paper. Keep them isolated to the passing engineering baseline; do not describe them as biological equations.

Next steps:
1. Request the authors' MATLAB implementation or supplementary data that defines `J_hv(t)`, its physical units, and the simulation stimulus/timing.
2. Request or inspect a source that explicitly states the B.2-to-B.9 calcium state coupling and the `E_Ca` logarithm convention. Do not infer them from model plausibility.
3. Cross-check the separate implementation's transcribed equations and parameters against a legible original-paper copy; preserve unresolved branches and separate calcium groups until source evidence says otherwise.
4. After the source definitions are resolved, run the paper-specified stimulus and compare with any recoverable numerical published data. Keep solver convergence separate from biological validation.
5. Only then define and quantify discrete-time/fixed-point errors relative to the float64 source-equation model. Keep the passing engineering baseline intact.
6. Expand baseline RTL coverage independently; any later correction requires regenerated vectors and user-run Vivado tests.
7. Run the Phase 5 adaptive candidate tests manually and evaluate captured errors/recomputation counts. Keep those results scoped to the provisional engineering baseline; separately validated paper-model equations are still required before any biological claim.

## Phase 5 — adaptive RTL candidate integration

### Status

- Adaptive current-cache datapath and trigger modules: **IMPLEMENTED, STATIC REVIEW ONLY**.
- Existing full-update baseline: **PRESERVED**; its equations and ports were not changed.
- New adaptive scheduler/error-budget/integrated tests: **PREPARED, NOT RUN**. No HDL tool was invoked.
- Baseline-versus-adaptive CSV capture and Python metrics utility: **PREPARED, NOT RUN ON SIMULATOR DATA**.
- Adaptive accuracy and recomputation metrics: **PENDING user Vivado/XSim output**.
- Biological fidelity and power savings: **NOT ESTABLISHED**.

### Architecture

`photoreceptor_adaptive.v` uses the baseline's 40-bit signed Q16.24 current, gate, calcium, and membrane modules. It caches the six ionic currents as one group (`I_h`, `I_Kv`, `I_Ca`, `I_ClCa`, `I_KCa`, and leak); `I_photo` remains combinational each sample. Gate, calcium, and membrane state updates remain active on every accepted sample. The scheduler tracks accepted samples since the last group refresh and requires refresh for first initialization, any changed light value since refresh, a 1 mV absolute voltage excursion from the refresh snapshot, projected accumulated error-proxy budget exhaustion, or maximum interval (8 accepted samples by default). The 16-bit age counter is intended for intervals no greater than 65535.

Reset asynchronously clears cache-valid state and the update count. Cached current registers reset to zero, but combinational selection uses live current values until a valid refresh has occurred; the first accepted sample always refreshes. Invalid samples deassert valid and hold state, cache, age, and budget. The budget accumulator saturates on unsigned overflow and resets on refresh. Invalid input is excluded from refresh-event assertion. `photoreceptor_top` selects the baseline at `ADAPTIVE_ENABLE=0` and adaptive when nonzero; the actual RTL parameter default is 1, so baseline mode must be explicitly selected. `MAX_REFRESH_INTERVAL=1` forces its full-refresh fallback.

The purported voltage-error budget is explicitly an **unvalidated heuristic**: each accepted update adds `abs(V[n]-V[n-1]) >> 4` in raw Q16.24 units. This scaled voltage-step proxy is not derived from stale-current sensitivity, cannot guarantee a bound on voltage error, and must not be described as a conservative error estimate. Light and interval trigger checks are independent of it. `MAX_REFRESH_INTERVAL=1` provides a full-refresh fallback.

### Test and comparison workflow

Run manually in Vivado in this order, adding the RTL dependencies of the selected top:

1. `tb_current_update_scheduler.v` — initialization, no-trigger hold, maximum interval, voltage/light changes, explicit force, error-budget force, and invalid-cycle behavior.
2. `tb_voltage_error_budget.v` — accumulation, projected threshold crossing, clear, saturation, and valid timing.
3. `tb_photoreceptor_adaptive.v` — first-refresh cache initialization, light-triggered refresh, valid output, and invalid-cycle state hold.
4. `tb_edge_cases.v` — checks known adaptive voltage/current outputs for dark and unit-light inputs.
5. `tb_photoreceptor_comparison.v` — writes `adaptive_comparison_trace.csv` for dark, step, pulse, and alternating-light inputs and checks mandatory light-change/max-age refresh behavior. Run for at least 2000 ns or use `run -all`; 1000 ns is insufficient to finish its four 40-cycle scenarios.

Historical user-run XSim update (2026-10-10): scheduler PASS at 116 ns, adaptive checks PASS at 36 ns, edge-case PASS at 26 ns, corrected voltage-budget PASS at 96 ns, and comparison PASS for all 4 scenarios x 40 cycles at 1680 ns. These were user-reported outcomes; no HDL tool was run by the assistant in this update. The previous CSV used the former mixed-timing schema and is superseded.

The six adaptive ionic-current modules remain combinational, but the latest RTL adds default-on input operand isolation so their voltage/gate/calcium operands hold between accepted refreshes. This is intended to suppress input-driven internal toggling; no activity or power reduction has been measured. The current global refresh policy is still heuristic and does not guarantee voltage accuracy.

### Phase 5 checklist

- COMPLETE — Preserve the reported-passing baseline and use it as the full-update reference.
- COMPLETE — Replace stale 16-bit/obsolete adaptive module interfaces with a Q16.24 cached-current design using the current baseline primitives.
- COMPLETE — Define refresh triggers, age handling, reset/cache-valid behavior, state-update ordering, and an explicit full-refresh fallback.
- COMPLETE — Prepare scheduler, budget, adaptive-state, and four-stimulus comparison testbenches plus a trace metrics script.
- HISTORICAL USER REPORT — Earlier Vivado/XSim runs reported scheduler, budget, adaptive, edge-case, and 4 x 40 comparison bench PASS; not rerun or revalidated in this update.
- COMPLETE — User supplied analyzer output for the regenerated 160-row, 65-column paired trace; local strict parsing reproduced it. Dark/step/pulse/alternating observed max voltage differences: 0.178403616/0.127412140/0.186290324/0 mV. Applied total-current max differences: 30.8087424/30.8087424/30.8087424/0 pA. Nominal refresh-count reductions: 55.00/27.50/20.00/0.00%. These are observed/proxy metrics, not guaranteed accuracy or hardware activity.
- PENDING — Decide whether the measured trajectory error/recomputation tradeoff meets explicitly specified engineering requirements; no tolerance was supplied.
- BLOCKED — Claim any mathematically bounded voltage error; current budget proxy has no proof.
- BLOCKED — Claim paper fidelity, power savings, or research novelty; biological blockers remain, and the only hardware power estimate supplied so far is marked low confidence.

### Adaptive trace and metrics hardening (2026-10-10)

Changed files for this evaluation update:

- `sim_1/new/tb_photoreceptor_comparison.v` now writes a paired row per accepted sample. It emits scenario and cycle IDs, `valid_in`, duplicate baseline/adaptive light inputs, the pre-edge refresh decision and counters, baseline pre-edge and applied currents, adaptive live and selected/applied currents, photocurrent, total currents, voltage before the edge, then appends post-edge states and counters. Capturing current fields before the active edge distinguishes the values used by that voltage update from recalculated post-edge outputs.
- `ISCAS 2027/adaptive_trace_metrics.py` now rejects an incomplete/invalid schema, wrong/missing/unexpected scenario IDs, row-count/cycle-order defects, invalid rows, mismatched light inputs, malformed integers, inconsistent counters and total-current Q16.24 sums. It never sorts rows to conceal ordering errors.
- `ISCAS 2027/test_adaptive_trace_metrics.py` covers valid metric calculations and malformed trace/schema, missing scenarios, wrong row count, duplicate/nonconsecutive/out-of-order cycles, invalid samples, malformed values, input mismatch, and sum consistency.
- `RTL_REVIEW.md` records the trace timing, scaling, units, formulas, and limits.

The fixed-point raw word is signed 40-bit Q16.24 (`real = raw / 2^24`). Voltage is mV, current is pA, calcium states are mM, gate states are dimensionless, and light is logged as the raw normalized Q16.24 input. Observed voltage error is computed from paired post-edge states: `max(abs(V_adapt - V_base))/2^24` and `sqrt(sum((V_adapt - V_base)^2)/N)/2^24`, in mV. Applied total-current difference is computed from paired pre-edge values actually used for the membrane update, with identical max/RMS formulas in pA. These are measured sample errors, not a guaranteed error bound.

The renamed `nominal_refresh_count_reduction_percent` is based on `6*refreshes` versus `6*accepted_samples`. Baseline nominal formula counts are testbench bookkeeping, and the adaptive counter counts refresh-triggered current updates. Neither measures logic activity or power. Operand isolation now holds current-module inputs between refreshes, but actual switching, area, and power effects require matched implementation/activity reports.

Python-only results for this update: targeted trace-metrics tests passed (7 passed). Running the hardened metrics CLI on the existing CSV correctly rejected its obsolete header. No current-format simulator CSV exists yet; generating one requires the user-run comparison bench.

Correction to the earlier pending-validation paragraph: the latest user-provided trace is the current-format regenerated CSV, not the obsolete header. The analyzer passed against it locally and reproduced the user's output; the targeted Python tests passed 8/8. The CSV contains 160 rows and 65 columns (four 40-cycle scenarios). This does not establish that the updated comparison bench itself reported PASS; no HDL transcript for that run was included. The old paragraph above describing an obsolete CSV is superseded.

#### Next manual Vivado checks

1. Add/select `tb_photoreceptor_comparison.v` as the simulation top with the previously documented baseline, adaptive, scheduler, budget, and top-wrapper source dependencies.
2. Run `run -all` or at least 2000 ns. Confirm the bench completion summary; retain the simulator transcript.
3. Inspect the regenerated `results/metrics/adaptive_comparison_trace.csv`: expect four scenario IDs, cycles 0–39 per scenario, `valid_in=1`, and one complete paired row per cycle. Confirm current columns are pre-edge/applied and state columns are post-edge.
4. In the project Python folder, run `python -m pytest -q test_adaptive_trace_metrics.py`, then `python adaptive_trace_metrics.py results/metrics/adaptive_comparison_trace.csv`.
5. If trace validation fails, do not interpret partial metrics; diagnose the CSV/schema or simulator run first. No new HDL result is claimed here.

### Static RTL area optimization trial (2026-10-10)

The user-provided Vivado summary reports 27,673 LUTs for baseline and 28,226 for adaptive against 20,800 available; both exceed capacity. It also attributes 13,995 LUTs hierarchically to `calcium_dynamics`. These figures have not been independently checked because the detailed utilization and timing reports were not present for review.

An exact-width arithmetic trial was applied to shared RTL used by both baseline and adaptive:

- Q-format multiply intermediates are now `DATA_WIDTH + FRAC_BITS` bits when `FRAC_BITS <= DATA_WIDTH` (64 bits for the default 40/24 design), with the prior `2*DATA_WIDTH` width retained for larger fractional widths.
- Scaled Q-format division numerators use the same exact-width rule. For default signed 40-bit operands shifted left 24 places, 64 bits represent the full signed scaled value; no overflow or quotient rounding behavior is intentionally changed.
- The five configured gate slopes are exact multiples of Q16.24 `SCALE`; `gate_update.v` now cancels that common scale and divides the raw voltage difference by the corresponding integer slope (8, 10, 8, 5, or 6). A generate-time fallback retains the original general Q division for zero or non-integral slope parameters.
- The phototransduction product uses the matching exact intermediate width.
- The sigmoid LUT index replaces division by `HALF_STEP` (a positive power of two) with a right shift. In the non-clamped branch, the offset makes `shifted_x` positive, so the shift gives the same integer index.
- No biological/current/state equations, fixed-point constants, update order, cache policy, or baseline/adaptive selection were changed. In particular, the ignored `i_ca_pA_q` input remains unchanged.

Changed files: `sources_1/new/calcium_dynamics.v`, `ca_current.v`, `clca_current.v`, `gate_update.v`, `ih_current.v`, `kca_current.v`, `kv_current.v`, `leakage_current.v`, `membrane_voltage.v`, `phototransduction.v`, and `sigmoid_lut.v`; added `ISCAS 2027/test_rtl_arithmetic_widths.py`; updated `RTL_REVIEW.md` and `PROJECT_STATUS.md`.

The new Python tests compare the narrowed arithmetic against the former full-width fixed-point definitions, including exhaustive reduced-width products, Q16.24 signed extremes and randomized multiply/divide vectors, exact gate-slope cancellation, sigmoid index boundaries/random interior points, and source checks for all edited datapaths. Focused tests (`test_rtl_arithmetic_widths.py` and `test_baseline_fixed_point.py`) passed: **20 passed**. The complete Python project suite passed: **46 passed**. These tests establish arithmetic equivalence in the Python model only. They do not compile RTL, prove Vivado infers narrower hardware, or establish any LUT reduction.

#### Required manual Vivado verification

1. Preserve a copy/branch of the pre-change RTL as the golden build. Use the same Vivado 2024.1 version, FPGA part, constraints, top, and synthesis options for each design.
2. Run the existing fixed-point, phototransduction, ionic-current, baseline, adaptive, and four-scenario comparison benches against the changed RTL. Require exact raw-value matches to the existing baseline Python reference for the default configuration; retain simulator logs.
3. Synthesize baseline and adaptive separately. Export hierarchical utilization and timing reports, including leaf-instance LUT/FF/DSP, inferred multiplier/DSP details, and worst-path/slack data.
4. Compare before/after LUT, FF, DSP, and timing using identical settings. Only a new report can establish area impact; stop if arithmetic regressions appear or timing/resource results worsen beyond project requirements.

Status: RTL arithmetic-width changes and Python equivalence tests are present; **Python verification is complete**. The user supplied a top-level implementation/power screenshot for both parameter selections, but raw synthesis/timing/power reports and updated HDL-regression output are still pending. No LUT reduction or timing improvement from the arithmetic edit is established. Biological validation and actual power/activity claims remain unresolved.

### User-reported top-level implementation and power comparison (2026-10-10)

The user supplied screenshots of separate `photoreceptor_top` runs, selecting baseline with `ADAPTIVE_ENABLE=0` and adaptive with `ADAPTIVE_ENABLE=1`. The values below are transcribed from the supplied screenshots; the underlying Vivado reports, exact FPGA part, constraints, clock/activity assumptions, and run logs were not provided for independent verification.

| Metric | Baseline (`ADAPTIVE_ENABLE=0`) | Adaptive (`ADAPTIVE_ENABLE=1`) | Adaptive change vs. baseline |
|---|---:|---:|---:|
| Total on-chip power estimate | 0.863 W | 0.899 W | +4.17% |
| Dynamic power estimate | 0.791 W | 0.827 W | +4.55% |
| Device static power estimate | 0.072 W | 0.072 W | 0.00% |
| Top-level implementation LUTs | 16,348 | 28,226 | +72.66% |
| Flip-flops | 283 | 701 | +147.70% |
| DSP blocks | 71 | 71 | 0.00% |
| I/O blocks | 125 | 125 | 0.00% |
| Power report confidence | Low | Low | — |

The screenshots identify 20,800 available LUTs. Relative to that stated capacity, the reported baseline uses 78.60% (4,452 LUT headroom); adaptive uses 135.70% (7,426 LUTs above capacity). Thus, the reported adaptive configuration does not fit this LUT capacity, while the reported baseline does. These figures are the user's run results and do not constitute an independently repeated run.

The user-provided historical table (from before the operand-isolation edit) reports estimated dynamic and total power **higher**, not lower, for the adaptive configuration. Both estimates have low confidence, and activity assumptions/report details are absent. This is not proof of actual power increase or a result for the modified source. No activity or power result exists for the current operand-isolated RTL.

The earlier baseline LUT value of 27,673 was a distinct prior report and conflicts with this later 16,348 baseline screenshot; do not combine these runs or infer a before/after optimization delta from them. Adaptive is 28,226 in both summaries, but identical source/constraints/settings are not established. Preserve the raw Vivado reports and record top, `ADAPTIVE_ENABLE`, part, constraints, tool version, synthesis/implementation options, and power stimulus/SAIF details before drawing comparisons.

### Python adaptive experiment rerun (2026-10-10)

The existing experiment runner was executed without overwriting its existing `results/metrics/adaptive_experiments.csv`. New results are in `results/metrics/area_followup_python/adaptive_experiments.csv`. This was Python-only execution of the existing provisional model, using the runner defaults: 1 s duration, 0.1 ms step, 10,001 grid points, nine stimuli (dark, step-up/down, pulse, repeated pulses, ramp, sinusoidal periodic, abrupt transitions, steady state), and four scheduler modes (`full`, `periodic`, `threshold`, `budget_empirical`). The output contains 36 scenario/mode rows.

- Full update is the reference: 60,006 ionic-current function evaluations per scenario (six currents at 10,001 grid points).
- The periodic configuration (`periodic_interval=4`, `max_interval=16`) failed the model's 1 V numerical runaway guard on 7 of 9 stimuli. It completed on sinusoidal periodic and steady-state cases; steady-state maximum voltage error was 4.545 mV with an 80.0% formula-evaluation count reduction.
- The threshold configuration (`current_error_threshold=1e-12`, `max_interval=16`) completed all nine cases; maximum observed voltage error ranged from 0 to 0.07520 mV and nominal Python current-function evaluation reductions ranged from 0% (the rapidly changing sinusoid forced updates) to 92.09%.
- The empirical-budget configuration (`voltage_error_budget=1e-5 V`, `max_interval=16`, transition tolerance `1e-2`) completed all nine cases; maximum observed voltage error ranged from 0 to 0.05158 mV, with Python current-function evaluation reductions from 37.68% to 89.44%.
- The empirical budget proxy's maximum estimated value stayed near 10 μV in successful runs, while observed trajectory error reached 51.58 μV in the periodic-light case and 32.14 μV in the ramp case. It is therefore not a guaranteed error bound. No tolerance-exceedance rate was configured or reported, so these results do not establish tolerance compliance.

Because `discrete_time_model.py` calls its current equations only for refreshed currents, these are actual avoided **Python model function evaluations**, unlike RTL refresh counters. They do not measure Verilog switching, FPGA resource use, energy, or power. Stimulus amplitudes/timings are the runner's single default set, and this rerun does not cover reset/invalid RTL behavior or multi-amplitude/tolerance/interval sweeps. Keep the model explicitly provisional and not biologically validated.

### Empirical budget / maximum-interval sweep (Python only)

`run_budget_sweep.py` was executed at 1 s duration and 0.1 ms timestep across the fixed nine-stimulus suite, with trigger settings 1/10/100 μV and max intervals 4/16. The CSV contains 54 rows; all 54 cases were stable and all fields validated as finite. A sample-accounting correction now calculates voltage/current errors and strict tolerance-exceedance counts over the 10,000 post-initial state updates per case. The six-current full-update denominator is 60,006 Python function evaluations per stimulus (all 10,001 time points), or 540,054 across the nine stimuli.

| Trigger | Max interval | Maximum observed voltage difference | Samples over 10 / 50 / 100 μV (out of 90,000) | Weighted Python evaluation reduction |
|---:|---:|---:|---:|---:|
| 1 μV | 4 | 7.21549 μV | 0 / 0 / 0 | 48.96% |
| 1 μV | 16 | 7.21549 μV | 0 / 0 / 0 | 52.38% |
| 10 μV | 4 | 51.50652 μV | 5,780 / 22 / 0 | 61.68% |
| 10 μV | 16 | 51.57906 μV | 5,903 / 23 / 0 | 65.72% |
| 100 μV | 4 | 301.89304 μV | 34,386 / 9,277 / 3,598 | 73.99% |
| 100 μV | 16 | 308.30578 μV | 40,283 / 11,344 / 5,637 | 79.15% |

Observed trajectory errors exceed the configured trigger, so the accumulated trigger remains a heuristic and is not a guaranteed voltage bound. These evaluation reductions are Python function-call counts only, not RTL switching or power. The current modules remain combinational; operand isolation holds their operands outside refresh cycles. Sweep details: `results/metrics/area_followup_python/empirical_budget_sweep.csv` and `budget_sweep_metadata.json`.

### Current research decision

The research question remains unestablished. A Python per-current sensitivity policy outperformed the accumulated proxy at the fixed 10 μV target on the finite held-out set, but this policy is not yet implemented in RTL. Operand isolation is implemented around the six adaptive current modules, but no HDL or hardware activity result exists. Do not claim a formal error guarantee, power/area/timing benefit, FPGA feasibility, biological fidelity, or novelty. Manually run the new simulation regression, compare `OPERAND_ISOLATION_ENABLE=0/1` with the same adaptive scheduler, and collect matched synthesis/timing/activity reports before considering implementation benefit.

### Final one-pass follow-up (2026-10-10)

The user-requested follow-up included a deterministic held-out Python comparison, operand-isolation RTL, reference vectors, static boundary checks, and a manual verification plan. Pre-change copies of 16 in-scope files were saved under the session's `files/phase7_prechange/` backup directory (outside the project tree).

- Full Python tests: **52 passed**.
- Existing 54-case budget sweep rerun after correcting applied-current alignment to use sample `i` for the transition producing voltage sample `i+1`; the CSV still has 54 stable cases.
- Held-out comparison: per-current sensitivity (`1e-14 A`, max age 16) vs accumulated proxy (`1e-6 V`, max age 16), selected only using nine training stimuli and a fixed 10 μV maximum-observed-error target.
- Held-out per-current sensitivity: max 1.48659 μV; pooled RMS 0.21603 μV; pooled MAE 0.08455 μV; 0 threshold exceedances; 38.08% Python current-function evaluation reduction (222,934/360,036 calls).
- Held-out accumulated proxy: max 6.97410 μV; pooled RMS 0.31175 μV; pooled MAE 0.04978 μV; 0 threshold exceedances; 33.00% reduction (241,224/360,036 calls).
- Updated comparison testbench labels identify isolated recomputation-path values, and adaptive testbench assertions check refresh-time live operands and held snapshots.
- Added five generated 40-cycle baseline Q16.24 vectors (alternating, held-out step, pulse, ramp, rapid pulse) and added them to the baseline trace bench alongside existing dark/step/pulse vectors.
- New static RTL changes: default-on adaptive current-input operand isolation; parameter `OPERAND_ISOLATION_ENABLE` to bypass it for an adaptive A/B run; 16-bit scheduler interval clamp/saturation; 32-bit recomputation-counter saturation.
- The selected Python per-current sensitivity algorithm was **not** implemented in RTL. RTL retains its pre-existing group-refresh triggers. This unresolved algorithm gap is explicit; held-out Python metrics do not validate the current RTL.
- No Vivado, HDL compiler/simulator, synthesis, timing, implementation, or power tools were run. All modified RTL/testbenches await user-run Vivado verification.
