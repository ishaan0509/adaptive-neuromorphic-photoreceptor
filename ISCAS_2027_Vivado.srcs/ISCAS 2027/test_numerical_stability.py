import numpy as np

from photoreceptor_reference import simulate_reference_model


def test_light_step_remains_finite_for_varied_steps():
    for amplitude in (0.1, 0.5, 1.0):
        result = simulate_reference_model(stimulus={"type": "step", "amplitude": amplitude, "t_on": 0.05}, t_end=0.2, dt=1e-4)
        assert np.all(np.isfinite(result["V"]))
        assert np.all(np.isfinite(result["I_total"]))


def test_dark_simulation_is_stable():
    result = simulate_reference_model(stimulus={"type": "dark"}, t_end=0.2, dt=1e-4)
    assert np.all(np.isfinite(result["V"]))
    assert len(result["time"]) > 10
