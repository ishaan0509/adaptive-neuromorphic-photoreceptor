# Assumptions and Units

## Intended SI units in the current Python code

- capacitance: farads (F)
- conductance: siemens (S)
- voltage: volts (V)
- currents: amperes (A)
- concentration: molar (M)

## Appendix B source-vs-code status

The attached paper's Appendix B was transcribed from the supplied enlarged
images for printed pages 8–10. See `PAPER_EQUATION_AUDIT.md` for the equations,
paper values/initial conditions, component-by-component discrepancy table,
and unresolved notation.

The initial code still uses a direct normalized-light photocurrent, generic
sigmoid activation curves, simplified calcium dynamics, and placeholder
parameters/initial conditions. These are known mismatches, not uncertain
transcriptions of the paper. The generated dark/step/pulse/ramp waveforms are
engineering stimuli, not reproductions of the paper stimulus.

The B.2 input `J_hv(t)` is undefined in the supplied Appendix B. Some units
and the coupling between the B.2 Ca/Cab/cGMP states and B.9 shell/free calcium
states also remain unclear. As a result, the source equations cannot yet be
run as a fully specified paper experiment without inventing information.
The paper's printed parameter units should not be conflated with the
provisional code's SI conventions.
