# Research question and falsifiable criteria

## Question

For the existing provisional fixed-point photoreceptor, can an implementation selectively defer ionic-current updates while meeting a voltage-error tolerance chosen before testing, reducing actual current-computation activity, and keeping the hardware resource and activity costs acceptable relative to a full-update baseline?

This is a question, not a novelty or performance claim.

## Configurations to compare

1. **Full-update reference:** recompute all six ionic currents at every accepted sample.
2. **Existing heuristic adaptive:** preserve the RTL's initialization, light, voltage, proxy-budget, and max-age triggers.
3. **Python sensitivity policies:** use the existing periodic, threshold, and empirical-budget modes in `discrete_time_model.py` as distinct experimental comparators. These call the current equations conditionally in Python and must not be conflated with RTL switching activity.

## Assumptions and limits

- Compare identical initial state, stimulus samples, accepted-sample timing, parameters, and arithmetic convention.
- Current evidence is for the provisional model only. The paper-defined optical input, calcium coupling, and `E_Ca` logarithm base remain unresolved.
- The sensitivity/budget estimate is empirical. It is not a mathematical upper bound.
- The RTL currently computes ionic currents combinationally even when cached outputs are selected.

## Preregistered success criteria (proposed, not yet run)

Before a new sweep, choose and record:

- A voltage tolerance in mV and whether it applies to max absolute error or all samples.
- A finite stimulus suite covering dark, steps, pulses, ramps, periodic and adversarial rapid transitions, plus amplitude/timing variation.
- A max refresh interval and scheduler parameters.
- An RTL activity methodology (same clock, constraints, input vectors, implementation settings, and activity source such as matched SAIF/VCD or documented vectorless assumptions).

Candidate evidence for support requires all test traces to satisfy the predeclared voltage tolerance, a reproducible reduction in actual RTL switching/activity, and a feasible area/timing result. Failure of any criterion falsifies the combined claim. Passing finite tests would not establish a formal bound.

## Current status

No tolerance has been preregistered for the existing trace set. The latest Python sweep shows up to 51.58 μV observed voltage error for the configured 10 μV empirical budget; no exceedance fraction was reported. The user-provided top-level report shows adaptive LUTs and flip-flops higher than baseline, and low-confidence estimated power also higher. The central hypothesis is therefore **not established**.

## Held-out experiment status (2026-10-10)

For a follow-up finite-sample test, the observed maximum-voltage-error target was fixed at 10 μV before held-out evaluation. Scheduler parameters were selected only on the existing nine training stimuli. Six deterministic held-out stimuli then tested different step timings, a double pulse, a triangle ramp, rapid pulses, and chirped illumination.

The selected sensitivity-triggered Python policy (`1e-14 A`, max interval 16) achieved 1.48659 μV worst held-out max error and 38.08% Python current-function evaluation reduction. The selected accumulated-proxy policy (`1e-6 V`, max interval 16) achieved 6.97410 μV and 33.00% reduction. Both had zero of 240 held-out voltage samples above 10, 50, or 100 μV. These held-out outcomes support further testing of the Python sensitivity policy against this baseline on these six traces, but do not establish generalization, a proven error bound, or a hardware benefit.

The RTL has received operand isolation around all six adaptive ionic-current modules, but it still uses the existing group-wide scheduler rather than the selected per-current Python sensitivity rule. Thus the Python outcome does not validate the current RTL scheduler. No Vivado activity, power, timing, area, or HDL-simulation result exists for the modified RTL. The combined research hypothesis remains **unestablished** until that algorithm gap, broader validation, and manual hardware evidence are addressed.
