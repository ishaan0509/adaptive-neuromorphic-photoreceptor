from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ADAPTIVE = (ROOT / "sources_1" / "new" / "photoreceptor_adaptive.v").read_text()
SCHEDULER = (ROOT / "sources_1" / "new" / "current_update_scheduler.v").read_text()


def test_all_six_current_modules_use_refresh_isolated_operands():
    for operand in (
        "current_v_q",
        "current_m_h_q",
        "current_m_kv_q",
        "current_m_ca_q",
        "current_m_clca_q",
        "current_m_kca_q",
        "current_ca_i_q",
    ):
        assert f"assign {operand} =" in ADAPTIVE
    assert ".v_mem_q(current_v_q)" in ADAPTIVE
    assert ".m_h_q(current_m_h_q)" in ADAPTIVE
    assert ".m_kv_q(current_m_kv_q)" in ADAPTIVE
    assert ".m_ca_q(current_m_ca_q)" in ADAPTIVE
    assert ".m_clca_q(current_m_clca_q)" in ADAPTIVE
    assert ".m_kca_q(current_m_kca_q)" in ADAPTIVE
    assert ".ca_i_q(current_ca_i_q)" in ADAPTIVE


def test_isolation_snapshots_update_only_on_valid_refresh_and_reset_known():
    assert "end else if (valid_in) begin" in ADAPTIVE
    assert "if (refresh_all) begin" in ADAPTIVE
    assert "isolated_v_q <= v_mem_q;" in ADAPTIVE
    assert "isolated_ca_i_q <= ca_i_wire_q;" in ADAPTIVE
    assert "isolated_v_q <= -40'sd1006632960;" in ADAPTIVE
    assert "cache_initialized <= 1'b0;" in ADAPTIVE


def test_scheduler_interval_is_clamped_and_counter_saturates():
    assert "MAX_REFRESH_INTERVAL > 65536) ? 65536" in SCHEDULER
    assert "refresh_counter != 16'hffff" in SCHEDULER
