"""Train empirical schedulers on fixed stimuli, then evaluate held-out traces."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from discrete_time_model import IONIC_NAMES, SchedulerConfig, simulate_discrete
from generate_stimuli import generate_light_suite

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "results" / "metrics" / "heldout_scheduler"
TARGET_MAX_ERROR_V = 10e-6
DURATION_S = 1.0
DT_S = 1e-4


def generate_heldout_suite(duration: float = DURATION_S, dt: float = DT_S) -> Dict[str, Dict[str, np.ndarray]]:
    """Return deterministic waveforms not used during scheduler selection."""
    if duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be positive")
    time = np.arange(0.0, duration + dt / 2.0, dt, dtype=np.float64)
    phase = np.mod(time, 0.2)
    suite = {
        "heldout_step_early": np.where(time >= 0.1173, 0.7, 0.0),
        "heldout_step_late_down": np.where(time < 0.7317, 0.85, 0.1),
        "heldout_double_pulse": np.where(
            ((time >= 0.0831) & (time < 0.1197)) |
            ((time >= 0.6423) & (time < 0.7111)), 0.65, 0.0
        ),
        "heldout_triangle_ramp": np.where(
            phase < 0.1, phase / 0.1, (0.2 - phase) / 0.1
        ) * 0.8,
        "heldout_rapid_pulse_train": np.where(
            np.mod(time, 0.037) < 0.011, 1.0, 0.0
        ),
        "heldout_chirped_light": 0.5 * (
            1.0 + np.sin(2.0 * np.pi * (0.8 * time + 4.0 * time * time))
        ),
    }
    return {
        name: {"t": time.copy(), "amplitude": np.asarray(light, dtype=np.float64)}
        for name, light in suite.items()
    }


def _stimulus(payload: Dict[str, np.ndarray]) -> Dict:
    return {"type": "custom", "time": payload["t"], "signal": payload["amplitude"]}


def _metrics(reference: Dict[str, np.ndarray], candidate: Dict[str, np.ndarray]) -> Dict[str, float]:
    # State row zero is the shared initial condition; current row i is applied
    # to the state transition that produces row i+1.
    voltage_error = candidate["V"][1:] - reference["V"][1:]
    applied_current_error = np.concatenate([
        candidate[name][:-1] - reference[name][:-1] for name in IONIC_NAMES
    ])
    return {
        "max_abs_voltage_error_V": float(np.max(np.abs(voltage_error))),
        "rms_voltage_error_V": float(np.sqrt(np.mean(np.square(voltage_error)))),
        "mae_voltage_error_V": float(np.mean(np.abs(voltage_error))),
        "samples_over_10uV": int(np.count_nonzero(np.abs(voltage_error) > 10e-6)),
        "samples_over_50uV": int(np.count_nonzero(np.abs(voltage_error) > 50e-6)),
        "samples_over_100uV": int(np.count_nonzero(np.abs(voltage_error) > 100e-6)),
        "max_abs_applied_ionic_current_error_A": float(np.max(np.abs(applied_current_error))),
        "rms_applied_ionic_current_error_A": float(np.sqrt(np.mean(np.square(applied_current_error)))),
    }


def _evaluation_count(result: Dict[str, np.ndarray]) -> int:
    count = int(result["exact_current_evaluations"][0])
    refresh_count = int(np.count_nonzero(result["refresh_mask"]))
    if count != refresh_count:
        raise RuntimeError(
            f"Python current-call counter {count} does not match refresh mask {refresh_count}"
        )
    return count


def _candidate_configs():
    configs = []
    for threshold in (1e-14, 1e-13, 1e-12, 1e-11, 1e-10, 1e-9):
        for max_interval in (4, 16):
            configs.append((
                "per_current_sensitivity",
                f"threshold={threshold:g};max_interval={max_interval}",
                SchedulerConfig(
                    mode="threshold",
                    current_error_threshold=threshold,
                    max_interval=max_interval,
                    transition_tolerance=1e-2,
                ),
            ))
    for budget in (1e-6, 3e-6, 1e-5, 3e-5):
        for max_interval in (4, 16):
            configs.append((
                "accumulated_voltage_proxy",
                f"budget={budget:g};max_interval={max_interval}",
                SchedulerConfig(
                    mode="budget",
                    voltage_error_budget=budget,
                    max_interval=max_interval,
                    transition_tolerance=1e-2,
                ),
            ))
    return configs


def run_experiments() -> tuple[Path, Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    training = generate_light_suite(duration=DURATION_S, dt=DT_S)
    heldout = generate_heldout_suite()
    configs = _candidate_configs()
    training_rows = []
    references = {
        name: simulate_discrete(
            stimulus=_stimulus(payload), t_end=DURATION_S, dt=DT_S,
            scheduler=SchedulerConfig(mode="full"),
        )
        for name, payload in training.items()
    }

    for policy, config_name, config in configs:
        for stimulus_name, payload in training.items():
            try:
                candidate = simulate_discrete(
                    stimulus=_stimulus(payload), t_end=DURATION_S, dt=DT_S,
                    scheduler=config,
                )
                metrics = _metrics(references[stimulus_name], candidate)
                evaluations = _evaluation_count(candidate)
                full_evaluations = _evaluation_count(references[stimulus_name])
                training_rows.append({
                    "policy": policy,
                    "configuration": config_name,
                    "stimulus": stimulus_name,
                    "status": "OK",
                    **metrics,
                    "python_current_function_evaluations": evaluations,
                    "full_update_python_function_evaluations": full_evaluations,
                    "python_function_evaluation_reduction_percent":
                        100.0 * (1.0 - evaluations / full_evaluations),
                    "failure_reason": "",
                })
            except (FloatingPointError, ZeroDivisionError) as error:
                training_rows.append({
                    "policy": policy,
                    "configuration": config_name,
                    "stimulus": stimulus_name,
                    "status": "FAILED",
                    "failure_reason": str(error),
                })

    eligible: Dict[str, list[dict]] = {"per_current_sensitivity": [], "accumulated_voltage_proxy": []}
    for policy in eligible:
        for config_name in dict.fromkeys(
            row["configuration"] for row in training_rows if row["policy"] == policy
        ):
            rows = [
                row for row in training_rows
                if row["policy"] == policy and row["configuration"] == config_name
            ]
            if len(rows) == len(training) and all(
                row["status"] == "OK" and row["max_abs_voltage_error_V"] <= TARGET_MAX_ERROR_V
                for row in rows
            ):
                eligible[policy].append({
                    "configuration": config_name,
                    "worst_training_max_error_V": max(row["max_abs_voltage_error_V"] for row in rows),
                    "mean_training_reduction_percent": float(np.mean([
                        row["python_function_evaluation_reduction_percent"] for row in rows
                    ])),
                })

    selected = {}
    for policy, candidates in eligible.items():
        if candidates:
            selected[policy] = max(candidates, key=lambda row: row["mean_training_reduction_percent"])
        else:
            # Keep the nearest training candidate visible, but explicitly mark
            # it ineligible rather than presenting it as target-matched.
            successful = [
                row for row in training_rows
                if row["policy"] == policy and row["status"] == "OK"
            ]
            config_groups: Dict[str, list[dict]] = {}
            for row in successful:
                config_groups.setdefault(row["configuration"], []).append(row)
            if config_groups:
                nearest = min(
                    config_groups.items(),
                    key=lambda item: max(r["max_abs_voltage_error_V"] for r in item[1]),
                )
                selected[policy] = {
                    "configuration": nearest[0],
                    "target_met_on_training": False,
                    "worst_training_max_error_V": max(
                        row["max_abs_voltage_error_V"] for row in nearest[1]
                    ),
                    "mean_training_reduction_percent": float(np.mean([
                        row["python_function_evaluation_reduction_percent"]
                        for row in nearest[1]
                    ])),
                }
        if policy in selected and "target_met_on_training" not in selected[policy]:
            selected[policy]["target_met_on_training"] = True

    csv_fields = [
        "split", "policy", "configuration", "stimulus", "status",
        "max_abs_voltage_error_V", "rms_voltage_error_V", "mae_voltage_error_V",
        "samples_over_10uV", "samples_over_50uV", "samples_over_100uV",
        "max_abs_applied_ionic_current_error_A", "rms_applied_ionic_current_error_A",
        "python_current_function_evaluations",
        "full_update_python_function_evaluations",
        "python_function_evaluation_reduction_percent", "failure_reason",
    ]
    result_path = OUTPUT_DIR / "heldout_scheduler_results.csv"
    with result_path.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=csv_fields)
        writer.writeheader()
        for row in training_rows:
            writer.writerow({"split": "training", **row})
        for policy, chosen in selected.items():
            config_name = chosen["configuration"]
            config = next(item[2] for item in configs if item[1] == config_name)
            for stimulus_name, payload in heldout.items():
                try:
                    reference = simulate_discrete(
                        stimulus=_stimulus(payload), t_end=DURATION_S, dt=DT_S,
                        scheduler=SchedulerConfig(mode="full"),
                    )
                    candidate = simulate_discrete(
                        stimulus=_stimulus(payload), t_end=DURATION_S, dt=DT_S,
                        scheduler=config,
                    )
                    metrics = _metrics(reference, candidate)
                    evaluations = _evaluation_count(candidate)
                    full_evaluations = _evaluation_count(reference)
                    writer.writerow({
                        "split": "heldout",
                        "policy": policy,
                        "configuration": config_name,
                        "stimulus": stimulus_name,
                        "status": "OK",
                        **metrics,
                        "python_current_function_evaluations": evaluations,
                        "full_update_python_function_evaluations": full_evaluations,
                        "python_function_evaluation_reduction_percent":
                            100.0 * (1.0 - evaluations / full_evaluations),
                        "failure_reason": "",
                    })
                except (FloatingPointError, ZeroDivisionError) as error:
                    writer.writerow({
                        "split": "heldout",
                        "policy": policy,
                        "configuration": config_name,
                        "stimulus": stimulus_name,
                        "status": "FAILED",
                        "failure_reason": str(error),
                    })

    plot_path = OUTPUT_DIR / "heldout_scheduler_tradeoff.png"
    with result_path.open(newline="", encoding="ascii") as stream:
        saved_rows = list(csv.DictReader(stream))
    selected_heldout = [
        row for row in saved_rows
        if row["split"] == "heldout" and row["status"] == "OK"
    ]
    plot_policies = list(selected)
    labels = ["Sensitivity trigger", "Accumulated proxy"]
    max_errors = [
        max(float(row["max_abs_voltage_error_V"]) for row in selected_heldout
            if row["policy"] == policy) * 1e6
        for policy in plot_policies
    ]
    reductions = [
        float(np.mean([
            float(row["python_function_evaluation_reduction_percent"])
            for row in selected_heldout if row["policy"] == policy
        ]))
        for policy in plot_policies
    ]
    figure, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(labels, max_errors, color=("#3c78d8", "#e69138"))
    axes[0].axhline(TARGET_MAX_ERROR_V * 1e6, color="black", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Maximum observed |voltage error| (μV)")
    axes[0].set_title("Held-out accuracy")
    axes[0].tick_params(axis="x", rotation=15)
    axes[1].bar(labels, reductions, color=("#3c78d8", "#e69138"))
    axes[1].set_ylabel("Python function-evaluation reduction (%)")
    axes[1].set_title("Held-out Python operation count")
    axes[1].tick_params(axis="x", rotation=15)
    figure.suptitle("Provisional-model held-out comparison; not hardware power")
    figure.tight_layout()
    figure.savefig(plot_path, dpi=160)
    plt.close(figure)

    metadata_path = OUTPUT_DIR / "heldout_scheduler_metadata.json"
    metadata = {
        "seed": None,
        "deterministic_waveforms": True,
        "training_suite": list(training),
        "heldout_suite": list(heldout),
        "training_not_used_as_heldout": True,
        "target_max_abs_voltage_error_V": TARGET_MAX_ERROR_V,
        "duration_s": DURATION_S,
        "dt_s": DT_S,
        "python_model_initial_state": "DEFAULT_PARAMETERS.state_vector()",
        "current_error_alignment": "currents at sample i applied to state transition producing sample i+1",
        "voltage_error_alignment": "post-initial states at samples 1..N compared",
        "voltage_exceedance_comparison": "strict absolute-error > tolerance",
        "evaluation_count_validation": "exact_current_evaluations equals refresh_mask true count",
        "full_update_evaluation_denominator": "six current terms evaluated on every model grid sample, including terminal sample",
        "candidate_configurations": [
            {"policy": policy, "configuration": name}
            for policy, name, _ in configs
        ],
        "selected_from_training_only": selected,
        "results_csv": result_path.name,
        "plot": plot_path.name,
        "limitations": [
            "Observed errors on a provisional Python model are not guaranteed bounds.",
            "Python function-evaluation reductions do not measure RTL activity or power.",
            "No biological validation is implied.",
            "If a policy has no training configuration satisfying the fixed target, its nearest candidate is labeled ineligible.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")
    return result_path, metadata_path, plot_path


if __name__ == "__main__":
    for output in run_experiments():
        print(output)
