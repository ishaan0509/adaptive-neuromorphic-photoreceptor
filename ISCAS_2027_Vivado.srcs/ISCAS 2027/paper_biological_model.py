"""Double-precision implementation of the legible Shah et al. Appendix B model.

The paper stimulus J_hv(t) and the calcium reversal-potential logarithm base
are not specified. Both are therefore explicit caller inputs; this module
does not assign a paper stimulus or claim biological validation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from math import exp, expm1, isfinite, log, log10
from typing import Literal

import numpy as np

from paper_biological_parameters import INITIAL_STATE, PAPER_PARAMETERS, PaperParameters


State = Mapping[str, float]
LogBase = Literal["e", "10"]
STATE_NAMES = tuple(INITIAL_STATE)
MEMBRANE_CURRENT_NAMES = (
    "I_photo_pA",
    "I_h_pA",
    "I_Kv_pA",
    "I_Ca_pA",
    "I_ClCa_pA",
    "I_KCa_pA",
    "I_L_pA",
    "I_ex_pA",
    "I_ex2_pA",
)


def initial_state() -> dict[str, float]:
    """Return a fresh state dictionary containing the Appendix B initial values."""
    return dict(INITIAL_STATE)


def state_to_array(state: State) -> np.ndarray:
    """Convert a named state mapping to the model's fixed, documented ordering."""
    missing = set(STATE_NAMES).difference(state)
    if missing:
        raise ValueError(f"Missing state variables: {', '.join(sorted(missing))}")
    values = np.asarray([state[name] for name in STATE_NAMES], dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError("State values must all be finite")
    return values


def array_to_state(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(STATE_NAMES),) or not np.all(np.isfinite(array)):
        raise ValueError(f"Expected {len(STATE_NAMES)} finite state values")
    return dict(zip(STATE_NAMES, map(float, array)))


def _exp(value: float) -> float:
    try:
        result = exp(value)
    except OverflowError as exc:
        raise ValueError(f"Exponential overflow for argument {value}") from exc
    return result


def _x_over_expm1(x: float) -> float:
    """Stable evaluation of x/(exp(x)-1), including its removable limit."""
    if abs(x) < 1e-7:
        return 1.0 - x / 2.0 + x * x / 12.0
    return x / expm1(x)


def calcium_reversal_potential(
    ca_s_uM: float,
    log_base: LogBase,
    params: PaperParameters = PAPER_PARAMETERS,
) -> float:
    """B.5 E_Ca in mV; the source's unspecified logarithm base is explicit."""
    if not isfinite(ca_s_uM) or ca_s_uM <= 0:
        raise ValueError("[Ca]s must be finite and positive for E_Ca")
    if log_base == "e":
        logarithm = log(ca_s_uM / params.Ca0_uM)
    elif log_base == "10":
        logarithm = log10(ca_s_uM / params.Ca0_uM)
    else:
        raise ValueError("log_base must be explicitly set to 'e' or '10'")
    return -12.5 * logarithm


def currents(
    state: State,
    log_base: LogBase,
    params: PaperParameters = PAPER_PARAMETERS,
) -> dict[str, float]:
    """Evaluate Appendix B algebraic currents (pA) from one pre-update state."""
    v = float(state["V_mV"])
    ca_s = float(state["Ca_s_uM"])
    if not isfinite(v) or not isfinite(ca_s):
        raise ValueError("Voltage and shell calcium must be finite")

    c3 = float(state["cGMP"]) ** 3
    photo_j = params.Jmax_pA * c3 / (c3 + 10.0**3)
    i_photo = -photo_j * (1.0 - _exp((v - 8.5) / 17.0))

    i_h = params.gbar_h_nS * (
        float(state["O1"]) + float(state["O2"]) + float(state["O3"])
    ) * (v - params.E_h_mV)
    i_kv = (
        params.gbar_Kv_nS
        * float(state["mKv"]) ** 3
        * float(state["hKv"])
        * (v - params.E_K_mV)
    )
    h_ca = _exp((40.0 - v) / 18.0)
    h_ca /= 1.0 + h_ca
    e_ca = calcium_reversal_potential(ca_s, log_base, params)
    i_ca = (
        params.gbar_Ca_nS
        * float(state["mCa"]) ** 4
        * h_ca
        * (v - e_ca)
    )
    m_cl = 1.0 / (1.0 + _exp((0.37 - ca_s) / 0.09))
    i_cl = params.gbar_Cl_nS * m_cl * (v - params.E_Cl_mV)
    m_kca_s = ca_s / (ca_s + 0.3)
    i_kca = (
        params.gbar_KCa_nS
        * float(state["mKCa"]) ** 2
        * m_kca_s
        * (v - params.E_K_mV)
    )
    i_l = params.g_L_nS * (v - params.E_L_mV)
    i_ex = (
        params.J_ex_pA
        * _exp(-(v + 14.0) / 70.0)
        * (ca_s - params.Cae_uM)
        / (ca_s - params.Cae_uM + params.K_ex_uM)
    )
    i_ex2 = (
        params.J_ex2_pA
        * (ca_s - params.Cae_uM)
        / (ca_s - params.Cae_uM + params.K_ex2_uM)
    )
    result = {
        "J_pA": photo_j,
        "I_photo_pA": i_photo,
        "I_h_pA": i_h,
        "I_Kv_pA": i_kv,
        "I_Ca_pA": i_ca,
        "I_ClCa_pA": i_cl,
        "I_KCa_pA": i_kca,
        "I_L_pA": i_l,
        "I_ex_pA": i_ex,
        "I_ex2_pA": i_ex2,
    }
    if not all(isfinite(value) for value in result.values()):
        raise ValueError("Current evaluation produced a non-finite result")
    result["I_ALL_pA"] = sum(result[name] for name in MEMBRANE_CURRENT_NAMES)
    return result


def derivatives(
    t_s: float,
    state: State,
    j_hv: float,
    log_base: LogBase,
    params: PaperParameters = PAPER_PARAMETERS,
) -> dict[str, float]:
    """Evaluate all Appendix B state derivatives at one instant.

    j_hv is the explicitly supplied Rh-driving input in the source equation's
    units. The paper does not specify its units or time course.
    """
    if not isfinite(t_s) or not isfinite(j_hv):
        raise ValueError("Time and J_hv must be finite")
    v = float(state["V_mV"])
    rh, rhi = float(state["Rh"]), float(state["Rhi"])
    tr, pde = float(state["Tr"]), float(state["PDE"])
    ca = float(state["Ca_uM"])
    cgmp, cab = float(state["cGMP"]), float(state["Cab_uM"])
    c1, c2, o1, o2, o3 = (float(state[name]) for name in ("C1", "C2", "O1", "O2", "O3"))
    m_kv, h_kv = float(state["mKv"]), float(state["hKv"])
    m_ca, ca_s, ca_f = float(state["mCa"]), float(state["Ca_s_uM"]), float(state["Ca_f_uM"])
    cab_ls, cab_hs = float(state["Cab_ls_uM"]), float(state["Cab_hs_uM"])
    cab_lf, cab_hf = float(state["Cab_lf_uM"]), float(state["Cab_hf_uM"])
    m_kca = float(state["mKCa"])
    i = currents(state, log_base, params)

    alpha_h = 8.0 / (_exp((v + 78.0) / 14.0) + 1.0)
    beta_h = 18.0 / (_exp((-v + 8.0) / 19.0) + 1.0)
    dh_states = (
        -4.0 * alpha_h * c1 + beta_h * c2,
        4.0 * alpha_h * c1 - (3.0 * alpha_h + beta_h) * c2 + 2.0 * beta_h * o1,
        3.0 * alpha_h * c2 - (2.0 * alpha_h + 2.0 * beta_h) * o1 + 3.0 * beta_h * o2,
        2.0 * alpha_h * o1 - (alpha_h + 3.0 * beta_h) * o2 + 4.0 * beta_h * o3,
        alpha_h * o2 - 4.0 * beta_h * o3,
    )

    x_kv = (100.0 - v) / 42.0
    alpha_m_kv = 5.0 * 42.0 * _x_over_expm1(x_kv)
    beta_m_kv = 9.0 * _exp(-(v - 20.0) / 40.0)
    alpha_h_kv = 0.15 * _exp(-v / 22.0)
    beta_h_kv = 0.4125 / (_exp((10.0 - v) / 7.0) + 1.0)

    x_ca = (80.0 - v) / 25.0
    alpha_m_ca = 3.0 * 25.0 * _x_over_expm1(x_ca)
    beta_m_ca = 10.0 / (1.0 + _exp((v + 38.0) / 7.0))
    x_kca = (80.0 - v) / 40.0
    alpha_m_kca = 15.0 * 40.0 * _x_over_expm1(x_kca)
    beta_m_kca = 20.0 * _exp(-v / 35.0)

    # B.9 current conversion: pA -> A and mol/dm^3 -> μM.
    ca_current_source_uM_s = -(i["I_Ca_pA"] + i["I_ex_pA"] + i["I_ex2_pA"]) * 1e-6
    ca_current_source_uM_s /= 2.0 * params.F_C_mol * params.V1_dm3
    diffusion = params.D_Ca_dm2_s * params.S1_dm2 / (params.delta_dm * params.V1_dm3)
    diffusion_free = params.D_Ca_dm2_s * params.S1_dm2 / (params.delta_dm * params.V2_dm3)

    d = {
        "V_mV": -i["I_ALL_pA"] / params.C_m_nF,
        "Rh": j_hv - params.alpha1_s * rh + params.alpha2_s * rhi,
        "Rhi": params.alpha1_s * rh - (params.alpha2_s + params.alpha3_s) * rhi,
        "Tr": (
            params.epsilon_s_uM * rh * (params.Ttot_uM - tr)
            - params.beta1_s * tr
            + params.tau2_s * pde
            - params.tau1_s_uM * tr * (params.PDEtot_uM - pde)
        ),
        "PDE": params.tau1_s_uM * tr * (params.PDEtot_uM - pde) - params.tau2_s * pde,
        "Ca_uM": (
            params.b_uM_s_pA * i["J_pA"]
            - params.gammaCa_s * (ca - params.C0_uM)
            - params.k1_s_uM * (params.eT_uM - cab) * ca
            + params.k2_s * cab
        ),
        "cGMP": (
            params.Amax_uM_s / (1.0 + (ca / params.Kc_value) ** 4)
            - cgmp * (params.Vbar_s - params.sigma_s_uM * pde)
        ),
        "Cab_uM": params.k1_s_uM * (params.eT_uM - cab) * ca - params.k2_s * cab,
        "C1": dh_states[0],
        "C2": dh_states[1],
        "O1": dh_states[2],
        "O2": dh_states[3],
        "O3": dh_states[4],
        "mKv": alpha_m_kv * (1.0 - m_kv) - beta_m_kv * m_kv,
        "hKv": alpha_h_kv * (1.0 - h_kv) - beta_h_kv * h_kv,
        "mCa": alpha_m_ca * (1.0 - m_ca) - beta_m_ca * m_ca,
        "Ca_s_uM": (
            ca_current_source_uM_s
            - diffusion * (ca_s - ca_f)
            - params.Lb1_s_uM * ca_s * (params.BL_uM - cab_ls)
            + params.Lb2_s * cab_ls
            - params.Hb1_s_uM * ca_s * (params.BH_uM - cab_hs)
            + params.Hb2_s * cab_hs
        ),
        "Ca_f_uM": (
            diffusion_free * (ca_s - ca_f)
            - params.Lb1_s_uM * ca_f * (params.BL_uM - cab_lf)
            + params.Lb2_s * cab_lf
            - params.Hb1_s_uM * ca_f * (params.BH_uM - cab_hf)
            + params.Hb2_s * cab_hf
        ),
        "Cab_ls_uM": params.Lb1_s_uM * ca_s * (params.BL_uM - cab_ls) - params.Lb2_s * cab_ls,
        "Cab_hs_uM": params.Hb1_s_uM * ca_s * (params.BH_uM - cab_hs) - params.Hb2_s * cab_hs,
        "Cab_lf_uM": params.Lb1_s_uM * ca_f * (params.BL_uM - cab_lf) - params.Lb2_s * cab_lf,
        "Cab_hf_uM": params.Hb1_s_uM * ca_f * (params.BH_uM - cab_hf) - params.Hb2_s * cab_hf,
        "mKCa": alpha_m_kca * (1.0 - m_kca) - beta_m_kca * m_kca,
    }
    if not all(isfinite(value) for value in d.values()):
        raise ValueError("Derivative evaluation produced a non-finite result")
    return d


def simulate(
    duration_s: float,
    max_step_s: float,
    j_hv: Callable[[float], float],
    log_base: LogBase,
    *,
    rtol: float = 1e-9,
    atol: float = 1e-11,
    params: PaperParameters = PAPER_PARAMETERS,
):
    """Integrate the full printed state equations using SciPy DOP853.

    J_hv and log_base are required to prevent silent assumptions about the two
    unresolved source definitions. Output currents are evaluated at solver
    sample points from the corresponding returned (post-integration) states.
    """
    if duration_s <= 0 or max_step_s <= 0 or rtol <= 0 or atol <= 0:
        raise ValueError("duration, max_step, rtol, and atol must be positive")
    if not callable(j_hv):
        raise TypeError("j_hv must be a callable that accepts time in seconds")
    y0 = state_to_array(INITIAL_STATE)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        state = array_to_state(y)
        d = derivatives(t, state, float(j_hv(t)), log_base, params)
        return np.asarray([d[name] for name in STATE_NAMES], dtype=np.float64)

    from scipy.integrate import solve_ivp

    solution = solve_ivp(
        rhs,
        (0.0, duration_s),
        y0,
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=max_step_s,
    )
    if not solution.success:
        raise RuntimeError(f"Paper-model integration failed: {solution.message}")
    states = [array_to_state(solution.y[:, index]) for index in range(solution.t.size)]
    current_rows = [currents(state, log_base, params) for state in states]
    return {
        "t_s": solution.t,
        "states": states,
        "currents": current_rows,
        "solver_message": solution.message,
        "nfev": solution.nfev,
        "log_base_assumption": log_base,
        "j_hv_description": getattr(j_hv, "__name__", repr(j_hv)),
    }
