"""Sweep empirical current-refresh budgets and max ages on fixed stimuli."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from discrete_time_model import IONIC_NAMES, SchedulerConfig, simulate_discrete
from generate_stimuli import generate_light_suite

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "results" / "metrics" / "area_followup_python"

BUDGETS_V = (1e-6, 1e-5, 1e-4)
MAX_INTERVALS = (4, 16)
VOLTAGE_TOLERANCES_V = (1e-5, 5e-5, 1e-4)


def run_budget_sweep(duration: float = 1.0, dt: float = 1e-4) -> Path:
    suite = generate_light_suite(duration=duration, dt=dt)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "empirical_budget_sweep.csv"
    fields = [
        "stimulus",
        "status",
        "budget_trigger_V",
        "max_interval_samples",
        "accepted_samples",
        "max_abs_voltage_error_V",
        "rms_voltage_error_V",
        "mae_voltage_error_V",
        "max_abs_current_error_A",
        "ionic_current_function_evaluations",
        "full_update_function_evaluations",
        "python_function_evaluation_reduction_percent",
        "samples_over_10uV",
        "samples_over_50uV",
        "samples_over_100uV",
        "failure_reason",
    ]

    with output_path.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for stimulus_name, stimulus_data in suite.items():
            stimulus = {"type": "custom", "time": stimulus_data["t"], "signal": stimulus_data["amplitude"]}
            baseline = simulate_discrete(
                stimulus=stimulus, t_end=duration, dt=dt,
                scheduler=SchedulerConfig(mode="full"),
            )
            baseline_evaluations = len(baseline["time"]) * len(IONIC_NAMES)
            for budget in BUDGETS_V:
                for max_interval in MAX_INTERVALS:
                    config = SchedulerConfig(
                        mode="budget",
                        voltage_error_budget=budget,
                        max_interval=max_interval,
                        transition_tolerance=1e-2,
                    )
                    try:
                        candidate = simulate_discrete(
                            stimulus=stimulus, t_end=duration, dt=dt, scheduler=config,
                        )
                    except FloatingPointError as error:
                        writer.writerow({
                            "stimulus": stimulus_name,
                            "status": "UNSTABLE",
                            "budget_trigger_V": budget,
                            "max_interval_samples": max_interval,
                            "accepted_samples": len(baseline["time"]) - 1,
                            "failure_reason": str(error),
                        })
                        continue

                    voltage_error = np.abs(candidate["V"][1:] - baseline["V"][1:])
                    current_error = np.concatenate([
                        candidate[name][:-1] - baseline[name][:-1] for name in IONIC_NAMES
                    ])
                    evaluations = int(candidate["exact_current_evaluations"][0])
                    writer.writerow({
                        "stimulus": stimulus_name,
                        "status": "OK",
                        "budget_trigger_V": budget,
                        "max_interval_samples": max_interval,
                        "accepted_samples": len(baseline["time"]) - 1,
                        "max_abs_voltage_error_V": float(np.max(voltage_error)),
                        "rms_voltage_error_V": float(np.sqrt(np.mean(voltage_error**2))),
                        "mae_voltage_error_V": float(np.mean(voltage_error)),
                        "max_abs_current_error_A": float(np.max(np.abs(current_error))),
                        "ionic_current_function_evaluations": evaluations,
                        "full_update_function_evaluations": baseline_evaluations,
                        "python_function_evaluation_reduction_percent": 100.0 * (
                            1.0 - evaluations / baseline_evaluations
                        ),
                        "samples_over_10uV": int(np.count_nonzero(voltage_error > VOLTAGE_TOLERANCES_V[0])),
                        "samples_over_50uV": int(np.count_nonzero(voltage_error > VOLTAGE_TOLERANCES_V[1])),
                        "samples_over_100uV": int(np.count_nonzero(voltage_error > VOLTAGE_TOLERANCES_V[2])),
                        "failure_reason": "",
                    })
    return output_path


if __name__ == "__main__":
    print(run_budget_sweep())
