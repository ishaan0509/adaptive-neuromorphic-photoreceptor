# Existing adaptive algorithm and limits

## Baseline update

The baseline computes `I_photo` and six ionic currents from the current voltage, gate, calcium state, and light. On each valid clock edge, membrane voltage, gates, and calcium states update using those pre-edge currents/states. The default fixed-point representation is signed 40-bit Q16.24.

## Existing RTL adaptive policy

The current RTL caches the six ionic currents together. A valid sample requests refresh when any of the following holds:

1. No cache has yet been initialized after reset.
2. Light differs from the light value recorded at refresh.
3. Voltage differs from its refresh snapshot by the configured threshold.
4. The heuristic voltage-step accumulator reaches its configured budget.
5. Maximum accepted-sample age is reached.

`I_photo` remains combinational; gate, calcium, and membrane state updates continue on valid samples. Invalid samples hold state and cache. The first accepted sample refreshes. Setting `MAX_REFRESH_INTERVAL=1` requests a current refresh for every valid sample.

## Python policy and counted operations

`discrete_time_model.py` has `full`, `periodic`, `threshold`, and `budget` policies. It evaluates each current function only when that current is selected for refresh and reports the number of such calls. The threshold/budget policies use first-order current sensitivities at the last refresh snapshot:

`estimated_stale_error_i = sum_j(abs((dI_i/dx_j at snapshot) * (x_j - x_j_snapshot)))`

The empirical budget accumulates an estimate scaled by `dt/C_m` and forces all currents to refresh near a configured threshold. This is a local linear estimate; it omits nonlinear remainder and parameter/state-domain uncertainty. It is not conservative and cannot guarantee voltage error.

## Required interpretation

- Before operand isolation was added, the adaptive current datapaths saw live voltage/gate/calcium operands and could switch continuously. The current RTL still contains combinational current logic, but by default its operands are selected from refresh snapshots between refreshes. This is structural switching suppression, not a measured activity or power result.
- Python function-call reductions are actual avoided calculations in that Python implementation only. They do not establish FPGA switching, area, energy, or power reductions.
- The 10 μV empirical budget did not bound observed trajectory error in the run: the periodic-light case reached 51.58 μV and ramp reached 32.14 μV.
- No error-constrained RTL algorithm is validated. Do not add a formal-bound label or claim guaranteed accuracy.

## Python matched-target comparison (2026-10-10)

A fixed 10 μV maximum observed voltage-error target was used only to choose configurations on the nine existing training stimuli. The selected per-current sensitivity configuration was `current_error_threshold=1e-14 A`, `max_interval=16`; the selected accumulated-voltage-proxy configuration was `voltage_error_budget=1e-6 V`, `max_interval=16`. Six deterministic waveforms (additional step times, double pulse, triangular ramp, rapid pulse train, chirped illumination) were evaluated only after selection.

On those six held-out traces:

- Per-current sensitivity: max observed voltage difference 1.48659 μV (worst: held-out triangle ramp), pooled RMS 0.21603 μV, pooled MAE 0.08455 μV, 0 samples over 10/50/100 μV, 38.08% Python current-function evaluation reduction (222,934/360,036 calls).
- Accumulated voltage proxy: max observed voltage difference 6.97410 μV (worst: held-out chirped illumination), pooled RMS 0.31175 μV, pooled MAE 0.04978 μV, 0 samples over 10/50/100 μV, 33.00% reduction (241,224/360,036 calls).

Both policies remained below the chosen observed-error target on these finite traces. The sensitivity policy achieved lower maximum/RMS voltage error and higher Python function-call reduction, while the accumulated proxy had lower pooled MAE. This is limited evidence supporting further evaluation of the sensitivity policy, not evidence of novelty, a formal error guarantee, hardware switching savings, or biological fidelity. Training and held-out outputs are in `results/metrics/heldout_scheduler/`.

## Current RTL operand isolation and boundary behavior

`photoreceptor_adaptive` retains the existing global refresh policy (initialization, light change, voltage excursion, accumulated proxy, and maximum age) and now defaults `OPERAND_ISOLATION_ENABLE=1`. Before the six current modules, input muxes select live voltage/gate/calcium operands only while `refresh_all` is asserted; otherwise they feed registers holding the operands from the last accepted refresh. Those snapshot registers update on `valid_in && refresh_all` and reset to known initial state values. The first accepted sample is forced to refresh by the scheduler's uninitialized state. Invalid samples do not update snapshots or caches.

This operand-isolation change does **not** implement the Python per-current sensitivity scheduler: the RTL remains group-refresh and its fixed-point heuristic thresholds are not calibrated to the Python `1e-14 A` setting. Do not claim that the RTL inherits the Python held-out accuracy numbers. It is a separate hardware-side experiment. The baseline remains unchanged and selectable via `ADAPTIVE_ENABLE=0`; `OPERAND_ISOLATION_ENABLE=0` bypasses operand isolation for an adaptive A/B comparison.

The scheduler's 16-bit sample-age counter saturates and uses an effective interval clamped to 65,536 samples for oversized parameter values. The 32-bit recomputation counter saturates instead of wrapping. These changes avoid silent counter rollover; they do not change biological equations. The isolation muxes/registers can increase LUT/FF use and timing pressure; only manual Vivado measurements can establish whether the design fits or has reduced switching.
