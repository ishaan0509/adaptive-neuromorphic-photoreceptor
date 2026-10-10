# ISCAS 2027 Digital Neuromorphic Retina Project

This workspace contains a provisional Python model, numerical experiments and an RTL prototype under review for the ISCAS 2027 research project. Appendix B of Shah et al. has been transcribed and audited, and the current Python/RTL equations and parameters are **confirmed to differ materially from it**; generated plots and metrics are debugging evidence for the provisional code, not scientific validation.

## Structure

- `photoreceptor_parameters.py`: consolidated parameter set
- `numerical_methods.py`: fixed-point and numerical helpers
- `photoreceptor_reference.py`: continuous-time reference simulation
- `discrete_time_model.py`: Euler integration with actual cached-current update policies
- `generate_stimuli.py`: reproducible stimulus generation
- `run_reference_experiments.py`: experiment runner for stimulus suite
- `compare_models.py`: provisional solver, Euler and state-quantization comparison
- `run_adaptive_experiments.py`: full, periodic, threshold and empirical-budget scheduler screening
- `generate_results.py`: provisional trace and plot generation
- `RTL_REVIEW.md`: RTL limitations and manual Vivado check guidance
- `PROJECT_STATUS.md`: validation status, user-confirmed Vivado results, and next steps
- `RESEARCH_AUDIT.md`, `RESEARCH_QUESTION.md`, `ALGORITHM.md`, `LITERATURE_REVIEW.md`: current research framing and limits
- `IMPLEMENTATION_RESULTS.md`, `RTL_MANUAL_VERIFICATION.md`, `FINAL_RESEARCH_ASSESSMENT.md`: user-reported hardware results, manual test recipe, and evidence assessment
- `baseline_fixed_point.py`: RTL-matched Q16.24 cycle model
- `export_baseline_vectors.py`: deterministic per-cycle raw-value CSV export
- `sim_1/new/tb_photoreceptor_baseline_trace.v`: Vivado CSV-driven trace comparison testbench
- `sources_1/new/photoreceptor_adaptive.v`: separate cached-ionic-current candidate; the baseline remains the reference
- `sim_1/new/tb_photoreceptor_comparison.v`: four-scenario baseline/adaptive trace capture
- `adaptive_trace_metrics.py`: post-processes the comparison CSV for state/current errors and refresh counts
- `test_adaptive_trace_metrics.py`: Python-only tests for CSV metrics and mandatory refresh checks
- `RTL_FIXED_POINT_REFERENCE.md`: arithmetic semantics, CSV comparison procedure, and assumptions
- `PAPER_EQUATION_AUDIT.md`: Appendix B transcription, source parameters/initial conditions, audit table, and validation blockers
- `paper_biological_parameters.py`: separate transcription of Appendix B parameters and initial conditions
- `paper_biological_model.py`: double-precision equations B.1–B.9, with unresolved stimulus and log base explicitly supplied by the caller
- `test_paper_biological_model.py`: Python-only equation and invariant tests for the separate paper-model transcription
- `run_paper_model_convergence.py`: short solver convergence experiment under an explicitly synthetic zero-input condition
- `results/metrics/paper_model_solver_convergence.csv`: per-case solver convergence settings and endpoint differences
- `run_all.py`: top-level pipeline entry point

## Notes

This implementation is intentionally structured to match the requested Vivado project layout and the research flow described in the project prompt. It focuses on the scientific Python reference model before the adaptive Verilog design phase.

The existing engineering model and passing RTL remain unchanged and are not paper-faithful. A separate double-precision transcription of the visible Appendix B equations now exists, with tests and a numerical convergence screen. The screen uses synthetic zero `J_hv` and both explicit `E_Ca` logarithm interpretations because the paper does not specify the input stimulus or log base; the B.2/B.9 calcium-state relation also remains unclear. Thus the solver results show only numerical consistency under these explicit branches, not a reproduced paper response or biological validation. See `PAPER_EQUATION_AUDIT.md`, `PROJECT_STATUS.md`, `model_equations.md`, `assumptions_and_units.md`, and `literature_gap.md`. Do not report biological fidelity, current-calculation savings as power savings, or RTL simulation success from these artifacts.

The Python adaptive simulator is a separate algorithmic exploration. Its error-budget estimate is empirical and not a conservative bound. The RTL adaptive candidate likewise reuses six cached ionic currents while updating membrane, gate, and calcium states on every accepted sample. Its budget accumulator receives a scaled absolute voltage-step proxy; this is not a derived error bound. These candidates are for provisional-engineering-model evaluation only.

The user reported PASS for earlier standalone scheduler and baseline tests, including exact Python/Vivado agreement for 40-cycle dark, step, and pulse traces. The scheduler, error-budget, adaptive, and comparison sources have since been changed; the prior scheduler PASS does not validate later edits. The latest user-supplied screenshots compare `photoreceptor_top` with `ADAPTIVE_ENABLE=0` and `=1`: the adaptive report shows more LUTs/FFs, exceeds the stated LUT capacity, and gives low-confidence higher power estimates. These are user-reported report values, not assistant-run verification. See `IMPLEMENTATION_RESULTS.md` and `RTL_MANUAL_VERIFICATION.md`.

## Phase 5 adaptive RTL

The candidate refreshes all six ionic-current equations as a group. It forces an initial refresh, a refresh after light differs from the light value at last refresh, when membrane voltage moves by the configured threshold from its refresh snapshot, when the error proxy reaches its budget, and at the configured maximum accepted-sample interval (default 8). Photocurrent is still evaluated each sample. Voltage, gates, and calcium states continue their normal baseline update each valid sample. Invalid samples hold state and do not count toward the interval. Reset clears caches and initialization state; the first valid sample must refresh before cached currents can be selected. In the inspected `photoreceptor_top.v`, the parameter default is `ADAPTIVE_ENABLE=1`; set it explicitly to 0 for baseline and 1 for adaptive comparisons. `MAX_REFRESH_INTERVAL=1` forces a current refresh each accepted sample.

The default voltage movement threshold is 1 mV raw-Q16.24 and the error-proxy budget is 0.1 mV. The accumulated quantity is `abs(V[n]-V[n-1])/16` in Q16.24 units; the factor of 1/16 is an engineering heuristic, not a sensitivity-derived estimate or guaranteed bound. Full-refresh fallback is selected by lowering `MAX_REFRESH_INTERVAL` to 1. Recalculation counters and the testbench's CSV report six ionic-current evaluations per refresh; they are not a power metric.

Manual Vivado sequence for this new candidate: `tb_current_update_scheduler.v`, `tb_voltage_error_budget.v`, `tb_photoreceptor_adaptive.v`, `tb_edge_cases.v`, then `tb_photoreceptor_comparison.v`. The user reported PASS for all five; the comparison completed 4 scenarios x 40 cycles at 1680 ns. The captured CSV is `results/metrics/adaptive_comparison_trace.csv` under `ISCAS 2027`; the metrics script ran successfully on its 160 rows. Current-evaluation avoidance was 55.00% dark, 27.50% step, 20.00% pulse, and 0.00% alternating light. Maximum voltage differences from baseline were 0.178404, 0.127412, 0.186290, and 0 mV; max total-current differences were 30.80874, 30.80874, 30.80874, and 0 pA. No light-refresh misses, interval violations, or count mismatches occurred. These are measured trace comparisons only, not power savings or biological validation; no acceptable error threshold has been specified. The Python metrics tests passed (2 tests) and are included in the full Python suite (26 passed).

## Run

From the project folder:

```bash
python run_all.py
```

`run_all.py` runs the provisional Python pipeline (reference traces, solver/Euler and state-quantization comparisons, scheduler experiments, and plots). It does not run any HDL tool or Vivado action.

The Python adaptive suite was rerun to `results/metrics/area_followup_python/adaptive_experiments.csv` without overwriting the older metrics file. It records nine stimuli against four scheduler policies; periodic scheduling hit the numerical runaway guard on seven stimuli. Results and limitations are summarized in `IMPLEMENTATION_RESULTS.md`.
