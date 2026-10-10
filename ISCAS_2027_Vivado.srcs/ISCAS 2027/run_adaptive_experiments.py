import csv
from pathlib import Path
from typing import Dict

import numpy as np

from discrete_time_model import IONIC_NAMES, SchedulerConfig, simulate_discrete
from error_analysis import summarize_experiment_error
from generate_stimuli import generate_light_suite

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results" / "metrics"

SCHEDULERS = {
    "full": SchedulerConfig(mode="full"),
    "periodic": SchedulerConfig(mode="periodic", periodic_interval=4, max_interval=16),
    "threshold": SchedulerConfig(mode="threshold", current_error_threshold=1e-12, max_interval=16),
    "budget_empirical": SchedulerConfig(
        mode="budget",
        voltage_error_budget=1e-5,
        max_interval=16,
        transition_tolerance=1e-2,
    ),
}


def _custom_stimulus(payload: Dict[str, np.ndarray]) -> Dict:
    return {"type": "custom", "time": payload["t"], "signal": payload["amplitude"]}


def run_experiments(duration: float = 1.0, dt: float = 1e-4) -> Path:
    suite = generate_light_suite(duration=duration, dt=dt)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "adaptive_experiments.csv"
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "stimulus",
            "scheduler",
            "status",
            "failure_reason",
            "max_abs_voltage_error_vs_full_euler_V",
            "rms_voltage_error_vs_full_euler_V",
            "max_abs_ionic_current_error_vs_full_euler_A",
            "ionic_current_evaluations",
            "ionic_current_evaluations_avoided_percent",
            "all-current_refresh_events",
            "transient_refresh_events",
            "budget_refresh_events",
            "maximum_estimated_voltage_error_V",
        ])
        for stimulus_name, payload in suite.items():
            stimulus = _custom_stimulus(payload)
            baseline = simulate_discrete(stimulus=stimulus, t_end=duration, dt=dt, scheduler=SCHEDULERS["full"])
            max_evaluations = len(baseline["time"]) * len(IONIC_NAMES)
            for scheduler_name, scheduler in SCHEDULERS.items():
                try:
                    candidate = baseline if scheduler_name == "full" else simulate_discrete(
                        stimulus=stimulus, t_end=duration, dt=dt, scheduler=scheduler
                    )
                except FloatingPointError as error:
                    writer.writerow([stimulus_name, scheduler_name, "UNSTABLE", str(error)] + [""] * 9)
                    print(f"{stimulus_name}/{scheduler_name}: UNSTABLE: {error}")
                    continue
                metrics = summarize_experiment_error(
                    baseline["V"], candidate["V"], baseline["I_total"], candidate["I_total"]
                )
                current_error = np.concatenate([
                    candidate[name] - baseline[name] for name in IONIC_NAMES
                ])
                evaluations = int(candidate["exact_current_evaluations"][0])
                avoided_percent = 100.0 * (1.0 - evaluations / max_evaluations)
                row = [
                    stimulus_name,
                    scheduler_name,
                    "OK",
                    "",
                    metrics["max_voltage_error"],
                    metrics["rms_voltage_error"],
                    float(np.max(np.abs(current_error))),
                    evaluations,
                    avoided_percent,
                    int(candidate["full_refresh_events"][0]),
                    int(candidate["transient_refresh_events"][0]),
                    int(candidate["budget_refresh_events"][0]),
                    float(np.max(candidate["estimated_voltage_error"])),
                ]
                writer.writerow(row)
                print(
                    f"{stimulus_name}/{scheduler_name}: "
                    f"max|dV|={metrics['max_voltage_error']:.6e} V, "
                    f"ionic evaluations avoided={avoided_percent:.1f}%"
                )
    return output_path


if __name__ == "__main__":
    print(f"Saved adaptive experiment metrics: {run_experiments()}")
