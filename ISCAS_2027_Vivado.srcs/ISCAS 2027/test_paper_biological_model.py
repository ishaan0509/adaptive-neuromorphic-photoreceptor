import math
import unittest
from dataclasses import replace

from paper_biological_model import (
    MEMBRANE_CURRENT_NAMES,
    STATE_NAMES,
    calcium_reversal_potential,
    currents,
    derivatives,
    initial_state,
)
from paper_biological_parameters import INITIAL_STATE, PAPER_PARAMETERS


class PaperBiologicalModelTests(unittest.TestCase):
    def test_initial_conditions_match_appendix_b_transcription(self):
        self.assertEqual(set(INITIAL_STATE), set(STATE_NAMES))
        self.assertEqual(initial_state(), INITIAL_STATE)
        self.assertEqual(INITIAL_STATE["V_mV"], -36.186)
        self.assertEqual(INITIAL_STATE["cGMP"], 2.0)
        self.assertEqual(INITIAL_STATE["Ca_s_uM"], 0.0966)

    def test_calcium_reversal_log_choice_is_explicit(self):
        ca = 80.0
        self.assertAlmostEqual(
            calcium_reversal_potential(ca, "e"),
            -12.5 * math.log(ca / PAPER_PARAMETERS.Ca0_uM),
        )
        self.assertAlmostEqual(
            calcium_reversal_potential(ca, "10"),
            -12.5 * math.log10(ca / PAPER_PARAMETERS.Ca0_uM),
        )
        self.assertNotAlmostEqual(
            calcium_reversal_potential(ca, "e"),
            calcium_reversal_potential(ca, "10"),
        )
        with self.assertRaises(ValueError):
            calcium_reversal_potential(0.0, "e")

    def test_calcium_reference_concentration_uses_supplied_parameters(self):
        params = replace(PAPER_PARAMETERS, Ca0_uM=1000.0)
        self.assertAlmostEqual(
            calcium_reversal_potential(100.0, "e", params),
            -12.5 * math.log(0.1),
        )
        state = initial_state()
        default_current = currents(state, "e")["I_Ca_pA"]
        custom_current = currents(state, "e", params)["I_Ca_pA"]
        self.assertNotEqual(default_current, custom_current)

    def test_currents_match_direct_algebraic_evaluations(self):
        state = initial_state()
        result = currents(state, "e")
        c3 = state["cGMP"] ** 3
        j = PAPER_PARAMETERS.Jmax_pA * c3 / (c3 + 10**3)
        expected_photo = -j * (
            1.0 - math.exp((state["V_mV"] - 8.5) / 17.0)
        )
        expected_leak = PAPER_PARAMETERS.g_L_nS * (
            state["V_mV"] - PAPER_PARAMETERS.E_L_mV
        )
        self.assertAlmostEqual(result["I_photo_pA"], expected_photo, places=13)
        self.assertAlmostEqual(result["I_L_pA"], expected_leak, places=13)
        self.assertAlmostEqual(
            result["I_ALL_pA"],
            sum(result[name] for name in MEMBRANE_CURRENT_NAMES),
            places=13,
        )
        self.assertNotEqual(result["J_pA"], result["I_photo_pA"])

    def test_b2_calcium_source_uses_j_not_the_membrane_photocurrent(self):
        state = initial_state()
        values = currents(state, "e")
        d = derivatives(0.0, state, j_hv=0.0, log_base="e")
        expected = (
            PAPER_PARAMETERS.b_uM_s_pA * values["J_pA"]
            - PAPER_PARAMETERS.gammaCa_s
            * (state["Ca_uM"] - PAPER_PARAMETERS.C0_uM)
            - PAPER_PARAMETERS.k1_s_uM
            * (PAPER_PARAMETERS.eT_uM - state["Cab_uM"])
            * state["Ca_uM"]
            + PAPER_PARAMETERS.k2_s * state["Cab_uM"]
        )
        self.assertAlmostEqual(d["Ca_uM"], expected, places=13)

    def test_h_channel_kinetic_matrix_conserves_total_probability(self):
        state = initial_state()
        d = derivatives(0.0, state, j_hv=0.0, log_base="e")
        self.assertAlmostEqual(
            sum(d[name] for name in ("C1", "C2", "O1", "O2", "O3")),
            0.0,
            places=12,
        )

    def test_voltage_dependent_rate_removable_singularities_are_finite(self):
        state = initial_state()
        state["V_mV"] = 100.0
        d_kv = derivatives(0.0, state, j_hv=0.0, log_base="e")
        alpha_m_kv = 210.0
        beta_m_kv = 9.0 * math.exp(-(100.0 - 20.0) / 40.0)
        self.assertAlmostEqual(
            d_kv["mKv"],
            alpha_m_kv * (1.0 - state["mKv"]) - beta_m_kv * state["mKv"],
        )

        state["V_mV"] = 80.0
        d_ca = derivatives(0.0, state, j_hv=0.0, log_base="e")
        alpha_m_ca = 75.0
        beta_m_ca = 10.0 / (1.0 + math.exp((80.0 + 38.0) / 7.0))
        self.assertAlmostEqual(
            d_ca["mCa"],
            alpha_m_ca * (1.0 - state["mCa"]) - beta_m_ca * state["mCa"],
        )
        self.assertTrue(all(math.isfinite(value) for value in d_ca.values()))

    def test_unresolved_input_is_supplied_and_propagates_into_rh(self):
        state = initial_state()
        d = derivatives(0.0, state, j_hv=2.5, log_base="e")
        self.assertEqual(d["Rh"], 2.5)
        with self.assertRaises(ValueError):
            derivatives(0.0, state, j_hv=0.0, log_base="natural")


if __name__ == "__main__":
    unittest.main()
