Error-Constrained Selective Ionic-Current Updates for a Digital Neuromorphic Photoreceptor

**Purpose:** A consolidated, paper-preparation handoff for the project: its research question, model lineage, methods, experiments, results, RTL changes, verification status, limitations, and reproducibility map. This file is intended to make the project understandable from one document. It is not a substitute for the cited paper, raw data, source code, or a final independently reviewed manuscript.

**Evidence date:** 10 October 2026
**Project state:** Python experiments rerun; operand-isolation RTL and benches edited; current RTL edits have not been compiled or simulated by the assistant. Vivado implementation evidence below is historical and user-reported.

> **Research status:** preliminary engineering study. The 52 passing tests are Python tests, not HDL tests. The reported adaptive Python reductions are function-call counts, not FPGA activity or power. The provisional RTL is not biologically validated and does not reproduce the cited paper.

### Repository layout

- [`ISCAS_2027_Vivado.xpr`](ISCAS_2027_Vivado.xpr) — Vivado 2024.1 project.
- [`ISCAS_2027_Vivado.srcs/sources_1/new/`](ISCAS_2027_Vivado.srcs/sources_1/new/) — baseline, adaptive, arithmetic, scheduler, and model RTL.
- [`ISCAS_2027_Vivado.srcs/sim_1/new/`](ISCAS_2027_Vivado.srcs/sim_1/new/) — simulation testbenches; current edited benches require a fresh manual Vivado run.
- [`ISCAS_2027_Vivado.srcs/ISCAS 2027/`](ISCAS_2027_Vivado.srcs/ISCAS%202027/) — Python models, experiments, audit documents, tests, and generated datasets.
- [`ISCAS_2027_Vivado.srcs/ISCAS 2027/results/`](ISCAS_2027_Vivado.srcs/ISCAS%202027/results/) — Python metrics, plots, and Q16.24 reference vectors.

The source-paper PDFs, local virtual environment, editor settings, caches, and simulator logs are intentionally not included. `README.md` is the repository overview and research handoff; the supporting project files and raw experiment artifacts are retained in the paths above.

---

## 1. Executive summary

This project investigates whether ionic-current computations in a digital photoreceptor model can be updated less often than the membrane/gating/calcium state while keeping the voltage trajectory close to a full-update reference. It contains:

1. A **provisional engineering model** implemented in Python and signed fixed-point RTL.
2. A separate, double-precision **transcription of equations visible in Appendix B** of Shah, Sonkusare, and Rathod (2023).
3. Python scheduler experiments using cached-current policies.
4. An RTL candidate that caches six ionic currents and now includes configurable operand isolation around the combinational current modules.

The quantitative Python results support further testing of a sensitivity-based scheduler **on this provisional model and on the finite traces tested**. The RTL does not implement that selected Python sensitivity policy: RTL remains a group-refresh heuristic. Recent operand-isolation changes have not received HDL simulation or new Vivado implementation/activity measurements.

**No biological validation, guaranteed voltage-error bound, proven hardware-activity reduction, power savings, FPGA feasibility, or research novelty has been established.** Historical user-reported implementation data show substantial area concerns and low-confidence power estimates, not a demonstrated benefit.

### Current bottom line

| Topic | What current evidence supports | What remains unestablished |
|---|---|---|
| Python adaptive algorithms | Reproducible finite comparisons against a full-update Euler reference; a sensitivity policy met a training-selected 10 μV observed-error criterion on nine training and six held-out waveforms. | Generalization, formal error guarantees, agreement with the source paper, RTL equivalence, or hardware savings. |
| Adaptive RTL | Static source contains group refresh, cached currents, and default-on operand-isolation muxes/snapshots. | Compilation/simulation of latest edits; equivalence; actual switching reduction; area/timing/power outcome. |
| Baseline RTL | Earlier user-reported Vivado tests and traces matched the project’s fixed-point Python reference for a limited set of tests. | Paper fidelity; broad coverage; validation of the latest changed source set. |
| Paper model | A separate float64 transcription of the legible Appendix B equations and equation-level Python tests exist. | Complete model interpretation and biological response validation; required inputs and conventions remain unspecified. |
| Novelty | A candidate research direction can be formulated around adaptive digital current evaluation and operand isolation. | A systematic literature review, differentiating evidence, and measured hardware contribution. Do not claim novelty or acceptance. |

---

## 2. Research framing

### 2.1 Source article and scope

The project reviewed:

> Payal Shah, Reena Sonkusare, and Surendra S. Rathod, “FinFET based photoreceptor for silicon retina to reduce power consumption,” *Biosensors and Bioelectronics: X* 14 (2023), article 100330. DOI: [10.1016/j.biosx.2023.100330](https://doi.org/10.1016/j.biosx.2023.100330).

Appendix B (printed pages 8–10) was inspected from the PDF and the enlarged source images. The article concerns a FinFET-based photoreceptor. This project’s present RTL is a digital fixed-point engineering model; it is **not a reproduction of the article’s FinFET device/circuit implementation** and the provisional equations materially differ from the paper’s stated equations.

### 2.2 Research question

For a defined photoreceptor model and stimulus suite, can selective ionic-current updating:

1. Meet a voltage-error criterion declared before evaluation;
2. Avoid actual unnecessary computation or switching in the target implementation; and
3. Remain acceptable in resource utilization and timing relative to an otherwise matched full-update baseline?

This is a falsifiable research question, not a conclusion. A defensible hardware claim requires matched implementation conditions and activity evidence, not just a count of scheduler refreshes.

### 2.3 Candidate contribution framing (not an established novelty claim)

A cautious future paper could evaluate a **digital adaptive-current-update architecture** that combines cached ionic-current values, a refresh policy, and operand isolation, comparing it with an always-refresh reference on a declared model and input suite. The current project does not yet support claiming that this is novel, biologically accurate, lower-power, smaller, or better than prior work. Before claiming novelty, conduct a systematic literature review and clearly distinguish the contribution from prior event-driven, adaptive-step, clock-gated, operand-isolated, and neuromorphic retina designs.

---

## 3. Model lineage and scientific assumptions

### 3.1 Three model artifacts that must not be conflated

| Artifact | Purpose | Arithmetic/model status |
|---|---|---|
| Provisional Python model (`photoreceptor_reference.py`, `discrete_time_model.py`) | Engineering reference and scheduler exploration. | Simplified provisional equations; primarily double precision; not a validated biological model. |
| Baseline fixed-point reference and RTL (`baseline_fixed_point.py`, `photoreceptor_baseline.v`) | Cycle-level engineering implementation and comparison reference. | Signed 40-bit Q16.24; Euler-style updates; truncation/wrap behavior; baseline equations remain the full-update reference. |
| Paper transcription (`paper_biological_model.py`, `paper_biological_parameters.py`) | Separate software transcription of the visible Appendix B equations. | Float64 and explicit caller choices for undefined paper inputs/conventions; equation tests only; not coupled to or validated against the provisional RTL. |

The Python adaptive experiments compare candidate policies to the **provisional Python full-update model**, not the paper transcription and not automatically the RTL. The fixed-point CSV vectors compare the baseline RTL against the project’s bit-accurate fixed-point reference, not against biological measurements or the source article.

### 3.2 Provisional RTL arithmetic and units

- Default data words are signed 40-bit Q16.24; one real unit is `raw_integer / 2^24`.
- Engineering-unit conventions used in the RTL review: voltage in mV, conductance in nS, current in pA, capacitance in pF, time in ms, calcium in mM, and normalized light.
- Under these conventions, `nS × mV = pA` and `pA / pF = mV/ms`.
- RTL multiplications/divisions rescale through fixed-point shifts/truncation. State/current arithmetic is not generally protected by saturation or overflow reporting.
- The sigmoid approximation is a finite LUT rather than the exact floating-point exponential.
- `calcium_dynamics.v` currently omits/does not use the `i_ca_pA_q` contribution identified in the source review. The associated concentration increment was described as sub-LSB at the tested operating scale, but that does not make omission a paper-derived equation or establish a general error bound. Do not change or justify this scientific assumption silently.

### 3.3 Differences and unresolved paper interpretation

Appendix B includes a membrane-current sum with `I_ex` and `I_ex2`, phototransduction equations driven by `J_hv(t)`, and multiple calcium state groups. The current provisional RTL instead uses simplified normalized-light photocurrent, LUT gate dynamics, provisional conductances/reversal values, and simplified calcium dynamics; it does not implement all Appendix B terms. The paper transcription is therefore kept separate.

Three material source gaps remain:

1. **Phototransduction stimulus `J_hv(t)`:** Appendix B gives its additive role but no waveform, amplitude, units conversion, or mapping from optical stimulus.
2. **Calcium state coupling:** Appendix B.2 calcium/binding states and B.9 shell/free calcium states are not explicitly related. They remain separate in the transcription.
3. **Calcium reversal logarithm:** the printed equation uses `log` without specifying natural or base-10 logarithm. The software transcription requires an explicit branch.

No machine-readable biological input/output trace was available for comparison. Thus the paper-equation transcription and its synthetic numerical checks do not constitute biological validation.

---

## 4. Architecture and algorithms

### 4.1 Full-update baseline

At each accepted sample, the baseline evaluates photocurrent and six ionic currents from the current pre-edge voltage, gating/calcium states, and light. The membrane, gate, and calcium states update at the active edge using these pre-edge quantities. The six ionic-current terms are:

`I_h`, `I_Kv`, `I_Ca`, `I_Cl(Ca)`, `I_K(Ca)`, and `I_L`.

The baseline is retained as the full-update reference. Its equations were not changed to improve the adaptive comparison.

### 4.2 Python scheduler experiments

The Python model contains full, periodic, threshold/sensitivity, and accumulated-budget modes. In the selective modes, an ionic-current function is called only when that current is refreshed. The experiment runner checks the exported evaluation count against the refresh mask. Those counts are actual Python function-call counts, not FPGA switching measurements.

The local first-order sensitivity estimate has the form:

`estimated_stale_error_i = sum_j(abs((dI_i/dx_j at refresh) * (x_j - x_j_at_refresh)))`

The accumulated voltage proxy integrates a heuristic derived from an estimated voltage-step/error contribution (project code scales the proxy using `dt/C_m` and triggers refresh at its selected threshold). The sensitivity estimate neglects nonlinear remainder and domain/parameter uncertainty. Neither expression is a mathematically proven upper bound.

### 4.3 Existing RTL scheduler

RTL refreshes the six ionic currents as one group when a trigger requires it. Source-inspected triggers include:

1. No valid cache has been initialized after reset;
2. Light differs from the light value saved at the prior refresh;
3. Voltage moves from its refresh snapshot by a configured threshold;
4. A voltage-step proxy reaches a configured budget; or
5. Maximum accepted-sample age is reached.

`I_photo` remains live/combinational, and membrane/gate/calcium state updates continue on each accepted valid sample. Invalid samples hold the state/cache and do not advance the accepted-sample age. The first accepted sample is forced to refresh. A maximum refresh interval of one requests refresh on every accepted sample.

The RTL policy is **not** the Python per-current sensitivity policy used for the selected held-out results. RTL values and fixed-point thresholds are not calibrated to the Python `1e-14 A` threshold.

### 4.4 Operand-isolation change

`OPERAND_ISOLATION_ENABLE` is exposed by `photoreceptor_top` and defaults to enabled for the adaptive path. For current-module operands, muxes provide live pre-edge states on refresh and reset-initialized snapshot values between refreshes. Snapshots and cached values update on an accepted refresh (`valid_in && refresh_all`). The intent is to keep current-module inputs stable between refreshes.

This is an **intended structural switching-reduction mechanism**, not a measured activity result. The current modules remain combinational. The isolation muxes and snapshot registers may increase LUT/FF utilization or affect timing. The only meaningful comparisons are matched runs of:

| Configuration | `ADAPTIVE_ENABLE` | `OPERAND_ISOLATION_ENABLE` |
|---|---:|---:|
| Baseline full update | 0 | not applicable |
| Adaptive, isolation bypassed | 1 | 0 |
| Adaptive, operand isolation enabled | 1 | 1 |

### 4.5 Counter and boundary handling changes

Static RTL changes clamp oversized maximum intervals to the representable/effective 65,536-sample range, saturate the 16-bit accepted-sample age counter, and saturate the 32-bit recomputation counter instead of silently wrapping. Reset, invalid-sample, and first-refresh behavior are covered by authored assertions but the latest edited testbench has not been run by the assistant.

---

## 5. Python methods and metrics

### 5.1 Deterministic held-out design

- Model: provisional double-precision discrete-time model.
- Duration and timestep: 1.0 s and 0.0001 s (10,001 grid points, 10,000 state updates).
- Training stimuli: dark, step up/down, pulse, repeated pulses, ramp, periodic, abrupt transitions, steady state.
- Held-out stimuli: early step, late/down step, double pulse, triangular ramp, rapid pulse train, chirped illumination.
- Both adaptive candidates and their full-update references use identical model parameters, initial state, samples, and grid.
- A maximum **observed** voltage error target of 10 μV was used to choose parameters on training stimuli only. The held-out set did not choose policy parameters.
- The recorded maximum error compares post-initial voltage states (`V[1:]`). Applied-current error aligns current sample `i` with the state transition from sample `i` to `i+1` (`I[0:-1]`).
- RMS/MAE aggregate the corresponding observed errors. Exceedances use strict `abs(error) > threshold`.

There are six current terms and 10,001 Python model grid samples, so the full-update function-evaluation denominator is 60,006 per stimulus. This gives 540,054 evaluations for nine training stimuli and 360,036 for six held-out stimuli. This denominator includes the terminal grid sample as documented in experiment metadata.

### 5.2 Metric definitions

For aligned baseline and candidate voltage arrays `V_b[k]` and `V_a[k]`:

`e_V[k] = V_a[k] - V_b[k]`

`max_abs_voltage_error = max_k(abs(e_V[k]))`

`RMS_voltage_error = sqrt(sum_k(e_V[k]^2) / N)`

`MAE_voltage_error = sum_k(abs(e_V[k])) / N`

For current comparisons, apply the same definitions to the current values used by each corresponding state transition. For Python evaluation counts:

`call_reduction_percent = 100 * (1 - adaptive_current_function_calls / full_update_current_function_calls)`

These error quantities are observations on finite traces. The voltage error is not the budget proxy and is not a bound. Python call reduction is not a hardware activity or power metric.

### 5.3 Training and held-out selected-policy results

| Policy selected using training stimuli | Split | Worst observed max voltage error | Pooled RMS | Pooled MAE | Samples over 10 / 50 / 100 μV | Python current evaluations | Reduction |
|---|---|---:|---:|---:|---:|---:|---:|
| Per-current sensitivity, threshold `1e-14 A`, max interval 16 | Training (9) | 1.39259 μV (abrupt transitions) | 0.16298 μV | 0.07661 μV | 0 / 0 / 0 | 228,302 / 540,054 | 57.73% |
| Accumulated voltage proxy, budget `1e-6 V`, max interval 16 | Training (9) | 7.21549 μV (periodic) | 0.34871 μV | 0.09583 μV | 0 / 0 / 0 | 257,166 / 540,054 | 52.38% |
| Per-current sensitivity, threshold `1e-14 A`, max interval 16 | Held-out (6) | 1.48659 μV (triangle ramp) | 0.21603 μV | 0.08455 μV | 0 / 0 / 0 | 222,934 / 360,036 | 38.08% |
| Accumulated voltage proxy, budget `1e-6 V`, max interval 16 | Held-out (6) | 6.97410 μV (chirped light) | 0.31175 μV | 0.04978 μV | 0 / 0 / 0 | 241,224 / 360,036 | 33.00% |

On the finite held-out set, the sensitivity policy had lower maximum and RMS voltage error and a higher Python-call reduction; the proxy policy had lower MAE. Both met the training-selected observed-error threshold on these traces. No conclusion about unseen inputs follows.

### 5.4 Earlier empirical-budget sweep

The 54-case sweep used nine stimuli, three accumulated-proxy thresholds, and two maximum ages. All cases completed under the Python model’s runaway guard. Across the pooled 90,000 post-initial voltage samples per configuration:

| Proxy trigger | Max age | Maximum observed voltage error | Largest per-stimulus RMS error | Samples over 10 / 50 / 100 μV | Weighted Python function-call reduction |
|---:|---:|---:|---:|---:|---:|
| 1 μV | 4 | 7.21549 μV | 0.93708 μV | 0 / 0 / 0 | 48.96% |
| 1 μV | 16 | 7.21549 μV | 0.93708 μV | 0 / 0 / 0 | 52.38% |
| 10 μV | 4 | 51.50652 μV | 20.82617 μV | 5,780 / 22 / 0 | 61.68% |
| 10 μV | 16 | 51.57906 μV | 20.95332 μV | 5,903 / 23 / 0 | 65.72% |
| 100 μV | 4 | 301.89304 μV | 80.27372 μV | 34,386 / 9,277 / 3,598 | 73.99% |
| 100 μV | 16 | 308.30578 μV | 110.21437 μV | 40,283 / 11,344 / 5,637 | 79.15% |

The 10 μV configured proxy does not bound the observed trajectory error. Its maximum was about 51.58 μV in this sweep. This is direct evidence that the proxy setting must not be presented as a guaranteed voltage tolerance.

### 5.5 Earlier Python screening

The broader prior adaptive screening found periodic refresh unstable by the model’s runaway guard for seven of nine stimuli. The threshold policy completed all nine and observed a maximum voltage error of 0.07520 mV; function-call reductions ranged from 0 to 92.09%. The 10 μV empirical-budget configuration completed all nine, observed 0.05158 mV maximum error, and reduced function calls by 37.68–89.44%. These settings/results are earlier screening evidence and are distinct from the training-selected held-out experiment above.

---

## 6. RTL evidence, comparison traces, and implementation concerns

### 6.1 User-reported adaptive comparison

The project records user-supplied XSim console outcomes for an earlier adaptive RTL revision: scheduler PASS, error-budget PASS after a failing initial test was corrected, adaptive initialization/refresh/idle-hold PASS, edge-case PASS, and comparison trace completion for four scenarios × 40 cycles. The user also supplied metrics from a 160-row, 65-column CSV:

| Scenario | Refreshes / 40 accepted cycles | Nominal refresh-count reduction | Max observed voltage error | RMS voltage error | Max applied total-current difference |
|---|---:|---:|---:|---:|---:|
| Dark | 18 | 55.00% | 0.178403616 mV | 0.105293143 mV | 30.8087424 pA |
| Step light | 29 | 27.50% | 0.127412140 mV | 0.070779280 mV | 30.8087424 pA |
| Pulse light | 32 | 20.00% | 0.186290324 mV | 0.084085860 mV | 30.8087424 pA |
| Alternating light | 40 | 0.00% | 0 mV | 0 mV | 0 pA |

The nominal count reduction denominator was `6 × accepted samples`, compared with `6 × refreshes`; it measures refresh-triggered current update bookkeeping. It does not establish logic toggles or power savings. Alternating light refreshed every sample because every input transition requires a refresh under the current policy; therefore the zero difference and zero nominal reduction are consistent with full refresh on all accepted samples.

These are **user-reported results from an earlier run/source revision**. In subsequent work, the comparison testbench was updated to clarify pre-edge/recomputed/applied and post-edge fields, and the adaptive RTL gained operand isolation and counter boundary changes. The latest modified RTL and revised testbenches have not been compiled or simulated by the assistant. Do not present the older trace as validation of those edits.

### 6.2 Baseline trace vectors and authored tests

Eight 40-cycle fixed-point baseline CSV vectors are available for dark, step, pulse, alternating light, held-out step, double pulse, ramp, and rapid-pulse inputs. The baseline trace testbench was updated to read them. Adaptive tests were extended for first refresh, invalid-cycle hold, and operand-isolated input snapshots. The comparison bench captures scenario/cycle/input/valid identifiers, pre-edge current values, applied current values, counters/refresh information, and post-edge state values.

The current testbench source still requires a manual Vivado review/run. In particular, confirm CSV paths and field counts, that output data is generated, and that baseline/adaptive values refer to identical accepted sample indices and input samples. No simulation of the newly edited benches is claimed.

### 6.3 Historical user-reported Vivado area/power reports

The following values are user-reported screenshots from earlier runs; raw reports, constraints, part, implementation stage, activity files, and exact source revisions were not independently verified. They predate the latest operand-isolation edits.

| Metric | Baseline | Adaptive | Interpretation |
|---|---:|---:|---|
| LUTs (latest screenshot) | 16,348 | 28,226 | Adaptive exceeds the stated 20,800 LUT capacity; baseline has 4,452 LUT headroom. |
| Flip-flops | 283 | 701 | Adaptive uses more reported registers. |
| DSP blocks | 71 | 71 | No reported difference. |
| Bonded I/O | 125 | 125 | No reported difference. |
| Estimated total power | 0.863 W | 0.899 W | Low-confidence estimate; not measured physical power. |
| Estimated dynamic power | 0.791 W | 0.827 W | Low-confidence estimate; not an activity-matched proof. |

An earlier user-provided baseline figure of 27,673 LUTs conflicts with the later 16,348-LUT baseline. This discrepancy is unresolved; it may reflect different top-level parameters, report stages, or settings. A prior hierarchical report attributed 13,995 LUTs to `calcium_dynamics`; the three 40-bit multiply operations and wide intermediate were identified as likely area contributors, but no causal conclusion or optimized Vivado result has been established. These reports do not support a claim of adaptive area or power benefit; the latest screenshot instead raises area-feasibility concerns.

---

## 7. Verification status

### 7.1 Python verification performed

- Final full Python suite after the latest experiment/test changes: **52 passed**.
- Held-out experiment rerun and artifacts regenerated.
- Generated result CSV checked: **192 rows, 17 columns** (180 training and 12 held-out policy/stimulus rows).
- Generated reference vectors checked: **eight files**, each with 40 data rows and 23 fields.
- Python function-evaluation counts are checked against the refresh mask in the experiment runner.
- No HDL tool was invoked by the assistant.

The 52-test result validates Python code covered by those tests. It does not compile or simulate Verilog.

### 7.2 Historical user-run HDL outcomes (not current-edit validation)

Earlier user-supplied messages reported PASS for fixed-point math, scheduler, phototransduction, ionic currents, baseline integration, dark/step/pulse trace comparison, and the adaptive scheduler/budget/edge/adaptive/comparison test set. These are attributed as user-reported outcomes and apply only to the tested sources at that time. The latest source edits require a fresh run.

### 7.3 Tests still required manually in Vivado

Follow [`RTL_MANUAL_VERIFICATION.md`](ISCAS_2027_Vivado.srcs/ISCAS%202027/RTL_MANUAL_VERIFICATION.md). At minimum:

1. Run the unit benches for fixed-point arithmetic, phototransduction, and all six currents.
2. Run the baseline integrated bench and all eight baseline trace vectors.
3. Run scheduler and error-budget benches, including reset, first-valid sample, invalid cycles, max-age boundaries, light transitions, and saturation/clamping behavior.
4. Run adaptive integration and edge-case benches; inspect the operand inputs for held values between refreshes.
5. Run the updated paired comparison bench for four scenarios × 40 cycles; independently validate CSV columns, cycles, valid samples, inputs, and pre-/post-edge alignment.
6. Save complete XSim transcripts and generated CSVs. Do not change expected data to make a failure disappear.
7. Repeat comparison for the three matched configurations: baseline, adaptive bypassing isolation, adaptive with isolation.
8. If evaluating hardware benefit, run matched synthesis/implementation for identical part, constraints, source set, clock, and tool settings; save LUT/FF/DSP, timing, and activity-based power reports. Prefer matched SAIF/VCD windows from identical stimuli. Nominal refresh counts and vectorless low-confidence power reports are insufficient.

The exact RTL top, parameter values, source lists, generated CSV paths, and outputs must be recorded with every run. The existing Vivado project file was previously reported to have empty source filesets; confirm all sources are registered before simulation or synthesis.

---

## 8. Novelty and claims policy

### What may be stated now

- The project implements and evaluates heuristic selective-current policies in a provisional Python model.
- In one finite train/held-out comparison, a selected per-current sensitivity policy met a 10 μV maximum-observed-error criterion on the tested traces while reducing Python current-function calls.
- The RTL contains a group-refresh current cache and a configurable operand-isolation experiment, verified only by static source inspection in the latest edits.
- The fixed-point baseline/reference uses signed Q16.24 and serves as the engineering full-update comparison.

### What may not be stated now

- “Guaranteed error below 10 μV” or “voltage-error bound”: false; observed errors can exceed the proxy threshold, and no bound is proved.
- “Hardware current computations reduced by X%,” “switching reduced,” or “power saved”: not measured. Python function calls and refresh counts are not FPGA activity or power.
- “The current RTL achieves the held-out Python sensitivity result”: the RTL does not implement that Python policy.
- “Validated biological photoreceptor,” “reproduces the paper,” or “paper-equivalent RTL”: unsupported; provisional model differs materially and the separate paper transcription has unresolved inputs/conventions.
- “Fits the FPGA” or “improves area”: historical user reports show adaptive LUT over-capacity and no current matched synthesis report exists.
- “Novel” or “first”: no systematic literature review and no novelty comparison has been completed.

### Evidence needed to elevate claims

1. Resolve source model/input definitions and compare against biological or published numerical traces.
2. Specify stimulus amplitudes/timings and a preregistered voltage metric/threshold.
3. Implement the selected scheduler in RTL or evaluate the existing global scheduler independently; do not conflate them.
4. Run broad, reproducible RTL tests with Python/RTL sample alignment and arithmetic-boundary coverage.
5. Measure switching/activity with matched SAIF/VCD or another justified activity methodology.
6. Compare area and timing on identical synthesis/implementation settings; reconcile the two baseline LUT counts.
7. Perform a systematic literature review before making a novelty claim.

---

## 9. Limitations, risks, and open questions

### Scientific/model limitations

- The baseline is provisional and materially differs from Appendix B.
- Biological validation is blocked by undefined `J_hv(t)`, uncertain B.2/B.9 calcium coupling, and unspecified `E_Ca` logarithm base.
- Calcium-current concentration coupling in the provisional RTL is omitted/quantized away at the reviewed scale; its general biological/numerical impact is unresolved.
- No externally measured or paper-provided trace has been used for biological fitting or validation.

### Algorithmic limitations

- Sensitivity and accumulated-budget triggers are heuristic estimates, not conservative bounds.
- The held-out stimuli are deterministic and finite; they do not establish robustness to all amplitudes, timings, parameter variation, noise, initial states, or adversarial traces.
- The selected Python sensitivity policy is absent from RTL; its accuracy/call-count results cannot be transferred to the RTL.
- The existing group scheduler may refresh every sample for frequent light transitions, eliminating nominal reuse in such conditions.

### RTL/hardware limitations

- Latest operand-isolation RTL and revised benches have not been simulated or synthesized by the assistant.
- Combinational current equations remain present; operand isolation is intended to stabilize their operands, but net internal switching depends on mapping and implementation.
- Added muxes/snapshots may worsen LUT, FF, timing, routing, or power.
- Q16.24 truncation/wrap and corner-case behavior need targeted test coverage.
- Historical user-reported adaptive LUT use exceeds the stated capacity; latest modified source must be remeasured.
- Historical power reports are low-confidence, and baseline LUT reports conflict.

---

## 10. Reproducibility map and useful files

Paths in the following tables are relative to `ISCAS_2027_Vivado.srcs/ISCAS 2027/` unless a path begins with `sources_1/` or `sim_1/`, which is relative to `ISCAS_2027_Vivado.srcs/`.

### Python models and experiments

| File/directory | Role |
|---|---|
| `photoreceptor_parameters.py`, `photoreceptor_reference.py`, `discrete_time_model.py` | Provisional model, parameters, and full/selective update policies. |
| `run_budget_sweep.py` | 54-case empirical-budget/maximum-age sweep; applied-current error alignment is documented in the runner. |
| `results/metrics/area_followup_python/empirical_budget_sweep.csv` | Detailed 54-case sweep data. |
| `run_heldout_scheduler_experiments.py` | Training-only selection and deterministic held-out evaluation. |
| `test_heldout_scheduler_experiments.py` | Tests for held-out experiment behavior, deterministic inputs, call counts, and metric alignment. |
| `results/metrics/heldout_scheduler/heldout_scheduler_results.csv` | Per-policy, per-stimulus results (192 rows total). |
| `results/metrics/heldout_scheduler/heldout_scheduler_metadata.json` | Stimulus definitions, parameters, denominators, alignment, and selection metadata. |
| `results/metrics/heldout_scheduler/heldout_scheduler_tradeoff.png` | Generated visualization of held-out scheduler outcomes. |
| `export_rtl_reference_vectors.py` | Exports baseline trace vectors in signed raw Q16.24. |
| `results/rtl_reference_vectors/` | Eight 40-cycle baseline vectors used by the trace testbench. |
| `baseline_fixed_point.py` | Cycle-level fixed-point baseline reference. |
| `adaptive_trace_metrics.py`, `test_adaptive_trace_metrics.py` | Paired RTL trace parser/metrics and parser tests. |

### RTL, verification, and project reporting

| File | Role |
|---|---|
| `sources_1/new/photoreceptor_baseline.v` | Preserved full-update baseline reference. |
| `sources_1/new/photoreceptor_adaptive.v` | Group-refresh adaptive candidate with optional operand isolation. |
| `sources_1/new/current_update_scheduler.v`, `voltage_error_budget.v` | Refresh trigger and heuristic budget modules. |
| `sources_1/new/photoreceptor_top.v` | Parameterized baseline/adaptive selection. |
| `sim_1/new/tb_photoreceptor_comparison.v` | Four-scenario paired trace capture; latest changed version needs Vivado validation. |
| `sim_1/new/tb_photoreceptor_baseline_trace.v` | CSV-driven baseline comparison across eight vectors. |
| `sim_1/new/tb_photoreceptor_adaptive.v` | Refresh, reset/invalid, and operand-isolation checks. |
| `RTL_MANUAL_VERIFICATION.md` | Manual Vivado sequence and matched implementation instructions. |

### Scientific audit and status

- `PAPER_EQUATION_AUDIT.md`: source equation transcription, units/parameter discussion, discrepancy audit, and biological blockers.
- `PROJECT_STATUS.md`: evolving phase history and validation records.
- `RTL_REVIEW.md`: module-level RTL review and testbench guidance.
- `RESEARCH_QUESTION.md`: hypothesis and falsifiable success criteria.
- `ALGORITHM.md`: scheduler architecture, equations, and interpretation.
- `IMPLEMENTATION_RESULTS.md`: historical user-reported Vivado results and Python studies.
- `FINAL_RESEARCH_ASSESSMENT.md`: concise evidence assessment for the held-out/operand-isolation work.

### Re-running the Python work

From the repository root, with the project Python dependencies installed:

```powershell
cd "ISCAS_2027_Vivado.srcs/ISCAS 2027"
python -m pytest -q
python run_heldout_scheduler_experiments.py
python export_rtl_reference_vectors.py
```

The documented final observed Python test result was `52 passed`. Running the experiment/vector scripts overwrites their generated output artifacts in their named result directories. These commands do not run HDL tools. Use the exact Python environment and preserve generated artifacts/revision hashes for publication.

---

## 11. Suggested manuscript structure and defensible message

1. **Introduction:** Motivate adaptive evaluation in digital photoreceptor models; separate motivation from claimed results; cite and distinguish the FinFET source article.
2. **Model and scope:** Define which model is evaluated (provisional engineering model), its units, equations, fixed-point format where relevant, and known differences from Appendix B.
3. **Methods:** Define full-update reference, candidate trigger equations, cached states, reset/valid semantics, stimuli, training/held-out split, parameter-selection rule, and metric alignment.
4. **Software results:** Report the selected Python sensitivity and accumulated-proxy comparisons, the 54-case sweep, and the failures/threshold exceedances, with raw tables and scripts.
5. **RTL architecture:** Explain group refresh, operand isolation, cache/reset/invalid semantics, and configuration variants. Label current implementation as static-review-only until new simulation evidence exists.
6. **Hardware evaluation:** Add only after fresh Vivado runs: matched resource/timing/activity results, reproducible tool/part/constraint/activity settings, and raw reports. Do not use refresh counters as the switching metric.
7. **Discussion:** Explain why the heuristic is not an error bound, why Python/RTL results are not interchangeable, and why model/paper ambiguities block biological conclusions.
8. **Conclusion:** State only what the completed evidence directly supports; identify source-model validation, RTL verification, activity measurement, and literature review as open work.

**Defensible present conclusion:** On a provisional software model, a training-selected per-current sensitivity heuristic showed favorable finite-trace voltage-error and Python function-call outcomes relative to an accumulated-proxy policy. A separate RTL operand-isolation experiment has been written but has not yet been validated in the current source revision or measured for hardware activity, area, timing, or power. This is preliminary engineering evidence, not a biological validation or established novelty claim.
