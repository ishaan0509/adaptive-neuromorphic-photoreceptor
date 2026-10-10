# Neuromorphic Retina Project — Work Completed and Current Position

This note summarizes the work completed so far in the existing Vivado project.
It is a project handoff and does not replace the technical details in
`PROJECT_STATUS.md`, `RTL_REVIEW.md`, or `PAPER_EQUATION_AUDIT.md`.

## Project organization

The original project structure is preserved:

- `ISCAS 2027/` — Python models, tests, experiment scripts, results, and research notes.
- `sources_1/new/` — synthesizable RTL source files.
- `sim_1/new/` — Verilog testbenches, including the CSV-driven baseline trace test.

The existing RTL baseline has not been replaced by a new project or branch.

## Work completed

### 1. Provisional Python model and numerical experiments

The Python side includes:

- A parameter container in `photoreceptor_parameters.py`.
- A floating-point provisional continuous-time model in `photoreceptor_reference.py`.
- A discrete-time Euler model in `discrete_time_model.py`, with full, periodic,
  threshold-triggered, and empirical voltage-error-budget current-update modes.
- Deterministic dark, step, pulse, ramp, and other engineering stimulus
  generators in `generate_stimuli.py`.
- Experiment, comparison, and result-generation scripts.

These models were useful for developing and exploring the architecture, but
their original equations and parameter values were not paper-derived. The
existing convergence and scheduler experiments describe only that provisional
model. The error-budget scheduler is an empirical estimator, not a proven
bound. Current-calculation counts are not evidence of power savings.

### 2. Baseline fixed-point RTL and matching Python reference

The baseline RTL uses signed 40-bit Q16.24 arithmetic. Its existing modules
implement a direct light-to-photocurrent relationship, six ionic-current
equations, gate updates using a 33-entry sigmoid lookup table, simplified
calcium-state updates, and an Euler membrane-voltage update.

`baseline_fixed_point.py` mirrors the current default RTL arithmetic and cycle
behavior, including signed wrapping, truncating multiplication/division,
lookup-table indexing, reset, pre-edge current use, and idle-state hold.
`export_baseline_vectors.py` produces signed raw-integer expected-value CSVs
for 40-cycle dark, step, and pulse scenarios.

The trace testbench in `sim_1/new/tb_photoreceptor_baseline_trace.v` reads those
CSVs and compares observable RTL states and currents cycle by cycle.

### 3. User-reported Vivado verification

The user reported these manual Vivado/XSim results:

| Testbench | Reported result |
|---|---|
| `tb_fixed_point_math.v` | PASS; finish at 3 ns |
| `tb_current_update_scheduler.v` (previous interface) | Historical PASS; finish at 86 ns; does not validate the Phase 5 scheduler rewrite |
| `tb_phototransduction.v` | PASS; finish at 4 ns |
| `tb_ionic_currents.v` | PASS; finish at 2 ns |
| `tb_photoreceptor_baseline.v` | PASS; finish at 26 ns |
| `tb_photoreceptor_baseline_trace.v` | All 40 rows matched for each of dark, step, and pulse; final PASS at 1206 ns |

These are user-reported results. The assistant did not execute or independently
inspect HDL compilation, simulation, waveforms, or synthesis. In particular,
the three-scenario trace match establishes agreement between the current RTL
and its bit-accurate Python reference for those vectors and the default RTL
configuration only. It does not establish biological fidelity.

### 4. Appendix B source review

The attached Shah et al. paper was reviewed using the supplied enlarged
Appendix B images for printed pages 8–10. Equations and parameters were
transcribed into `PAPER_EQUATION_AUDIT.md`, with source locations, states and
currents, initial conditions, a Python/RTL discrepancy table, and unresolved
notation.

The paper describes:

- A membrane equation whose total current includes nine terms, including
  `I_ex` and `I_ex2`.
- A multistate phototransduction cascade, with a voltage-dependent photocurrent.
- A five-state hyperpolarization-activated current.
- Distinct activation/inactivation kinetics for delayed-rectifier and calcium
  channels.
- Calcium-dependent chloride and potassium currents.
- Shell/free calcium and multiple calcium-buffer states.

### 5. Main finding: the baseline is not the paper model

The Appendix B audit found material mismatches between the paper and both the
provisional Python model and baseline RTL. Examples include:

- Direct normalized-light photocurrent instead of the paper's phototransduction
  cascade.
- Generic LUT gate updates instead of the paper's channel-specific kinetics.
- Missing Ih/Kv/Ca channel states and missing `I_ex`/`I_ex2` terms.
- Simplified calcium states instead of the B.2/B.9 coupled states and buffers.
- Different conductances, reversal potentials, capacitance, and initial states.
- Calcium-current concentration input accepted but unused in the baseline RTL.

The LUT and Q16.24 wrap/truncation are hardware implementation choices; they
are not equations stated in Appendix B. The current passing RTL must therefore
be described as an engineering baseline, not a biologically faithful model.

## Current research status

**Source audit:** Appendix B equations and listed parameter/initial-condition
values have been transcribed and compared against the existing code.

**Python numerical tests:** The latest full Python run reported
`26 passed` in the latest run, including eight focused tests for the paper
transcription and two tests for adaptive-trace metrics. No HDL tools were run
for the Phase 5 candidate.
This verifies code behavior, not biological fidelity.

**RTL/Python reference agreement:** The user-reported CSV-driven Vivado run
matched all rows for three generated baseline scenarios. This is scoped to
those tests and the current default RTL.

**Biological response validation:** Not completed.

**Separate paper-equation implementation:** Added as
`paper_biological_model.py` and `paper_biological_parameters.py`. It retains
the B.2 and B.9 calcium groups separately and requires explicit choices for
`J_hv(t)` and the unresolved calcium-reversal logarithm base.

**Paper-model solver convergence:** A 5 ms synthetic zero-input DOP853
convergence screen was run for both explicit logarithm branches. Endpoint
differences versus the tighter solver reference were at most `2.28e-13` in
the maximum-step sweep; tolerance-sweep differences ranged from `9.95e-14`
to `1.35e-10` (the largest was the intentionally loose base-10 case). This
is numerical consistency under an assumed input, not a paper stimulus or
biological validation. Per-state errors are exported; the across-state
maximum combines unlike units and is diagnostic only. Eight focused equation
tests passed.

**Synthesis, hardware metrics, and power:** The user supplied screenshots from
separate `photoreceptor_top` runs with `ADAPTIVE_ENABLE=0` and `=1`. They report
16,348/28,226 LUTs, 283/701 FFs, and low-confidence power estimates of
0.863/0.899 W total and 0.791/0.827 W dynamic. Raw reports and run settings
were not supplied, so these values are user-reported and not independently
verified. The adaptive result exceeds the stated 20,800-LUT capacity. No power
saving or timing claim is made; see `IMPLEMENTATION_RESULTS.md`.

### 5. Adaptive RTL candidate (static inspection; user reports partial Vivado results)

The existing baseline remains unchanged. `photoreceptor_top` selects baseline
when `ADAPTIVE_ENABLE=0` and adaptive when nonzero; its current RTL default is
1, so baseline must be explicitly selected. The separate adaptive datapath uses 40-bit Q16.24 interfaces,
caches all six ionic currents as one group, and continues to update membrane,
gate, and calcium states every accepted sample. `photoreceptor_top` selects it
with `ADAPTIVE_ENABLE=1`; `MAX_REFRESH_INTERVAL=1` forces full ionic-current
refreshes. Refresh triggers include first accepted sample, light changes since
the last refresh, absolute voltage excursion, an accumulated scaled
voltage-step proxy, and maximum cache age.

The budget input is `abs(V[n]-V[n-1]) >> 4`; it is an engineering heuristic,
not a bound on stale-current voltage error. New scheduler, budget, adaptive,
and baseline/adaptive comparison benches are prepared. The comparison bench
exports dark, step, pulse, and alternating-light traces with voltage, currents,
calcium states, and gates; `adaptive_trace_metrics.py` calculates max/RMS
differences and recomputation counts. The user reports that all five adaptive
benches passed in Vivado/XSim, including 4 scenarios x 40 comparison cycles
finishing at 1680 ns. Metrics were calculated from the resulting CSV:
current-evaluation avoidance was 55% dark, 27.5% step, 20% pulse, and 0%
alternating light. Maximum voltage differences from baseline were 0.1784,
0.1274, 0.1863, and 0 mV; max total-current difference was 30.8087 pA for the
first three and zero for alternating light. No refresh-trigger misses,
interval violations, or counter mismatches were reported. These short
provisional-model traces do not establish a guaranteed error bound, acceptable
accuracy, biological fidelity, or power savings. See `RTL_REVIEW.md` for RMS
and per-state results.
See `RTL_REVIEW.md` for exact manual test order and CSV procedure.

## Remaining blockers and next work

1. Resolve a source-supported definition, units, and time course for the
   phototransduction input `J_hv(t)`. It is used in Appendix B, but the
   inspected material does not specify the stimulus waveform, amplitude, or
   units.
2. Clarify how the B.2 calcium/bound-calcium states relate to the B.9 shell/free
   calcium compartments, including any required unit conversions. Resolve the
   unspecified base of the logarithm in the calcium reversal-potential
   equation from the cited source.
3. Cross-check the new float64 transcription against a legible original-paper
   copy and seek source-supported definitions for the remaining ambiguities.
   Do not overwrite the passing provisional model or RTL baseline.
4. Once the stimulus/units and other required definitions are supported, run
   the source-defined response and compare against any recoverable published
   data. Keep numerical convergence distinct from biological validation.
5. Quantify integration error separately from LUT and fixed-point error only
   after a scientifically supported operating trajectory is available.
6. Compare to published plots only if the stimulus and scaling can be
   established; any digitized curve must include digitization uncertainty.
7. Run the Phase 5 adaptive testbenches manually and assess the measured
   trace errors/recomputation counts. Keep them scoped to the provisional
   engineering baseline; paper-model source definitions remain blocked.

## Key documents

- `PROJECT_STATUS.md` — current validation record and next steps.
- `PAPER_EQUATION_AUDIT.md` — Appendix B transcription and detailed mismatch audit.
- `RTL_REVIEW.md` — baseline RTL behavior, user-reported test evidence, and Vivado guide.
- `RTL_FIXED_POINT_REFERENCE.md` — fixed-point semantics and CSV comparison details.
- `README.md` — original project overview.
