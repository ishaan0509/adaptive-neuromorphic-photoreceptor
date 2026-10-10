import numpy as np

from photoreceptor_reference import simulate_reference_model


def test_reference_model_runs_and_returns_finite_values():
    result = simulate_reference_model(stimulus={"type": "step", "amplitude": 1.0, "t_on": 0.1}, t_end=0.25, dt=1e-4)
    assert len(result["time"]) > 0
    assert np.all(np.isfinite(result["V"]))
    assert np.all(np.isfinite(result["I_total"]))
    assert np.isfinite(np.max(result["V"]))


def test_reference_model_regression_baseline():
    result = simulate_reference_model(stimulus={"type": "dark"}, t_end=0.1, dt=1e-4)
    assert result["V"][0] < 0.0
    assert np.all(np.isfinite(result["V"]))
