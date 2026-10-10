import numpy as np

from discrete_time_model import SchedulerConfig, simulate_discrete
from numerical_methods import FixedPointConfig, decode_twos_complement, fixed_point_to_float, quantize_fixed_point


def _step_stimulus():
    return {"type": "step", "amplitude": 0.2, "t_on": 0.005}


def test_full_euler_updates_all_ionic_currents_each_sample():
    result = simulate_discrete(
        stimulus=_step_stimulus(),
        t_end=0.02,
        dt=1e-4,
        scheduler=SchedulerConfig(mode="full"),
    )
    assert result["exact_current_evaluations"][0] == len(result["time"]) * 6
    assert np.all(np.isfinite(result["V"]))
    assert np.all(np.isfinite(result["I_total"]))


def test_periodic_scheduler_reuses_currents_and_forces_step_refresh():
    result = simulate_discrete(
        stimulus=_step_stimulus(),
        t_end=0.02,
        dt=1e-4,
        scheduler=SchedulerConfig(mode="periodic", periodic_interval=5, max_interval=10),
    )
    assert result["exact_current_evaluations"][0] < len(result["time"]) * 6
    assert result["transient_refresh_events"][0] >= 1
    assert np.all(np.isfinite(result["V"]))


def test_error_budget_estimator_is_nonnegative_and_safety_refresh_is_enforced():
    result = simulate_discrete(
        stimulus=_step_stimulus(),
        t_end=0.02,
        dt=1e-4,
        scheduler=SchedulerConfig(
            mode="budget",
            voltage_error_budget=1e-12,
            max_interval=4,
            transition_tolerance=1e-2,
        ),
    )
    assert np.all(result["estimated_voltage_error"] >= 0)
    assert result["budget_refresh_events"][0] > 0
    assert result["exact_current_evaluations"][0] <= len(result["time"]) * 6


def test_signed_fixed_point_range_and_twos_complement_decode():
    config = FixedPointConfig(width=16, fractional_bits=8)
    assert config.raw_min == -32768
    assert config.raw_max == 32767
    assert fixed_point_to_float(quantize_fixed_point(-128.0, config), config) == -128.0
    assert decode_twos_complement(0xFF00, config) == -1.0
    assert decode_twos_complement(0x0100, config) == 1.0
