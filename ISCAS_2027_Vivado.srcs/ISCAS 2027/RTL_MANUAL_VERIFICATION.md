# Manual Vivado verification

**All HDL tests, synthesis, timing, implementation, and power analyses must be run manually by the user. None was run by the assistant.**

## Preserve comparability

Keep a copy of the original baseline source and reports. For both configurations, use the same Vivado version, exact FPGA part, constraints, source set, top (`photoreceptor_top`), clock, implementation options, and power-analysis activity window. Set `ADAPTIVE_ENABLE=0` for baseline and `ADAPTIVE_ENABLE=1` for adaptive. Record each value in the run notes and retain the raw reports.

## Simulation order

Add the testbench from `sim_1/new/` and the listed design sources from `sources_1/new/`; set each bench as simulation top in turn:

1. `tb_fixed_point_math` — `fixed_point_math.v`.
2. `tb_phototransduction` — `phototransduction.v`.
3. `tb_ionic_currents` — `ih_current.v`, `kv_current.v`, `ca_current.v`, `clca_current.v`, `kca_current.v`, `leakage_current.v`.
4. `tb_photoreceptor_baseline` — `phototransduction.v`, the six current modules above, `sigmoid_lut.v`, `gate_update.v`, `calcium_dynamics.v`, `membrane_voltage.v`, `photoreceptor_baseline.v`.
5. `tb_photoreceptor_baseline_trace` — the same baseline dependency set as step 4.
6. `tb_current_update_scheduler` — `current_update_scheduler.v`.
7. `tb_voltage_error_budget` — `voltage_error_budget.v`.
8. `tb_photoreceptor_adaptive` — `phototransduction.v`, the six current modules, `sigmoid_lut.v`, `gate_update.v`, `calcium_dynamics.v`, `membrane_voltage.v`, `current_update_scheduler.v`, `voltage_error_budget.v`, `photoreceptor_adaptive.v`.
9. `tb_edge_cases` — the adaptive dependency set from step 8.
10. `tb_photoreceptor_comparison` — the common baseline dependencies from step 4, plus `current_update_scheduler.v`, `voltage_error_budget.v`, `photoreceptor_adaptive.v`, and `photoreceptor_top.v`. This bench instantiates the baseline and adaptive implementations and both top parameter values; run `run -all` or at least 2000 ns for the four 40-cycle scenarios.

For standalone synthesis comparison, set `photoreceptor_top` as the synthesis top and explicitly override `ADAPTIVE_ENABLE=0` for baseline, then `=1` for adaptive; the RTL default is 1. Confirm all named ports and source dependencies against actual RTL before elaborating.

Previous PASS messages in `PROJECT_STATUS.md` are user-reported historical results and do not validate the latest arithmetic-width edits. Keep new transcripts separately; do not alter expected vectors to suppress failures.

## Synthesis and implementation

After simulation regression:

1. Create one run with `photoreceptor_top`, `ADAPTIVE_ENABLE=0`.
2. Create a second run with the same top and settings, `ADAPTIVE_ENABLE=1`.
3. Save hierarchical utilization: LUT, FF, DSP, I/O by hierarchy; include available LUT capacity and inferred multiplier/DSP mapping.
4. Save timing summary, worst paths, constraints, and implementation status.
5. Save power reports and their confidence/accuracy, activity source, input window, and assumptions. Prefer matched SAIF/VCD from the same stimuli for both configurations; vectorless low-confidence reports are not sufficient evidence of a power improvement.
6. Compare against the same-source pre-optimization golden runs, not numbers from different configurations or report stages.

## Current known outcome

The supplied screenshots report baseline 16,348 LUT/283 FF and adaptive 28,226 LUT/701 FF, with estimated total power 0.863/0.899 W and low confidence. On the stated 20,800-LUT capacity, adaptive exceeds capacity. These numbers need raw-report confirmation and are not assistant-run results.

## Current source follow-up: operand isolation and held-out vectors

The current source adds `OPERAND_ISOLATION_ENABLE` to `photoreceptor_top` and `photoreceptor_adaptive`; it defaults to 1. `ADAPTIVE_ENABLE=0` selects the unchanged full-update baseline. For the adaptive design, test these matched parameter configurations:

1. Baseline: `ADAPTIVE_ENABLE=0`.
2. Adaptive without operand isolation: `ADAPTIVE_ENABLE=1`, `OPERAND_ISOLATION_ENABLE=0`.
3. Adaptive with operand isolation: `ADAPTIVE_ENABLE=1`, `OPERAND_ISOLATION_ENABLE=1`.

The policy remains the existing group-refresh scheduler; Python's per-current sensitivity policy is not implemented in RTL. Do not interpret the Python matched-target values below as expected RTL accuracy.

### Manual simulation order

Add the relevant RTL modules to Design Sources and set each listed bench as the Simulation Top in this order:

1. `tb_fixed_point_math` — `fixed_point_math.v`.
2. `tb_phototransduction` — `phototransduction.v`.
3. `tb_ionic_currents` — all six ionic current modules.
4. `tb_photoreceptor_baseline` — phototransduction, current modules, sigmoid, gate update, calcium, membrane, baseline.
5. `tb_photoreceptor_baseline_trace` — same dependencies as baseline. Run `run -all`; it reads eight CSV traces: dark, step, pulse, alternating, held-out step, held-out double pulse, held-out ramp, and held-out rapid pulse.
6. `tb_current_update_scheduler` — `current_update_scheduler.v`.
7. `tb_voltage_error_budget` — `voltage_error_budget.v`.
8. `tb_photoreceptor_adaptive` — adaptive dependencies including scheduler and budget. Check first refresh, invalid hold, light transition, recomputation count, and isolated operand hold.
9. `tb_edge_cases` — adaptive dependencies.
10. `tb_photoreceptor_comparison` — baseline and adaptive dependencies plus `photoreceptor_top.v`. Run `run -all` or at least 2000 ns; confirm all four scenarios complete and the paired CSV is emitted.

Expected PASS messages in the benches are assertions to be checked by the user; no modified bench has been executed here. Preserve full transcripts. If the testbench output file cannot be opened, set the project results folder in Vivado or update the testbench path to the actual workspace path without changing expected values.

### Vector and Python experiment locations

- Baseline bit-accurate Q16.24 vectors: `results/rtl_reference_vectors/baseline_{dark,step,pulse,alternating,heldout_step,heldout_pulse,heldout_ramp,heldout_rapid}_q16_24.csv`.
- Regenerate the five added vectors from the project Python folder with `python export_rtl_reference_vectors.py`. Values are signed raw Q16.24; `real = raw / 2^24`; light is normalized; model state/current units follow `RTL_REVIEW.md`.
- Held-out scheduler outputs/metadata/plot: `results/metrics/heldout_scheduler/heldout_scheduler_results.csv`, `heldout_scheduler_metadata.json`, and `heldout_scheduler_tradeoff.png`.
- Re-run the Python tests with `python -m pytest -q` before any manual HDL test.

### Manual hardware comparison after simulation

Use identical Vivado version, FPGA part, constraints, clock, sources, and implementation options for all three top configurations above. Record elaborated parameter values. Save hierarchical LUT/FF/DSP and timing reports. For activity/power, use matched input traces and comparable SAIF/VCD windows; vectorless low-confidence estimates are not sufficient to claim benefit. Compare the two adaptive variants to isolate operand isolation, and the baseline to quantify total adaptive overhead. Resource utilization, timing closure, switching reduction, power reduction, and FPGA feasibility are all pending.

The 10 μV Python training target and held-out results are empirical observations on a provisional double-precision model. They are neither an RTL specification nor a guarantee. The selected Python sensitivity policy is not implemented in the current RTL. Biological fidelity and research novelty remain unresolved.
