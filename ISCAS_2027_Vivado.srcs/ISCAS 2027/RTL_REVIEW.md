# RTL review and manual Vivado test guide

## Verification boundary

The assistant did not run any HDL compiler, Vivado, simulation, waveform inspection, or synthesis. The user has reported PASS results for the unit/current/baseline and CSV trace benches below; those results cover only their programmed assertions and stated scenarios. They do not establish biological fidelity or agreement with Shah et al.'s Appendix B.

The user confirmed these standalone Vivado results:

| Testbench | Result | Reported finish time | What it establishes |
|---|---|---:|---|
| `tb_fixed_point_math.v` | PASS | `$finish called at time : 3 ns` | The standalone arithmetic/saturation vectors passed. |
| `tb_current_update_scheduler.v` (previous interface) | PASS, historical | `$finish called at time : 86 ns` | This user-reported run predates the Phase 5 interface/behavior rewrite and does not validate the current scheduler or replacement bench. |
| `tb_phototransduction.v` | PASS | `$finish` at 4 ns | The light-to-photocurrent vectors passed. |
| `tb_ionic_currents.v` | PASS | `$finish` at 2 ns | The ionic-current vectors and zero-denominator guards passed. |
| `tb_photoreceptor_baseline.v` | PASS | `$finish` at 26 ns | The user-reported baseline assertions completed for reset, initial dark currents, one dark update, one light update, state movement, and idle hold. |
| `tb_photoreceptor_baseline_trace.v` | PASS | `$finish` at 1206 ns | User-reported XSim output: all 40 post-edge rows matched for dark, step, and pulse. |

These are user-reported Vivado/XSim outcomes, not runs performed or independently inspected by the assistant. The trace test reports exact raw-value matches for the generated 40-cycle scenarios at the default configuration; broader stimulus/parameter coverage and biological-model fidelity remain unverified.

## Paper-equation audit (Appendix B)

The attached Shah et al. paper's Appendix B has now been inspected from the
supplied enlarged images (printed pp. 8–10). The full equation transcription,
parameter/initial-condition table, and component-by-component Python/RTL
comparison are in [PAPER_EQUATION_AUDIT.md](./PAPER_EQUATION_AUDIT.md).
The baseline does **not** implement that source model: it substitutes a
direct normalized-light current, generic LUT gate dynamics, simplified
calcium states, and provisional conductance/reversal/initial values. The
paper explicitly includes `I_ex`/`I_ex2` in its membrane and calcium equations;
the baseline lacks those currents and does not use its calcium-current input
in the concentration update.

The LUT and Q16.24 truncation/wrap are engineering approximations, not
Appendix B equations. Their existing Vivado/Python trace agreement only
confirms agreement with this RTL baseline for the three reported test vectors.
It cannot establish source-paper fidelity.

## Separate float64 Appendix B transcription

`paper_biological_model.py` and `paper_biological_parameters.py` implement the
legible B.1–B.9 equations and initial values separately from the provisional
RTL/reference. The Python model includes the complete nine-current membrane
sum, the full phototransduction state set, the Ih Markov states, distinct
channel kinetics, and shell/free calcium buffers and current contributions.
No RTL or passing fixed-point reference was changed.

The transcription requires the caller to provide `J_hv(t)` and choose the
unresolved natural/base-10 logarithm interpretation in `E_Ca`. It does not
merge the B.2 calcium states with the B.9 shell/free compartments. Seven
focused Python tests passed, and a 5 ms synthetic zero-input DOP853
convergence check was recorded for both logarithm choices. These are
transcription/numerical checks only. The selected input is not specified by
the paper, the logarithm ambiguity remains, and the article does not provide
machine-readable reference traces or error bounds; therefore no biological
response validation is claimed. See
[`PAPER_EQUATION_AUDIT.md`](./PAPER_EQUATION_AUDIT.md) and
[`PROJECT_STATUS.md`](./PROJECT_STATUS.md).

## Static review findings and changes

All modules below use signed 40-bit Q16.24 words by default. Engineering units are mV, nS, pA, mM, ms, and normalized light. In these units, `nS * mV = pA` and `pA / pF = mV / ms`. Constants currently come from the provisional Python parameter object and are not paper-verified.

| Module | Current behavior / review note |
|---|---|
| `phototransduction.v` | Combinational `I_photo = 2000 pA * light`; removed the former clock/reset/voltage ports. |
| `ih_current.v` | Signed `g*m*(V-E)` arithmetic with Q rescaling at each multiplication. |
| `kv_current.v` | Signed `g*m^3*(V-E)` arithmetic. |
| `ca_current.v` | Signed `g*m^3*(V-E)` arithmetic. |
| `clca_current.v` | Uses `Ca_i/(Ca_i+K)` and guards a zero denominator with a zero output and status flag. |
| `kca_current.v` | Uses `Ca_i/(Ca_i+K)` and guards a zero denominator with a zero output and status flag. |
| `leakage_current.v` | Signed `g*(V-E)` arithmetic. |
| `sigmoid_lut.v`, `gate_update.v` | The gate model uses a nearest-half-step, 33-entry logistic LUT over normalized input [-8, 8], followed by explicit-Euler relaxation. This approximates, rather than exactly reproduces, the Python exponential sigmoid. |
| `calcium_dynamics.v` | Explicit-Euler recovery and transfer for the provisional three calcium states. The `alpha_ca * I_ca` concentration increment is smaller than one Q16.24 mM LSB at the tested operating scale and is currently omitted; this is a known quantization approximation, not paper-derived behavior. |
| `membrane_voltage.v` | Explicit-Euler `V_next = V - (I_total/C_m)*dt`, with a divide-by-zero guard. |
| `photoreceptor_baseline.v` | Integrates photocurrent, six ionic currents, five gates, three calcium states, membrane voltage, and valid timing. Current equations are continuously combinational; state updates are gated by `valid_in`. It is not the adaptive design and exposes states/currents for waveform inspection. |
| `photoreceptor_top.v` | Selects baseline at `ADAPTIVE_ENABLE=0`, adaptive at nonzero; source default is `ADAPTIVE_ENABLE=1`, so baseline runs must override explicitly. |

The baseline uses one state ordering per accepted clock: combinational currents are calculated from the pre-edge voltage/gates/calcium and current light; at the active edge membrane voltage, gate states, and calcium states are updated using those pre-edge quantities. `valid_out` is a one-cycle registered indication of `valid_in`; state holds when `valid_in` is low. Asynchronous active-high reset restores the provisional initial state.

Known limitations before making research claims:

- The sigmoid LUT introduces a discrete approximation not used by the current floating-point Python equation.
- Q16.24 truncation occurs at each multiplication/division stage; there is no saturation/overflow reporting on state/current arithmetic.
- Light has no clipping/validity range; negative normalized light is accepted arithmetically.
- The calcium-current concentration term is neglected at this scale as described above.
- The user-reported trace-test PASS indicates that RTL outputs matched the bit-accurate Python CSVs for the generated 40-cycle dark, step, and pulse traces. Broader stimulus, parameter, and arithmetic-boundary coverage remains incomplete.
- Raw waveform values were not independently inspected by the assistant; the user's XSim console transcript is the evidence for these comparisons.
- `photoreceptor_top.v` remains the full-update baseline wrapper. The adaptive candidate is selected explicitly as `photoreceptor_adaptive`; the reported baseline source set is not switched implicitly.
- The existing `.xpr` was previously found with empty design/simulation file lists and `TopModule=test`; confirm/add sources in the correct Vivado filesets before simulation.

## Testbench sequence

Run one testbench at a time, with the listed dependencies in Design Sources and the testbench in Simulation Sources. Expected PASS lines below are the newly authored assertions' success messages, not observed simulator results.

### 1. `tb_phototransduction.v`

Design source: `phototransduction.v`.

Checks four combinational Q16.24 vectors: zero light, unit light -> 2000 pA, half light -> 1000 pA, and negative half light -> -1000 pA. No clock or valid handshake is present in this primitive.

Expected success text: `PASS tb_phototransduction: Q16.24 light-to-pA vectors`.
Inspect `light_q` and `i_photo_q`; output should change without a clock edge and match the signed integer reference words in the test.

### 2. `tb_ionic_currents.v`

Design sources: `ih_current.v`, `kv_current.v`, `ca_current.v`, `clca_current.v`, `kca_current.v`, and `leakage_current.v`.

Checks six signed Q16.24 currents at the initial Python state (`V=-60 mV`, initial gate/calcium states), plus zero-denominator behavior of both calcium-activated channels. The expected raw integers are independently evaluated from the listed conductance/reversal/gate equations with Q16.24 truncation at each RTL multiplication/division stage; they are engineering-unit results, not paper measurements.

Expected success text: `PASS tb_ionic_currents: six Q16.24 golden vectors and zero-denominator guards`.
Inspect all `i_*` outputs, `invalid_denominator` flags, and the zeroed outputs in the invalid-denominator case.

### 3. `tb_photoreceptor_baseline.v`

Design sources: `phototransduction.v`, `ih_current.v`, `kv_current.v`, `ca_current.v`, `clca_current.v`, `kca_current.v`, `leakage_current.v`, `sigmoid_lut.v`, `gate_update.v`, `calcium_dynamics.v`, `membrane_voltage.v`, and `photoreceptor_baseline.v`.

Checks asynchronous reset values; initial dark photocurrent and all six initial ionic-current reference words; exact first dark Euler voltage result (`-958630687` raw Q16.24, about -57.13884 mV); gate/calcium state movement; response to one unit of light; valid pulse timing; and voltage hold when `valid_in` is low.

Expected success text: `PASS tb_photoreceptor_baseline: reset, dark golden step, light response and valid timing`.
Inspect `v_mem_q`, `i_photo_q`, each `i_*_q`, `i_total_q`, `m_*_q_out`, `ca_i_q/ca_s_q/ca_f_q`, `valid_in`, `valid_out`, and `divide_by_zero`. During dark input the first step should move voltage upward from -60 mV because the initial summed ionic current is negative. Applying unit light adds 2000 pA; under this provisional current sign convention, the next voltage should move downward relative to the dark-step value. Gate and calcium values update on valid edges and hold while invalid.

If any test fails, share the complete Vivado compile log and simulator console output, the failing vector/value, and (for the baseline) waveforms around reset and the first two active clock edges. A PASS on the current short baseline scenario is not broad trajectory or biological-model validation.

## Bit-accurate Python trace reference

`baseline_fixed_point.py` mirrors the default 40-bit Q16.24 RTL operation order and `sigmoid_lut.v` table. `export_baseline_vectors.py` writes 40-cycle dark, step, and pulse CSVs under `results/rtl_reference_vectors/`; their `_q` fields are signed raw integers sampled after each active edge. Follow `RTL_FIXED_POINT_REFERENCE.md` for exact input timing, output-port column mapping, and comparison instructions.

`tb_photoreceptor_baseline_trace.v` is the Vivado trace-comparison bench. Add it to Simulation Sources and set it as the simulation top; add the baseline dependency modules from the testbench section above to Design Sources. It reads the three CSVs from the documented absolute project path, drives their inputs, and compares every exposed baseline output at each settled post-edge cycle. If you use a different project root, update the paths near the end of the testbench.

The user-reported completed XSim transcript shows all 40 rows matched for dark, step, and pulse, followed by the final PASS and `$finish` at 1206 ns. This confirms that XSim accepted and compared the signed-decimal CSV values in that run. It is not evidence for other parameter settings or biological fidelity.

Six Python-only tests cover the arithmetic boundary semantics, LUT, reset, valid/idle behavior, deterministic trajectories, and CSV layout. These tests do not execute HDL and do not demonstrate Python-to-Vivado agreement. The reference deliberately retains the RTL's omitted calcium-current contribution and other listed approximations.

## Phase 5 adaptive candidate — static review, simulator status pending

### User-run XSim update (2026-10-10)

The user reported PASS for the rewritten `tb_current_update_scheduler.v`
(finish at 116 ns), `tb_photoreceptor_adaptive.v` (36 ns), and
`tb_edge_cases.v` (26 ns), and the corrected `tb_voltage_error_budget.v`
(96 ns). The comparison bench then completed with
`PASS comparison trace captured: 4 scenarios x 40 cycles` at 1680 ns after
the user ran it for 2000 ns. These are user-reported XSim results, not runs
performed by the assistant. The CSV is now available at
`results/metrics/adaptive_comparison_trace.csv` (160 data rows, 38 columns),
and the metrics script has been run against it. No missed light-transition
refreshes, interval violations, or recomputation-counter mismatches were
reported for these scenarios.

| Scenario | Refreshes / 40 | Six-current evaluations / 240 | Avoided evaluations | Max |V| error (mV) | RMS |V| error (mV) | Max |I_total| error (pA) |
|---|---:|---:|---:|---:|---:|---:|
| Dark | 18 | 108 | 55.00% | 0.178404 | 0.105293 | 30.80874 |
| Step light | 29 | 174 | 27.50% | 0.127412 | 0.070779 | 30.80874 |
| Pulse light | 32 | 192 | 20.00% | 0.186290 | 0.084086 | 30.80874 |
| Alternating light | 40 | 240 | 0.00% | 0 | 0 | 0 |

The largest individual ionic-current discrepancy was about 21.1513 pA
(`I_h`, dark); the leak-current maximum was 19.5944 pA. The largest gate
discrepancy was about `4.344e-4` (`m_ca`); calcium-state differences were
zero in these traces. Alternating light refreshed every sample and exactly
matched baseline. These results apply only to this 40-cycle-per-scenario
test, are not acceptance thresholds, and do not establish biological
correctness.

The baseline module is unchanged and remains the full-update reference. The adaptive module is a separate 40-bit Q16.24 datapath using the same combinational current, gate, calcium, and membrane modules. It caches all six ionic currents together (`I_h`, `I_Kv`, `I_Ca`, `I_ClCa`, `I_KCa`, and leak); the photocurrent is recomputed combinationally each sample. Every valid edge still updates membrane voltage, the five gate states, and three calcium states. Before the latest follow-up, the adaptive current-module operands followed live states continuously. The current adaptive source adds default-on operand isolation: current modules remain combinational, but their voltage/gate/calcium inputs are held at last-refresh snapshots between refreshes. This can suppress input-driven transitions, but its effect on internal switching is unmeasured. Refresh-derived counts do not establish hardware activity, area, or power reduction.

Refresh conditions in the current candidate:

1. First accepted sample after asynchronous reset, before any cache can be selected.
2. Any light difference from the light value at the last ionic-current refresh (threshold default is zero).
3. Absolute membrane-voltage excursion from its last-refresh snapshot at or above 1 mV (Q16.24 raw `16777216` by default).
4. Projected error-proxy budget reaching 0.1 mV (raw `1677722` default).
5. Maximum age of 8 accepted samples (configurable; 16-bit age counter, so use 1–65535).
6. Explicit `force_refresh` input at the scheduler boundary. The integrated adaptive module currently ties this override low; its other mandatory triggers remain active. `photoreceptor_top` selects the adaptive module when `ADAPTIVE_ENABLE=1`; inspected RTL source default is 1, so baseline mode must be selected explicitly with `ADAPTIVE_ENABLE=0`.

The scheduler evaluates refresh combinationally for the current valid sample. It samples `refresh_all` in the same active edge that captures the six current values and updates membrane/gate/calcium state from pre-edge values, following baseline sequencing. On invalid samples, `valid_out` deasserts and state, cache, age, and error budget hold; no refresh event is advertised. Reset clears the scheduler initialization flag, cache-valid flag, age, budget, and recomputation count. Current outputs select live values while the cache is invalid, so zero-reset cache registers are never consumed for an accepted state update.

The error accumulator saturates at the unsigned word maximum on overflow and clears on refresh. Its input estimate is `abs(V[n]-V[n-1]) >> 4`, interpreted as an empirical scaled voltage-step proxy. It is not a current-error estimate, has no sensitivity derivation, and does not provide a guaranteed voltage-error bound. The voltage threshold, light change, and max-age triggers are independent of this proxy. Setting `MAX_REFRESH_INTERVAL=1` on `photoreceptor_adaptive` or `photoreceptor_top` forces a full ionic refresh on every accepted sample.

### New manual Vivado sequence

Do not treat the historical `tb_current_update_scheduler.v` PASS above as evidence for this rewrite. Run each of these independently; the assistant did not invoke any HDL tool:

1. `tb_current_update_scheduler.v` — initialization refresh, idle no-trigger behavior, age boundary, voltage/light triggers, budget/force triggers, and invalid-cycle response.
2. `tb_voltage_error_budget.v` — nonnegative accumulation, projected threshold crossing one sample before the stored sum reaches the limit, clear, saturation, and valid timing.
3. `tb_photoreceptor_adaptive.v` — first accepted sample cache initialization, invalid-cycle state hold, light transition refresh, and recomputation count.
4. `tb_edge_cases.v` — known-value and valid checks under dark and unit-light inputs.
5. `tb_photoreceptor_comparison.v` — dark, step, pulse, and alternating-light stimulus; writes `ISCAS 2027/results/metrics/adaptive_comparison_trace.csv` and checks light and maximum-age refresh conditions plus both `photoreceptor_top` modes. Run for at least 2000 ns or use `run -all`; 1000 ns ends before all four scenarios and the completion summary.

For `tb_photoreceptor_adaptive.v`, add the baseline RTL dependencies (`phototransduction.v`, six current modules, `sigmoid_lut.v`, `gate_update.v`, `calcium_dynamics.v`, and `membrane_voltage.v`), plus `current_update_scheduler.v`, `voltage_error_budget.v`, and `photoreceptor_adaptive.v`. The comparison bench also needs `photoreceptor_baseline.v` and `photoreceptor_top.v` to verify both top selections. The unit scheduler and budget benches need only their respective design module. Confirm all sources in the Vivado project filesets; a prior static inspection found that the project file's source lists were empty.

After the comparison bench completes, process its CSV from the
`ISCAS 2027` Python folder with:

```text
python adaptive_trace_metrics.py results/metrics/adaptive_comparison_trace.csv
```

The previous trace format and metrics are historical and are not accepted by the hardened analyzer. Regenerate the CSV using the updated comparison bench. The new format stores one row per accepted sample, explicit scenario/cycle/valid fields, both input light values, pre-edge baseline currents, adaptive recomputation-path values and selected/applied currents, the currents and total currents applied to that voltage update, the pre-edge refresh decision, pre/post counters, and post-edge state values. Pre-edge values are written before the active edge; post-edge states/counters are appended after it. The testbench's baseline formula count is nominal bookkeeping; the adaptive recomputation counter is the RTL's refresh counter, not a hardware activity meter.

`adaptive_trace_metrics.py` requires scenarios 0–3, exactly 40 in-order cycles per scenario, valid samples, identical light inputs, a complete numeric schema, internally consistent Q16.24 total-current sums, and consistent refresh/evaluation counters. It rejects missing or unexpected scenarios, row-count/cycle errors, malformed values, and misaligned inputs rather than sorting or silently skipping them. Voltage observed error uses `dV[n] = V_adapt_post[n] - V_base_post[n]`; `max_abs = max(abs(dV))/2^24` mV and `RMS = sqrt(sum(dV^2)/N)/2^24` mV. Applied total-current differences use the captured pre-edge currents actually used on that edge and the same equations, in pA. Signed 40-bit arithmetic is treated modulo 2^40 for total-current consistency. Current words are pA, voltage words mV, calcium words mM, gates dimensionless, and all are Q16.24; normalized light is separately logged as raw Q16.24.

The field `nominal_refresh_count_reduction_percent` is `100*(1 - (6*refreshes)/(6*accepted_samples))`. It describes refresh-derived accounting only, not switching/power. The RTL now operand-isolates current-module inputs between refreshes, but no mapped activity has been measured. Reported post-edge voltage differences are observed trajectory differences for these samples, **not** a guaranteed error bound. The error-budget accumulator remains a heuristic without a mathematical accuracy proof. The prior trace with the old header is superseded; the current CSV has the revised 65-column schema.

Python validation: `test_adaptive_trace_metrics.py` passed (8 tests). Initially, the CLI correctly rejected the old-format CSV. The user has now regenerated the CSV and run the analyzer; the current 160-row, 65-column trace passed strict validation. An independent local run reproduced the user's four reported summaries exactly. No HDL tool was run by the assistant, and the user's posted analyzer output alone does not establish that a comparison-bench PASS was reported.

| Scenario | Refreshes / 40 | Nominal refresh count / full-update reference | Nominal refresh-count reduction | Observed max voltage difference (mV) | Observed RMS voltage difference (mV) | Applied total-current max difference (pA) | Applied total-current RMS difference (pA) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dark | 18 | 108 / 240 | 55.00% | 0.178403616 | 0.105293143 | 30.8087424 | 7.41616706 |
| Step light | 29 | 174 / 240 | 27.50% | 0.127412140 | 0.0707792798 | 30.8087424 | 7.61766648 |
| Pulse light | 32 | 192 / 240 | 20.00% | 0.186290324 | 0.0840858599 | 30.8087424 | 8.29262706 |
| Alternating light | 40 | 240 / 240 | 0.00% | 0 | 0 | 0 | 0 |

These are values reported by the strict analyzer for the regenerated CSV, before the operand-isolation change. The voltage and applied-current differences are observed trajectory/sample metrics only. Nominal refresh-count reductions are counter-derived; operand isolation is intended to hold the six combinational current-module inputs between refreshes, but no hardware activity reduction or power saving has been measured.

### Final follow-up: held-out results, operand isolation, and updated vectors (2026-10-10)

Static RTL review confirms the current instances `u_ih`, `u_kv`, `u_ca`, `u_clca`, `u_kca`, and `u_leak` consume `current_*_q` mux outputs. With the default `OPERAND_ISOLATION_ENABLE=1`, the muxes choose live pre-edge state only when `refresh_all` is true; otherwise they select reset-initialized registers. Those registers update only inside the `valid_in && refresh_all` state path. The first valid sample is forced to refresh because the scheduler has not initialized. The six ionic equations, gate/calcium/membrane update equations, and baseline module were not changed. Photocurrent remains live.

`OPERAND_ISOLATION_ENABLE=0` bypasses the operand muxes for an adaptive-only A/B run. This does not change `ADAPTIVE_ENABLE=0` baseline selection. This structure suppresses changing operands in the combinational current paths between refreshes, but no simulation, switching-activity, resource, timing, or power result exists for it. The selected Python per-current sensitivity scheduler is not implemented in RTL; current RTL remains group-refresh with the older light/voltage/proxy/max-age triggers.

Static corner handling: the 16-bit refresh-age counter saturates; requested max intervals greater than 65,536 are clamped to 65,536. The 32-bit recomputation counter saturates rather than wrapping. The error accumulator retains unsigned saturating addition and clears on refresh; zero budget forces refresh. Counter and operand-isolation RTL changes still require manual HDL compile/simulation.

Python held-out comparison (10 μV training-only target): per-current sensitivity (`1e-14 A`, max age 16) gave held-out max/RMS/MAE errors 1.48659/0.21603/0.08455 μV, zero samples over 10/50/100 μV, and 38.08% Python-call reduction; the accumulated proxy (`1e-6 V`, max age 16) gave 6.97410/0.31175/0.04978 μV and 33.00% reduction. Both passed the finite selected observed-error target, but the selected sensitivity method is not represented by current RTL and these are not accuracy guarantees. Full detail and plot: `results/metrics/heldout_scheduler/`.

Added fixed-point vectors are `baseline_alternating_q16_24.csv`, `baseline_heldout_step_q16_24.csv`, `baseline_heldout_pulse_q16_24.csv`, `baseline_heldout_ramp_q16_24.csv`, and `baseline_heldout_rapid_q16_24.csv`. `tb_photoreceptor_baseline_trace.v` now includes them with the original dark/step/pulse vectors. The adaptive bench checks isolated operand hold across invalid/non-refresh cycles. The comparison CSV now calls the internal values `*_recompute_path_pre_q` rather than implying they are uncached live computations.

### Manual run order for current source state

1. `tb_fixed_point_math`
2. `tb_phototransduction`
3. `tb_ionic_currents`
4. `tb_photoreceptor_baseline`
5. `tb_photoreceptor_baseline_trace` — reads all eight Python-generated 40-cycle Q16.24 files under `results/rtl_reference_vectors/`.
6. `tb_current_update_scheduler`
7. `tb_voltage_error_budget`
8. `tb_photoreceptor_adaptive` — checks first refresh, invalid hold, transition refresh, and isolated operand hold.
9. `tb_edge_cases`
10. `tb_photoreceptor_comparison` — run `run -all` or at least 2000 ns; it compares baseline/adaptive inputs and emits the paired CSV.

Use the common source dependencies listed in the project's Vivado filesets: the six current modules, `phototransduction.v`, `sigmoid_lut.v`, `gate_update.v`, `calcium_dynamics.v`, `membrane_voltage.v`, and the relevant top/baseline/adaptive/scheduler/budget modules. Run `photoreceptor_top` synthesis manually with `ADAPTIVE_ENABLE=0` for baseline, then `ADAPTIVE_ENABLE=1, OPERAND_ISOLATION_ENABLE=0`, then `ADAPTIVE_ENABLE=1, OPERAND_ISOLATION_ENABLE=1`, keeping part, constraints, clock, and tool options identical. Only the first is the full-update reference; the latter two isolate the operand-isolation effect. New PASS status, switching reduction, timing, area, power, and FPGA feasibility all remain pending user Vivado output.

### Evaluation-audit changes and manual trace refresh

For another trace, add the RTL sources for `tb_photoreceptor_comparison.v` as already listed above and run that bench manually in Vivado for at least 2000 ns or with `run -all`. Confirm the completion message and inspect that the CSV has 160 data rows, 4 scenarios x 40 `cycle_id` values, no blank cells, and columns ending in paired post-edge state values. Then run from `ISCAS 2027`:

```text
python -m pytest -q test_adaptive_trace_metrics.py
python adaptive_trace_metrics.py results/metrics/adaptive_comparison_trace.csv
```

These HDL steps are for the user to execute; no HDL tool was run while preparing this update. The metrics command deliberately rejects the old trace schema. Preserve each fresh simulator log and CSV. Confirm `refresh_decision_pre`, both pre/post counters, and pre-edge applied-current columns before interpreting the summary. The summary reports observed errors and nominal refresh counts only; it does not validate biological fidelity or guarantee accuracy.

### Current Phase 5 checklist

- COMPLETE — Preserve the baseline datapath and introduce a separately selectable adaptive candidate with consistent Q16.24 interfaces.
- COMPLETE — Define the six-current cache group, light/voltage/budget/age triggers, pre-edge use, reset initialization, and invalid-cycle hold.
- COMPLETE — Prepare separate unit/integrated benches and a repeatable CSV metrics workflow.
- COMPLETE — User-reported Vivado/XSim runs for scheduler, budget, adaptive, edge-case, and comparison benches. Comparison PASS was for 4 scenarios x 40 cycles.
- HISTORICAL — Processed the old user-run four-scenario comparison CSV; its mixed pre/post-edge current measurements are superseded and cannot be used for the revised applied-current metrics.
- PENDING — Decide whether the measured tradeoff is acceptable against explicit engineering requirements; no error tolerance was supplied.
- BLOCKED — A mathematically guaranteed voltage-error limit; the current budget proxy has no proof.
- BLOCKED — Biological validation, hardware power savings, and novelty claims.

## Static area optimization trial

The reported synthesis summary (user-provided; detailed report not available for independent verification) gives 27,673 baseline LUTs and 28,226 adaptive LUTs against 20,800 available. It attributes 13,995 LUTs to `calcium_dynamics`. The RTL hierarchy shares its current/gate/calcium/membrane arithmetic between baseline and adaptive, so arithmetic-width changes were made in shared modules rather than separately changing either design.

### Changes

- In `calcium_dynamics.v`, `ca_current.v`, `clca_current.v`, `gate_update.v`, `ih_current.v`, `kca_current.v`, `kv_current.v`, `leakage_current.v`, and `membrane_voltage.v`, the multiply intermediate is sized to `DATA_WIDTH + FRAC_BITS` for `FRAC_BITS <= DATA_WIDTH` (64 bits at 40/24), falling back to the prior `2*DATA_WIDTH` size for larger fractional widths. Only the low `DATA_WIDTH` result bits after the arithmetic shift are observed, so the narrower intermediate retains precisely the product bits needed for that result.
- The scaled numerator in the four Q-division implementations (`clca_current.v`, `gate_update.v`, `kca_current.v`, and `membrane_voltage.v`) uses the same width rule. At 40/24, sign-extending a signed 40-bit numerator and shifting by 24 fits exactly in 64 signed bits; division by zero guards and Verilog truncation toward zero are unchanged.
- In `gate_update.v`, each configured slope is an exact Q16.24 multiple representing 8, 10, 8, 5, or 6. The common fixed-point scale is canceled, replacing `(numerator * 2^24) / (slope_units * 2^24)` with signed integer `numerator / slope_units`. This preserves truncation toward zero. A generate-time general-Q-division branch is retained for zero or non-integral `SLOPE_Q` parameters.
- `phototransduction.v` uses the same exact product-width rule.
- `sigmoid_lut.v` replaces division by `HALF_STEP` with `>>> (FRAC_BITS - 1)`. In the non-clamped branch `shifted_x > 0`, and the divisor is the positive power of two `2^(FRAC_BITS-1)`, so the integer index is unchanged.

No equations, constants, current aggregation, state update order, gate table, or ignored calcium-current input behavior was changed. This does not remedy the scientific limitation that `i_ca_pA_q` is unused; changing that would alter the provisional model.

### Evidence and limitations

`test_rtl_arithmetic_widths.py` compares narrowed versus former full-width multiply/divide semantics, including exhaustive small widths, default-width signed extrema and randomized data, exact gate-slope cancellation, and sigmoid index boundaries/random inputs. The tests also check that the edited RTL sources contain the intended widths and shift. Focused tests (`test_rtl_arithmetic_widths.py` and `test_baseline_fixed_point.py`) passed: **20 passed**; the complete Python suite passed: **46 passed**. No HDL tool or synthesis was run.

The change is intended to reduce unnecessary intermediate datapath width and expose narrower arithmetic to synthesis in both designs. Synthesis may already have pruned unused high bits or constant-folded some expressions; therefore no LUT reduction is guaranteed. In particular, the reported calcium hierarchy count cannot be diagnosed precisely without the full hierarchical report, synthesis messages, and DSP mapping details.

### Next verification

1. Run Python-only: `python -m pytest -q test_rtl_arithmetic_widths.py test_baseline_fixed_point.py`.
2. In Vivado, run the existing fixed-point, phototransduction, ionic-current, baseline, adaptive, and comparison benches using the same source sets and stimuli as the golden build. Require exact Q16.24 output/state comparison for the default configuration.
3. Synthesize baseline and adaptive with identical Vivado version, part, constraints, top, and options. Save hierarchical LUT/FF/DSP utilization, multiplier/DSP mapping, timing summary, and worst paths.
4. Compare reports against the pre-change golden results. These reports—not Python arithmetic checks—determine whether LUT use, timing, or resource use improved.

The user has now supplied top-level implementation/power screenshots, but they do not include the raw reports or enough run metadata to independently verify timing, synthesis status, or the prior-to-current arithmetic optimization delta. The screenshots are transcribed below. Modified RTL simulation remains unverified. No claim of biological fidelity, activity reduction, power saving, or guaranteed voltage accuracy is made.

## User-reported implementation comparison

The latest screenshots compare the top wrapper with `ADAPTIVE_ENABLE=0` and `ADAPTIVE_ENABLE=1`. Reported values are: LUT 16,348 vs. 28,226; FF 283 vs. 701; DSP 71 vs. 71; I/O 125 vs. 125; total power estimate 0.863 W vs. 0.899 W; dynamic power estimate 0.791 W vs. 0.827 W; static estimate 0.072 W for both. Both power reports are explicitly low confidence. With the screenshot's 20,800-LUT capacity, adaptive is 7,426 LUTs over capacity. These are user-provided report values; the raw reports/settings were unavailable. See [IMPLEMENTATION_RESULTS.md](./IMPLEMENTATION_RESULTS.md).

The source default for `photoreceptor_top.ADAPTIVE_ENABLE` is 1. The baseline screenshot therefore corresponds to an explicit override of 0. The older baseline figure of 27,673 LUTs is from a conflicting prior report and is not directly comparable without matching run settings.

The reported low-confidence power values do not establish a physical increase or decrease; notably, they show no estimated saving. The RTL still evaluates the six combinational current blocks continuously, so the current adaptive design cannot claim hardware activity suppression. The Python experiment follow-up is separate from this hardware result and is summarized in `IMPLEMENTATION_RESULTS.md`.
