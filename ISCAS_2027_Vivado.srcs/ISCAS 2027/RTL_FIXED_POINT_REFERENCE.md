# Baseline RTL fixed-point reference

## Scope

`baseline_fixed_point.py` models the current default baseline RTL with
`DATA_WIDTH=40` and `FRAC_BITS=24`. It is intended to generate expected raw
values for manual comparison with Vivado traces. It does not validate the
model against Shah et al.; the biological equations, constants, signs, units,
and initial conditions remain provisional.

The user-reported XSim run matched the generated dark, step, and pulse CSVs
for all 40 rows in each scenario. This is scoped to those vectors and the
default RTL configuration; the assistant did not independently inspect the
raw waveforms or full simulator transcript.

## RTL behavior reproduced

- Signed state and signal words are 40-bit two's-complement values. Addition,
  subtraction, and assigned results wrap to their destination width; there is
  no saturation.
- Q multiplication forms a signed 80-bit product, arithmetic-shifts right by
  24, then keeps the signed 40-bit result. This is truncation toward negative
  infinity for negative non-integral products, as with Verilog `>>>`.
- Q division sign-extends its numerator into an 80-bit temporary, shifts left
  24 with 80-bit wrap, performs signed division truncated toward zero, then
  keeps the low 40-bit result. Calcium-channel divisions are bypassed when
  their wrapped denominator is zero.
- Driving-force and activation-denominator additions/subtractions wrap at 40
  bits before being used by the current calculations.
- The photocurrent multiplies the wrapped 40-bit light word by the Q16.24
  `2000 pA` gain, shifts the 80-bit product by 24, and keeps 40 bits.
- The 33 sigmoid table words and input-index calculation are copied from
  `sigmoid_lut.v`. It clamps at +/-8, adds the 0.25 offset, divides by a
  0.5 step, and uses the resulting integer index. No floating-point sigmoid
  is used.
- All ionic currents are calculated from the pre-edge voltage, gate, and
  intracellular-calcium states, plus the current `light_q`.
- On a valid rising edge, voltage, gates, and calcium update from the same
  pre-edge values. Current output signals are combinational, so the exported
  cycle row contains currents recomputed from the post-edge state and the
  cycle's light input.
- Reset is active high and asynchronous for each state/valid register. A reset
  cycle restores the RTL initial words, and reset dominates `valid_in`.
- With `valid_in=0`, registered states hold and `valid_out` deasserts. The
  combinational current outputs continue to reflect the current light input
  and held state.

The exported model is deliberately restricted to the RTL's default 40/24
format. It raises an error if constructed with a different width or fraction.

## Known approximations and unresolved assumptions

1. **Unverified science:** Equations and constants are copied from the current
   provisional RTL/Python work; no Appendix B validation has been done.
2. **Gate sigmoid:** The RTL uses its finite 33-entry, half-step LUT. This is
   the RTL's exact table/index behavior, not the Python continuous sigmoid.
3. **Calcium current contribution:** `calcium_dynamics.v` accepts `i_ca_pA_q`
   but does not use it. The reference therefore reproduces a zero
   calcium-current contribution exactly. The RTL comment describes the
   omitted contribution as sub-LSB, but its physical scaling has not been
   independently demonstrated; do not interpret that rationale as validated.
4. **Fixed-point constants:** Constants are the exact raw literals in the
   RTL. Some were rounded when originally selected; the reference does not
   regenerate them from decimal biological parameters.
5. **Overflow:** RTL arithmetic generally wraps without a flag. The only
   reported divide-by-zero signal is reproduced; there is no arithmetic
   overflow signal.
6. **Independent validation:** This reference mirrors the RTL source and is
   tested with Python unit tests. The user-reported XSim trace comparison is
   evidence of matching for the generated scenarios, not an independent proof
   for other stimuli, parameterizations, or biological fidelity.

## Deterministic stimulus and CSV format

From `ISCAS 2027`, run:

```powershell
python export_baseline_vectors.py --cycles 40
```

The script writes:

- `results/rtl_reference_vectors/baseline_dark_q16_24.csv`
- `results/rtl_reference_vectors/baseline_step_q16_24.csv`
- `results/rtl_reference_vectors/baseline_pulse_q16_24.csv`

Each CSV has one row per active clock cycle. Cycle 0 asserts asynchronous
reset; later cycles have `valid_in=1`. Dark holds light at zero. Step light
changes from zero to one normalized unit at cycle 10 and remains high. Pulse
light is one unit on cycles 10 through 14, then returns to zero.

All columns ending in `_q`, including `light_q`, contain **signed decimal raw
Q16.24 integers**, not decimal engineering-unit values and not unsigned hex.
Divide by `2^24` to display the represented engineering value. Columns
`m_h_q_out`, `m_kv_q_out`, `m_ca_q_out`, `m_clca_q_out`, and `m_kca_q_out`
use the exact baseline RTL output-port names. `cycle`, `reset`, `valid_in`,
`valid_out`, and `divide_by_zero` are integer 0/1 or cycle metadata.

Rows describe settled outputs **after** the active clock edge. To compare
manually, apply that row's `reset`, `valid_in`, and `light_q` before the edge;
after the edge and combinational settling, compare the exported states,
currents, `valid_out`, and `divide_by_zero`. On cycle 0, assert reset and
compare the reset state/current outputs; on cycle 1, deassert reset and
compare the first accepted update. Ensure the Vivado test uses the baseline
module and the same 40-bit / 24-fractional-bit parameters.

CSV generation is deterministic. Pass a different `--cycles` value to make
shorter or longer traces; step and pulse onset positions are derived from the
requested count, so use the documented 40-cycle setting for direct comparison.

## Automated Vivado comparison testbench

Add `tb_photoreceptor_baseline_trace.v` to Simulation Sources and set it as
simulation top. Add the same baseline Design Sources listed for
`tb_photoreceptor_baseline.v`. This testbench opens the three generated CSVs
using the project-root path
`C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/`
and checks all 40 rows in each file. If the project is moved, update those
three paths in the testbench or Vivado will report a file-open failure.

For each row, it applies the row inputs before a rising edge and compares the
settled post-edge values of voltage, all seven current outputs, all five gate
outputs, all three calcium states, `valid_out`, and `divide_by_zero` with the
CSV row. No waveform file is required to determine pass/fail. Expected console
messages identify scenarios as 0=dark, 1=step, and 2=pulse:

```text
PASS scenario 0: all 40 post-edge rows matched
PASS scenario 1: all 40 post-edge rows matched
PASS scenario 2: all 40 post-edge rows matched
PASS tb_photoreceptor_baseline_trace: dark, step, and pulse CSV comparisons
```

On mismatch it prints the scenario ID, cycle, expected and actual current/state
vectors, and reports the total mismatch count. A CSV parse or file-open issue
is reported as a failure. The user reports XSim PASS for all three scenarios
and the final testbench summary at 1206 ns. This is reported evidence of
agreement for these traces only, not other parameter settings or biological
fidelity.

## Python-only tests

Run from this folder:

```powershell
python -m pytest -q test_baseline_fixed_point.py
```

The tests cover signed range wrapping, multiplication/division behavior,
sigmoid clamping and center lookup, reset precedence, valid/idle state timing,
fixed first-step raw values, deterministic multi-step stimuli, and CSV
structure. They invoke no HDL tools.
