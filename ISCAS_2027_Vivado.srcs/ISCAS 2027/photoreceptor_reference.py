import csv
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from scipy.integrate import solve_ivp

from photoreceptor_parameters import DEFAULT_PARAMETERS, PhotoreceptorParameters
from numerical_methods import stable_sigmoid

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "reference_traces"
RESULTS_DIR = BASE_DIR / "results"


def sigmoid(v: float, v_half: float, k: float) -> float:
    if k <= 0:
        raise ValueError("sigmoid slope parameter k must be positive")
    return stable_sigmoid((v - v_half) / k)


def validate_stimulus(stimulus: Dict) -> Dict:
    stimulus_type = stimulus.get("type")
    if stimulus_type not in {"dark", "step", "pulse", "ramp", "custom"}:
        raise ValueError(f"Unsupported stimulus type: {stimulus_type!r}")
    if stimulus_type == "custom":
        if "time" not in stimulus or "signal" not in stimulus:
            raise ValueError("custom stimulus requires both 'time' and 'signal'")
        time = np.asarray(stimulus["time"], dtype=np.float64)
        signal = np.asarray(stimulus["signal"], dtype=np.float64)
        if time.ndim != 1 or signal.ndim != 1 or len(time) == 0 or len(time) != len(signal):
            raise ValueError("custom stimulus time and signal must be non-empty, equal-length 1D arrays")
        if not np.all(np.isfinite(time)) or not np.all(np.isfinite(signal)) or np.any(np.diff(time) <= 0):
            raise ValueError("custom stimulus values must be finite and time must be strictly increasing")
        return {**stimulus, "time": time, "signal": signal}
    return stimulus


def _stimulus_lookup(stimulus: Dict, t: float) -> float:
    stimulus_type = stimulus.get("type")
    if stimulus_type == "dark":
        return 0.0
    if stimulus_type == "step":
        amp = float(stimulus.get("amplitude", 0.0))
        return amp if t >= float(stimulus.get("t_on", 0.0)) else 0.0
    if stimulus_type == "pulse":
        amp = float(stimulus.get("amplitude", 0.0))
        t_on = float(stimulus.get("t_on", 0.0))
        t_off = float(stimulus.get("t_off", t_on))
        if t_off < t_on:
            raise ValueError("pulse t_off must be greater than or equal to t_on")
        return amp if t_on <= t <= t_off else 0.0
    if stimulus_type == "ramp":
        t_start = float(stimulus.get("t_start", 0.0))
        duration = max(float(stimulus.get("duration", 0.1)), 1e-9)
        amp = float(stimulus.get("amplitude", 0.0))
        segment = (t - t_start) / duration
        if t < t_start:
            return 0.0
        if t > t_start + duration:
            return amp
        return amp * segment
    if stimulus_type == "custom":
        time = np.asarray(stimulus["time"], dtype=np.float64)
        signal = np.asarray(stimulus["signal"], dtype=np.float64)
        idx = np.searchsorted(time, t, side="right") - 1
        idx = max(0, min(len(signal) - 1, idx))
        return float(signal[idx])
    raise ValueError(f"Unsupported stimulus type: {stimulus_type!r}")


def calculate_currents(V: float, state: Dict[str, float], params: PhotoreceptorParameters, light: float) -> Dict[str, float]:
    I_photo = params.g_photo * light
    m_h = state["m_h"]
    m_kv = state["m_kv"]
    m_ca = state["m_ca"]
    m_clca = state["m_clca"]
    m_kca = state["m_kca"]
    Ca_i = state["Ca_i"]

    I_h = params.g_h * m_h * (V - params.E_h)
    I_kv = params.g_kv * (m_kv ** 3) * (V - params.E_k)
    I_ca = params.g_ca * (m_ca ** 3) * (V - params.E_ca)
    clca_denom = Ca_i + params.k_clca_ca
    kca_denom = Ca_i + params.k_kca_ca
    if clca_denom == 0 or kca_denom == 0:
        raise ZeroDivisionError("Calcium-current activation denominator is zero")
    I_clca = params.g_clca * m_clca * (Ca_i / clca_denom) * (V - params.E_cl)
    I_kca = params.g_kca * m_kca * (Ca_i / kca_denom) * (V - params.E_k)
    I_l = params.g_l * (V - params.E_l)
    I_total = I_photo + I_h + I_kv + I_ca + I_clca + I_kca + I_l
    return {
        "I_photo": I_photo,
        "I_h": I_h,
        "I_kv": I_kv,
        "I_ca": I_ca,
        "I_clca": I_clca,
        "I_kca": I_kca,
        "I_l": I_l,
        "I_total": I_total,
    }


def state_rhs(
    t: float,
    y: np.ndarray,
    stimulus: Dict,
    params: PhotoreceptorParameters,
    currents: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    V = float(y[0])
    state = {
        "V": V,
        "I_photo": float(y[1]),
        "m_h": float(y[2]),
        "m_kv": float(y[3]),
        "m_ca": float(y[4]),
        "m_clca": float(y[5]),
        "m_kca": float(y[6]),
        "Ca_i": float(y[7]),
        "Ca_s": float(y[8]),
        "Ca_f": float(y[9]),
    }

    light = _stimulus_lookup(stimulus, t)
    active_currents = currents or calculate_currents(V, state, params, light)

    m_h_inf = sigmoid(V, params.v_half_h, params.k_h)
    m_kv_inf = sigmoid(V, params.v_half_kv, params.k_kv)
    m_ca_inf = sigmoid(V, params.v_half_ca, params.k_ca)
    m_clca_inf = sigmoid(V, params.v_half_clca, params.k_clca)
    m_kca_inf = sigmoid(V, params.v_half_kca, params.k_kca)

    dV = -(active_currents["I_total"]) / params.C_m
    dI_photo = 0.0
    dm_h = (m_h_inf - state["m_h"]) / params.tau_h
    dm_kv = (m_kv_inf - state["m_kv"]) / params.tau_kv
    dm_ca = (m_ca_inf - state["m_ca"]) / params.tau_ca
    dm_clca = (m_clca_inf - state["m_clca"]) / params.tau_clca
    dm_kca = (m_kca_inf - state["m_kca"]) / params.tau_kca

    Ca_i = state["Ca_i"]
    Ca_s = state["Ca_s"]
    Ca_f = state["Ca_f"]
    dCa_i = -params.alpha_ca * active_currents["I_ca"] - params.beta_ca * (Ca_i - params.ca_rest)
    dCa_s = 0.5 * (Ca_i - Ca_s)
    dCa_f = 0.25 * (Ca_s - Ca_f)

    return np.array([
        dV,
        dI_photo,
        dm_h,
        dm_kv,
        dm_ca,
        dm_clca,
        dm_kca,
        dCa_i,
        dCa_s,
        dCa_f,
    ], dtype=np.float64)


def simulate_reference_model(
    parameters: Optional[PhotoreceptorParameters] = None,
    stimulus: Optional[Dict] = None,
    t_end: Optional[float] = None,
    dt: Optional[float] = None,
) -> Dict[str, np.ndarray]:
    params = parameters or DEFAULT_PARAMETERS
    stim = validate_stimulus(stimulus or {"type": "dark"})
    if t_end is not None:
        params = PhotoreceptorParameters(**{**params.as_dict(), "t_end": t_end})
    if dt is not None:
        params = PhotoreceptorParameters(**{**params.as_dict(), "dt": dt})

    if params.t_end <= 0 or params.dt <= 0:
        raise ValueError("t_end and dt must be positive")
    count = int(np.floor(params.t_end / params.dt))
    t_eval = params.dt * np.arange(count + 1, dtype=np.float64)
    if t_eval[-1] < params.t_end and not np.isclose(t_eval[-1], params.t_end):
        t_eval = np.append(t_eval, params.t_end)
    else:
        t_eval[-1] = params.t_end
    y0 = np.array([
        params.v_init,
        params.i_photo_init,
        params.m_h_init,
        params.m_kv_init,
        params.m_ca_init,
        params.m_clca_init,
        params.m_kca_init,
        params.ca_i_init,
        params.ca_s_init,
        params.ca_f_init,
    ], dtype=np.float64)

    def rhs_func(t, y):
        return state_rhs(float(t), y, stim, params)

    sol = solve_ivp(
        rhs_func,
        (0.0, params.t_end),
        y0,
        t_eval=t_eval,
        method=params.solver,
        rtol=params.rtol,
        atol=params.atol,
        max_step=params.max_step,
    )

    if not sol.success:
        raise RuntimeError(f"Reference solver failed: {sol.message}")
    if sol.y.shape[1] != len(t_eval) or not np.all(np.isfinite(sol.y)):
        raise FloatingPointError("Reference solver returned incomplete or non-finite state values")

    state_table = sol.y.T
    output: Dict[str, np.ndarray] = {"time": sol.t}
    for idx, key in enumerate([
        "V",
        "I_photo",
        "m_h",
        "m_kv",
        "m_ca",
        "m_clca",
        "m_kca",
        "Ca_i",
        "Ca_s",
        "Ca_f",
    ]):
        output[key] = state_table[:, idx]

    currents = []
    for i, V in enumerate(output["V"]):
        s = {
            "V": float(V),
            "I_photo": float(output["I_photo"][i]),
            "m_h": float(output["m_h"][i]),
            "m_kv": float(output["m_kv"][i]),
            "m_ca": float(output["m_ca"][i]),
            "m_clca": float(output["m_clca"][i]),
            "m_kca": float(output["m_kca"][i]),
            "Ca_i": float(output["Ca_i"][i]),
            "Ca_s": float(output["Ca_s"][i]),
            "Ca_f": float(output["Ca_f"][i]),
        }
        currents.append(calculate_currents(float(V), s, params, _stimulus_lookup(stim, sol.t[i])))

    for key in ["I_photo", "I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l", "I_total"]:
        output[key] = np.asarray([entry[key] for entry in currents], dtype=np.float64)
    output["light"] = np.asarray([_stimulus_lookup(stim, time) for time in sol.t], dtype=np.float64)

    return output


def save_reference_trace(output: Dict[str, np.ndarray], filename: str = "reference_trace.csv") -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        header = ["time", "light", "V", "I_photo", "m_h", "m_kv", "m_ca", "m_clca", "m_kca", "Ca_i", "Ca_s", "Ca_f",
                  "I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l", "I_total"]
        writer.writerow(header)
        for idx in range(len(output["time"])):
            row = [output["time"][idx], output["light"][idx]]
            for key in ["V", "I_photo", "m_h", "m_kv", "m_ca", "m_clca", "m_kca", "Ca_i", "Ca_s", "Ca_f",
                        "I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l", "I_total"]:
                row.append(float(output[key][idx]))
            writer.writerow(row)
    return path


def main() -> None:
    sim = simulate_reference_model(stimulus={"type": "step", "amplitude": 1.0, "t_on": 0.2})
    save_reference_trace(sim, "reference_trace.csv")
    print(f"Saved reference trace to: {DATA_DIR / 'reference_trace.csv'}")


if __name__ == "__main__":
    main()
