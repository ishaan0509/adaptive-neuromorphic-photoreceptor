from baseline_fixed_point import (
    FRAC_BITS,
    LUT_VALUES,
    SCALE,
    BaselineFixedPoint,
    make_stimuli,
    qdiv,
    qmul,
    sigmoid_lut,
    simulate_stimulus,
    wrap_signed,
)
from export_baseline_vectors import export_all


def test_signed_40_bit_wrapping_and_qmul_boundaries():
    assert wrap_signed((1 << 39) - 1) == (1 << 39) - 1
    assert wrap_signed(1 << 39) == -(1 << 39)
    assert wrap_signed(-(1 << 39) - 1) == (1 << 39) - 1
    assert qmul(SCALE, -SCALE) == -SCALE
    assert qmul((1 << 39) - 1, SCALE) == (1 << 39) - 1


def test_qdiv_uses_signed_truncation_toward_zero_and_q_word_result():
    assert qdiv(-1, 3) == -((1 << FRAC_BITS) // 3)
    assert qdiv(1, 3) == (1 << FRAC_BITS) // 3
    assert qdiv(7 * SCALE, 2 * SCALE) == 3 * SCALE + SCALE // 2


def test_sigmoid_lut_matches_the_rtl_table_and_clamps_limits():
    assert sigmoid_lut(-8 * SCALE) == LUT_VALUES[0]
    assert sigmoid_lut(8 * SCALE) == LUT_VALUES[32]
    assert sigmoid_lut(0) == LUT_VALUES[16]
    assert sigmoid_lut(-9 * SCALE) == LUT_VALUES[0]
    assert sigmoid_lut(9 * SCALE) == LUT_VALUES[32]
    half_step = SCALE // 2
    for index, expected in enumerate(LUT_VALUES):
        x_q = -8 * SCALE + index * half_step
        assert sigmoid_lut(x_q) == expected


def test_reset_valid_update_and_idle_hold():
    model = BaselineFixedPoint()
    reset_row = model.cycle(reset=True, valid_in=True, light_q=SCALE, cycle=0)
    assert reset_row["v_mem_q"] == -1006632960
    assert reset_row["i_photo_q"] == 33554432000
    assert reset_row["valid_out"] == 0

    first = model.cycle(light_q=0, valid_in=True, cycle=1)
    assert first["valid_out"] == 1
    assert first["v_mem_q"] == -958630687
    state_after_valid = dict(model.state)

    idle = model.cycle(light_q=SCALE, valid_in=False, cycle=2)
    assert idle["valid_out"] == 0
    assert model.state == state_after_valid
    assert idle["i_photo_q"] == 33554432000

    restarted = model.cycle(reset=True, valid_in=False, cycle=3)
    assert restarted["valid_out"] == 0
    assert model.state["v_mem_q"] == -1006632960


def test_dark_step_and_pulse_stimuli_are_deterministic_and_multi_step():
    stimuli_a = make_stimuli(40)
    stimuli_b = make_stimuli(40)
    assert stimuli_a == stimuli_b
    assert len(stimuli_a["dark"]) == 40
    assert stimuli_a["dark"][0]["reset"] == 1
    assert all(row["light_q"] == 0 for row in stimuli_a["dark"])

    step = [row["light_q"] for row in stimuli_a["step"]]
    pulse = [row["light_q"] for row in stimuli_a["pulse"]]
    assert step.count(SCALE) > 0 and step[-1] == SCALE
    assert pulse.count(SCALE) > 0 and pulse[-1] == 0

    for scenario in stimuli_a.values():
        trace = simulate_stimulus(scenario)
        assert len(trace) == 40
        assert trace[0]["valid_out"] == 0
        assert trace[1]["valid_out"] == 1
        assert trace[-1]["cycle"] == 39
        assert all(len(row) == 23 for row in trace)


def test_csv_export_contains_all_observable_raw_values(tmp_path):
    exports = export_all(tmp_path, cycles=8)
    assert set(exports) == {"dark", "step", "pulse"}
    for path in exports.values():
        lines = path.read_text(encoding="ascii").splitlines()
        assert len(lines) == 9
        header = lines[0].split(",")
        assert "v_mem_q" in header
        assert "i_total_q" in header
        assert "m_h_q_out" in header
        assert "ca_i_q" in header
        assert "valid_out" in header
