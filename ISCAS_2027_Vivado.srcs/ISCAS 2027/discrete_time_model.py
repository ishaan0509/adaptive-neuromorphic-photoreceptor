"""Explicit-Euler and selective-current models for the provisional equations.

These routines deliberately keep the six ionic-current calculations separate
from state propagation so that a scheduler can truly reuse cached currents.
The model equations/parameters still require verification against Appendix B.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np

from numerical_methods import FixedPointConfig, quantize_fixed_point
from photoreceptor_parameters import DEFAULT_PARAMETERS, PhotoreceptorParameters
from photoreceptor_reference import (
    _stimulus_lookup,
    calculate_currents,
    state_rhs,
    validate_stimulus,
)

STATE_NAMES = (
    "V", "I_photo", "m_h", "m_kv", "m_ca", "m_clca", "m_kca", "Ca_i", "Ca_s", "Ca_f",
)
IONIC_NAMES = ("I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l")
DEPENDENCIES = {
    "I_h": ("V", "m_h"),
    "I_kv": ("V", "m_kv"),
    "I_ca": ("V", "m_ca"),
    "I_clca": ("V", "m_clca", "Ca_i"),
    "I_kca": ("V", "m_kca", "Ca_i"),
    "I_l": ("V",),
}


@dataclass(frozen=True)
class SchedulerConfig:
    mode: str = "full"
    max_interval: int = 16
    periodic_interval: int = 4
    current_error_threshold: float = 1e-12
    voltage_error_budget: float = 1e-4
    transition_tolerance: float = 0.0

    def __post_init__(self) -> None:
        if self.mode not in {"full", "periodic", "threshold", "budget"}:
            raise ValueError(f"Unsupported update mode: {self.mode}")
        if self.max_interval < 1 or self.periodic_interval < 1:
            raise ValueError("Refresh intervals must be positive")
        if self.current_error_threshold < 0 or self.voltage_error_budget <= 0:
            raise ValueError("Error thresholds must be nonnegative and voltage budget positive")


def _initial_state(params: PhotoreceptorParameters) -> np.ndarray:
    initial = params.state_vector()
    return np.asarray([initial[name] for name in STATE_NAMES], dtype=np.float64)


def _state_mapping(values: np.ndarray) -> Dict[str, float]:
    return {name: float(value) for name, value in zip(STATE_NAMES, values)}


def _current_and_gradient(name: str, state: Dict[str, float], params: PhotoreceptorParameters):
    voltage = state["V"]
    calcium = state["Ca_i"]
    if name == "I_h":
        gate, conductance, reversal = state["m_h"], params.g_h, params.E_h
        current = conductance * gate * (voltage - reversal)
        return current, {"V": conductance * gate, "m_h": conductance * (voltage - reversal)}
    if name == "I_kv":
        gate, conductance, reversal = state["m_kv"], params.g_kv, params.E_k
        current = conductance * gate**3 * (voltage - reversal)
        return current, {"V": conductance * gate**3, "m_kv": 3 * conductance * gate**2 * (voltage - reversal)}
    if name == "I_ca":
        gate, conductance, reversal = state["m_ca"], params.g_ca, params.E_ca
        current = conductance * gate**3 * (voltage - reversal)
        return current, {"V": conductance * gate**3, "m_ca": 3 * conductance * gate**2 * (voltage - reversal)}
    if name in {"I_clca", "I_kca"}:
        if name == "I_clca":
            gate_name, conductance, reversal, k_ca = "m_clca", params.g_clca, params.E_cl, params.k_clca_ca
        else:
            gate_name, conductance, reversal, k_ca = "m_kca", params.g_kca, params.E_k, params.k_kca_ca
        gate = state[gate_name]
        denominator = calcium + k_ca
        if denominator == 0:
            raise ZeroDivisionError(f"Calcium activation denominator is zero for {name}")
        activation = calcium / denominator
        driving_force = voltage - reversal
        current = conductance * gate * activation * driving_force
        derivative_ca = k_ca / (denominator * denominator)
        return current, {
            "V": conductance * gate * activation,
            gate_name: conductance * activation * driving_force,
            "Ca_i": conductance * gate * derivative_ca * driving_force,
        }
    if name == "I_l":
        current = params.g_l * (voltage - params.E_l)
        return current, {"V": params.g_l}
    raise KeyError(name)


def _make_time_grid(t_end: float, dt: float) -> np.ndarray:
    if not np.isfinite(t_end) or t_end <= 0 or not np.isfinite(dt) or dt <= 0:
        raise ValueError("t_end and dt must be finite and positive")
    count = int(np.floor(t_end / dt))
    times = dt * np.arange(count + 1, dtype=np.float64)
    if times[-1] < t_end and not np.isclose(times[-1], t_end):
        times = np.append(times, t_end)
    else:
        times[-1] = t_end
    return times


def _assemble_output(times, states, stored_currents, light_values, params):
    output = {"time": times}
    for idx, name in enumerate(STATE_NAMES):
        output[name] = states[:, idx]
    for name in ("I_photo", *IONIC_NAMES):
        output[name] = stored_currents[name]
    output["I_total"] = stored_currents["I_photo"].copy()
    for name in IONIC_NAMES:
        output["I_total"] += stored_currents[name]
    output["light"] = light_values
    return output


def simulate_discrete(
    parameters: Optional[PhotoreceptorParameters] = None,
    stimulus: Optional[Dict] = None,
    t_end: Optional[float] = None,
    dt: Optional[float] = None,
    scheduler: Optional[SchedulerConfig] = None,
    fixed_point: Optional[FixedPointConfig] = None,
) -> Dict[str, np.ndarray]:
    """Run Euler state updates with cached currents under the selected scheduler.

    `budget` uses a first-order sensitivity estimate of stale-current error. It
    is empirical, not a conservative mathematical bound.
    """
    params = parameters or DEFAULT_PARAMETERS
    stim = validate_stimulus(stimulus or {"type": "dark"})
    stop_time = params.t_end if t_end is None else t_end
    step_size = params.dt if dt is None else dt
    times = _make_time_grid(stop_time, step_size)
    config = scheduler or SchedulerConfig()
    states = np.zeros((len(times), len(STATE_NAMES)), dtype=np.float64)
    states[0] = _initial_state(params)
    lights = np.asarray([_stimulus_lookup(stim, time) for time in times], dtype=np.float64)
    currents_out = {name: np.zeros(len(times), dtype=np.float64) for name in ("I_photo", *IONIC_NAMES)}

    held = {name: 0.0 for name in IONIC_NAMES}
    snapshots: Dict[str, Dict[str, float]] = {}
    gradients: Dict[str, Dict[str, float]] = {}
    ages = {name: 0 for name in IONIC_NAMES}
    initialized = False
    estimated_voltage_error = 0.0
    budget_history = np.zeros(len(times), dtype=np.float64)
    refresh_mask = np.zeros((len(times), len(IONIC_NAMES)), dtype=np.bool_)
    exact_current_evaluations = 0
    full_refresh_events = 0
    transient_refresh_events = 0
    budget_refresh_events = 0

    for index, time in enumerate(times):
        state = _state_mapping(states[index])
        light = lights[index]
        photo_current = params.g_photo * light
        transient = index > 0 and abs(lights[index] - lights[index - 1]) > config.transition_tolerance

        estimated_stale_error = {}
        for name in IONIC_NAMES:
            if name not in snapshots:
                estimated_stale_error[name] = float("inf")
            else:
                delta = {dep: state[dep] - snapshots[name][dep] for dep in DEPENDENCIES[name]}
                estimated_stale_error[name] = sum(
                    abs(gradients[name][dep] * delta[dep]) for dep in delta
                )

        refresh = {}
        for name in IONIC_NAMES:
            periodic_due = ages[name] >= config.periodic_interval
            safety_due = ages[name] >= config.max_interval
            if config.mode == "full":
                should_refresh = True
            elif config.mode == "periodic":
                should_refresh = periodic_due or safety_due
            elif config.mode == "threshold":
                should_refresh = estimated_stale_error[name] >= config.current_error_threshold or safety_due
            else:
                should_refresh = safety_due
            refresh[name] = should_refresh or transient or not initialized

        if config.mode == "budget" and initialized and not transient:
            step = times[index] - times[index - 1] if index else 0.0
            estimated_voltage_increment = (
                step / params.C_m * sum(estimated_stale_error.values())
                if np.isfinite(sum(estimated_stale_error.values()))
                else float("inf")
            )
            if estimated_voltage_error + estimated_voltage_increment >= config.voltage_error_budget:
                refresh = {name: True for name in IONIC_NAMES}
                budget_refresh_events += 1
                estimated_voltage_error = 0.0
            else:
                estimated_voltage_error += estimated_voltage_increment

        refreshed_count = 0
        for current_index, name in enumerate(IONIC_NAMES):
            if refresh[name]:
                value, gradient = _current_and_gradient(name, state, params)
                if not np.isfinite(value) or not all(np.isfinite(v) for v in gradient.values()):
                    raise FloatingPointError(f"Non-finite {name} or sensitivity estimate at t={time:g}")
                held[name] = value
                snapshots[name] = {dep: state[dep] for dep in DEPENDENCIES[name]}
                gradients[name] = gradient
                ages[name] = 0
                refresh_mask[index, current_index] = True
                exact_current_evaluations += 1
                refreshed_count += 1
            else:
                ages[name] += 1
        if refreshed_count == len(IONIC_NAMES):
            full_refresh_events += 1
        if transient and refreshed_count:
            transient_refresh_events += 1
        initialized = True

        currents_out["I_photo"][index] = photo_current
        for name in IONIC_NAMES:
            currents_out[name][index] = held[name]
        budget_history[index] = estimated_voltage_error

        if index < len(times) - 1:
            used_currents = dict(held)
            used_currents["I_photo"] = photo_current
            used_currents["I_total"] = photo_current + sum(held.values())
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                derivative = state_rhs(float(time), states[index], stim, params, currents=used_currents)
                next_state = states[index] + (times[index + 1] - time) * derivative
            if fixed_point is not None:
                next_state = np.asarray([
                    quantize_fixed_point(float(value), fixed_point) / fixed_point.scale
                    for value in next_state
                ])
            next_state = np.asarray(next_state, dtype=np.float64)
            if not np.all(np.isfinite(next_state)):
                raise FloatingPointError(f"Non-finite state at t={time:g}")
            if abs(next_state[0]) > 1.0:
                raise FloatingPointError(
                    f"Voltage exceeded the 1 V numerical runaway guard at t={time:g}; "
                    "this is a numerical safeguard, not a physiological limit"
                )
            states[index + 1] = next_state

    output = _assemble_output(times, states, currents_out, lights, params)
    output.update({
        "estimated_voltage_error": budget_history,
        "refresh_mask": refresh_mask,
        "exact_current_evaluations": np.asarray([exact_current_evaluations]),
        "full_refresh_events": np.asarray([full_refresh_events]),
        "transient_refresh_events": np.asarray([transient_refresh_events]),
        "budget_refresh_events": np.asarray([budget_refresh_events]),
    })
    return output
