import numpy as np
import pytest

from discrete_time_model import IONIC_NAMES, SchedulerConfig, simulate_discrete
from run_heldout_scheduler_experiments import (
    _evaluation_count,
    _metrics,
    generate_heldout_suite,
)


def test_heldout_suite_is_deterministic_and_has_distinct_scenarios():
    first = generate_heldout_suite(duration=0.02, dt=1e-4)
    second = generate_heldout_suite(duration=0.02, dt=1e-4)
    assert len(first) == 6
    assert list(first) == list(second)
    for name in first:
        np.testing.assert_array_equal(first[name]["t"], second[name]["t"])
        np.testing.assert_array_equal(first[name]["amplitude"], second[name]["amplitude"])
        assert np.all(np.isfinite(first[name]["amplitude"]))


def test_current_evaluation_count_matches_actually_refreshed_python_terms():
    result = simulate_discrete(
        stimulus={"type": "dark"},
        t_end=0.003,
        dt=0.001,
        scheduler=SchedulerConfig(mode="periodic", periodic_interval=3, max_interval=3),
    )
    assert result["exact_current_evaluations"][0] == _evaluation_count(result)
    assert result["exact_current_evaluations"][0] < len(result["time"]) * len(IONIC_NAMES)


def test_error_metrics_align_post_initial_voltage_and_applied_currents():
    reference = {
        "V": np.array([0.0, 1.0, 2.0]),
        **{name: np.array([0.0, 2.0, 100.0]) for name in IONIC_NAMES},
    }
    candidate = {
        "V": np.array([0.0, 1.00002, 2.00004]),
        **{name: np.array([0.0, 2.00001, 1000.0]) for name in IONIC_NAMES},
    }
    metrics = _metrics(reference, candidate)
    assert metrics["max_abs_voltage_error_V"] == pytest.approx(4e-5)
    assert metrics["mae_voltage_error_V"] == pytest.approx(3e-5)
    assert metrics["max_abs_applied_ionic_current_error_A"] == pytest.approx(1e-5)
    assert metrics["samples_over_10uV"] == 2
