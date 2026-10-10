from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class PhotoreceptorParameters:
    """Parameter container for the provisional model.

    The current physiological values are unverified placeholders retained from
    the initial implementation; they are not transcriptions of Shah et al.
    Numerical integration settings are experimental choices.
    """

    # Membrane and phototransduction
    C_m: float = 30e-12
    g_photo: float = 2.0e-9
    light_gain: float = 1.0
    E_photo: float = 0.0

    # Reversal potentials (V)
    E_h: float = -0.020
    E_k: float = -0.080
    E_ca: float = 0.060
    E_cl: float = -0.070
    E_l: float = -0.050

    # Conductances (S)
    g_h: float = 120e-9
    g_kv: float = 250e-9
    g_ca: float = 140e-9
    g_clca: float = 90e-9
    g_kca: float = 80e-9
    g_l: float = 20e-9

    # Gating variables
    v_half_h: float = -0.045
    k_h: float = 0.008
    tau_h: float = 0.010

    v_half_kv: float = -0.035
    k_kv: float = 0.010
    tau_kv: float = 0.020

    v_half_ca: float = -0.030
    k_ca: float = 0.008
    tau_ca: float = 0.025

    v_half_clca: float = -0.020
    k_clca: float = 0.005
    tau_clca: float = 0.030

    v_half_kca: float = -0.025
    k_kca: float = 0.006
    tau_kca: float = 0.040

    # Calcium subsystem and binding states
    alpha_ca: float = 1.2e-3
    beta_ca: float = 0.25
    ca_rest: float = 30e-6
    k_clca_ca: float = 0.4e-3
    k_kca_ca: float = 0.35e-3
    ca_scale: float = 1.0e-3

    # Initial conditions
    v_init: float = -0.060
    i_photo_init: float = 0.0
    m_h_init: float = 0.12
    m_kv_init: float = 0.18
    m_ca_init: float = 0.22
    m_clca_init: float = 0.15
    m_kca_init: float = 0.10
    ca_i_init: float = 0.11e-3
    ca_s_init: float = 0.08e-3
    ca_f_init: float = 0.05e-3

    # Numerical settings (experimental choices)
    dt: float = 1e-4
    t_end: float = 1.0
    solver: str = "LSODA"
    rtol: float = 1e-8
    atol: float = 1e-10
    max_step: float = 1e-4

    @staticmethod
    def default() -> "PhotoreceptorParameters":
        return PhotoreceptorParameters()

    def as_dict(self) -> Dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    def state_vector(self) -> Dict[str, float]:
        return {
            "V": self.v_init,
            "I_photo": self.i_photo_init,
            "m_h": self.m_h_init,
            "m_kv": self.m_kv_init,
            "m_ca": self.m_ca_init,
            "m_clca": self.m_clca_init,
            "m_kca": self.m_kca_init,
            "Ca_i": self.ca_i_init,
            "Ca_s": self.ca_s_init,
            "Ca_f": self.ca_f_init,
        }


DEFAULT_PARAMETERS = PhotoreceptorParameters.default()
