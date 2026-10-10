import csv
from pathlib import Path
from typing import Dict

import numpy as np

from discrete_time_model import SchedulerConfig, simulate_discrete
from error_analysis import summarize_experiment_error
from generate_stimuli import generate_light_suite
from numerical_methods import FixedPointConfig
from photoreceptor_reference import simulate_reference_model

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results" / "metrics"


def _as_custom_stimulus(payload: Dict[str, np.ndarray]) -> Dict:
    return {"type": "custom", "time": payload["t"], "signal": payload["amplitude"]}


def compare_model_traces(reference: Dict[str, np.ndarray], candidate: Dict[str, np.ndarray]) -> Dict[str, float]:
    if not np.array_equal(reference["time"], candidate["time"]):
        raise ValueError("Model traces must have exactly aligned time samples before comparison")
    metrics = summarize_experiment_error(
        reference["V"], candidate["V"], reference["I_total"], candidate["I_total"]
    )
    for name in ("I_photo", "I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l"):
        error = candidate[name] - reference[name]
        metrics[f"{name}_max_abs_error"] = float(np.max(np.abs(error)))
        metrics[f"{name}_rms_error"] = float(np.sqrt(np.mean(error**2)))
    for name in ("m_h", "m_kv", "m_ca", "m_clca", "m_kca", "Ca_i", "Ca_s", "Ca_f"):
        error = candidate[name] - reference[name]
        metrics[f"{name}_max_abs_error"] = float(np.max(np.abs(error)))
        metrics[f"{name}_rms_error"] = float(np.sqrt(np.mean(error**2)))
    return metrics


def run_comparisons(duration: float = 1.0, dt: float = 1e-4) -> Path:
    suite = generate_light_suite(duration=duration, dt=dt)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "model_comparison_metrics.csv"
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "stimulus",
            "max_abs_voltage_discretization_error_V",
            "rms_voltage_discretization_error_V",
            "max_abs_voltage_state_quantization_error_V",
            "rms_voltage_state_quantization_error_V",
            "max_abs_total_current_discretization_error_A",
            "max_abs_total_current_state_quantization_error_A",
        ])
        for name, payload in suite.items():
            stimulus = _as_custom_stimulus(payload)
            continuous = simulate_reference_model(stimulus=stimulus, t_end=duration, dt=dt)
            euler = simulate_discrete(stimulus=stimulus, t_end=duration, dt=dt)
            quantized = simulate_discrete(
                stimulus=stimulus,
                t_end=duration,
                dt=dt,
                fixed_point=FixedPointConfig(width=32, fractional_bits=16),
            )
            euler_metrics = compare_model_traces(continuous, euler)
            quant_metrics = compare_model_traces(euler, quantized)
            writer.writerow([
                name,
                euler_metrics["max_voltage_error"],
                euler_metrics["rms_voltage_error"],
                quant_metrics["max_voltage_error"],
                quant_metrics["rms_voltage_error"],
                euler_metrics["max_current_error"],
                quant_metrics["max_current_error"],
            ])
            print(
                f"{name}: Euler max|dV|={euler_metrics['max_voltage_error']:.6e} V, "
                f"state-quantized max|dV|={quant_metrics['max_voltage_error']:.6e} V"
            )
    return output_path


def run_step_size_convergence(duration: float = 0.2) -> Path:
    """Compare the provisional Euler model with a tighter-tolerance solver trace."""
    from dataclasses import replace

    from photoreceptor_parameters import DEFAULT_PARAMETERS

    stimulus = {"type": "step", "amplitude": 0.2, "t_on": 0.05}
    reference_dt = 2.5e-5
    parameters = replace(
        DEFAULT_PARAMETERS,
        dt=reference_dt,
        t_end=duration,
        rtol=1e-10,
        atol=1e-12,
        max_step=reference_dt,
    )
    reference = simulate_reference_model(parameters=parameters, stimulus=stimulus)
    output_path = RESULTS_DIR / "numerical_convergence.csv"
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "euler_dt_s",
            "max_abs_voltage_error_vs_fine_solver_V",
            "rms_voltage_error_vs_fine_solver_V",
            "max_abs_current_error_vs_fine_solver_A",
            "all_states_finite",
        ])
        for step in (2e-4, 1e-4, 5e-5):
            discrete = simulate_discrete(
                parameters=replace(parameters, dt=step),
                stimulus=stimulus,
                t_end=duration,
                dt=step,
            )
            ref_voltage = np.interp(discrete["time"], reference["time"], reference["V"])
            ref_current = np.interp(discrete["time"], reference["time"], reference["I_total"])
            voltage_error = discrete["V"] - ref_voltage
            current_error = discrete["I_total"] - ref_current
            writer.writerow([
                step,
                float(np.max(np.abs(voltage_error))),
                float(np.sqrt(np.mean(voltage_error**2))),
                float(np.max(np.abs(current_error))),
                bool(np.all(np.isfinite(discrete["V"]))),
            ])
    return output_path


if __name__ == "__main__":
    print(f"Saved comparison metrics: {run_comparisons()}")
    print(f"Saved numerical convergence metrics: {run_step_size_convergence()}")
