"""Appendix B values transcribed from Shah et al. (2023), printed pp. 8-10.

State and parameter quantities use the units printed in Appendix B where
available. A few units are only implied by the equations; see
PAPER_EQUATION_AUDIT.md before interpreting results.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperParameters:
    # B.1 membrane (V: mV, I: pA, C_m: nF, time: s)
    C_m_nF: float = 0.02

    # B.2 phototransduction (rate constants per second)
    alpha1_s: float = 50.0
    alpha2_s: float = 0.0003
    alpha3_s: float = 0.03
    epsilon_s_uM: float = 0.5
    Ttot_uM: float = 1000.0
    beta1_s: float = 2.5
    tau1_s_uM: float = 0.2
    tau2_s: float = 5.0
    PDEtot_uM: float = 100.0
    gammaCa_s: float = 50.0
    C0_uM: float = 0.1
    b_uM_s_pA: float = 0.25
    k1_s_uM: float = 0.2
    k2_s: float = 0.8
    eT_uM: float = 500.0
    Vbar_s: float = 0.4
    Kc_value: float = 0.1
    Amax_uM_s: float = 65.6
    sigma_s_uM: float = 1.0
    Jmax_pA: float = 5040.0

    # B.3 Ih
    gbar_h_nS: float = 3.0
    E_h_mV: float = -32.0

    # B.4 delayed-rectifier potassium
    gbar_Kv_nS: float = 2.0
    E_K_mV: float = -74.0

    # B.5 calcium current
    gbar_Ca_nS: float = 0.7
    Ca0_uM: float = 1600.0

    # B.6 calcium-activated chloride
    gbar_Cl_nS: float = 2.0
    E_Cl_mV: float = -20.0

    # B.7 calcium-activated potassium
    gbar_KCa_nS: float = 5.0

    # B.8 leakage
    g_L_nS: float = 0.35
    E_L_mV: float = -77.0

    # B.9 intercellular calcium
    F_C_mol: float = 9.648e4
    V1_dm3: float = 3.812e-13
    V2_dm3: float = 5.236e-13
    D_Ca_dm2_s: float = 6.0e-8
    delta_dm: float = 3.0e-5
    S1_dm2: float = 3.142e-8
    Lb1_s_uM: float = 0.4
    Lb2_s: float = 0.2
    Hb1_s_uM: float = 100.0
    Hb2_s: float = 90.0
    BL_uM: float = 500.0
    BH_uM: float = 300.0
    J_ex_pA: float = 20.0
    J_ex2_pA: float = 20.0
    K_ex_uM: float = 2.3
    K_ex2_uM: float = 0.5
    Cae_uM: float = 0.01


PAPER_PARAMETERS = PaperParameters()

# Appendix B initial conditions, printed pp. 8-10.
INITIAL_STATE = {
    "V_mV": -36.186,
    "Rh": 0.0,
    "Rhi": 0.0,
    "Tr": 0.0,
    "PDE": 0.0,
    "Ca_uM": 0.3,
    "cGMP": 2.0,
    "Cab_uM": 34.88,
    "C1": 0.646,
    "C2": 0.298,
    "O1": 0.0517,
    "O2": 0.00398,
    "O3": 0.000115,
    "mKv": 0.430,
    "hKv": 0.999,
    "mCa": 0.436,
    "Ca_s_uM": 0.0966,
    "Ca_f_uM": 0.0966,
    "Cab_ls_uM": 80.929,
    "Cab_hs_uM": 29.068,
    "Cab_lf_uM": 80.929,
    "Cab_hf_uM": 29.068,
    "mKCa": 0.642,
}
