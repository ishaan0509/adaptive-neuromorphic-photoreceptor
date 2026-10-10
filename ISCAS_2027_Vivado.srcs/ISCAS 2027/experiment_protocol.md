# Experiment Protocol

This protocol defines the validation flow for the reference model.

1. Generate a parameterized light suite using deterministic amplitudes and durations.
2. Run the scientific model across dark, step, pulse, ramp, and periodic stimuli.
3. Save time-series traces and summary metrics to `data/` and `results/`.
4. Validate that all traces remain finite and numerically stable.
5. Compare model outputs for step changes and steady-state operation before moving to the adaptive scheduler.
