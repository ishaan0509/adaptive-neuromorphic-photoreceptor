import copy
import math

import pytest

from adaptive_trace_metrics import (
    EXPECTED_CYCLES,
    EXPECTED_SCENARIOS,
    IONIC_CURRENTS,
    POST_STATE_PAIRS,
    REQUIRED_COLUMNS,
    summarize_rows,
)


def _signed_40(value):
    value &= (1 << 40) - 1
    return value - (1 << 40) if value & (1 << 39) else value


def _trace():
    rows = []
    for scenario in EXPECTED_SCENARIOS:
        age = 0
        last_refresh_light = 0
        adaptive_count = 0
        cached = {current: 100 for current in IONIC_CURRENTS}
        for cycle in range(EXPECTED_CYCLES):
            if scenario == 0:
                light = 0
            elif scenario == 1:
                light = 1 if cycle >= 10 else 0
            elif scenario == 2:
                light = 1 if 10 <= cycle < 16 else 0
            else:
                light = cycle % 2
            refresh = int(
                cycle == 0 or light != last_refresh_light or age >= 7
            )
            if refresh:
                last_refresh_light = light
                age = 0

            row = {
                "scenario": str(scenario),
                "cycle_id": str(cycle),
                "valid_in": "1",
                "light_base_q": str(light),
                "light_adapt_q": str(light),
                "refresh_decision_pre": str(refresh),
                "refresh_counter_pre": str(age),
                "baseline_nominal_ionic_formula_count_pre": str(cycle * 6),
                "adaptive_recomputation_counter_pre": str(adaptive_count),
                "i_photo_base_pre_q": "50",
                "i_photo_adapt_pre_q": "50",
                "i_photo_base_applied_q": "50",
                "i_photo_adapt_applied_q": "50",
                "v_base_pre_q": str(1000 + cycle),
                "v_adapt_pre_q": str(1000 + cycle),
            }
            base_total = 50
            adapt_live_total = 50
            adapt_applied_total = 50
            for current_index, current in enumerate(IONIC_CURRENTS):
                baseline_current = 100 + cycle + current_index
                live_current = baseline_current
                if refresh:
                    cached[current] = live_current
                applied_current = cached[current]
                row[f"{current}_base_pre_q"] = str(baseline_current)
                row[f"{current}_base_applied_q"] = str(baseline_current)
                row[f"{current}_adapt_live_pre_q"] = str(live_current)
                row[f"{current}_adapt_applied_q"] = str(applied_current)
                base_total += baseline_current
                adapt_live_total += live_current
                adapt_applied_total += applied_current

            row["i_total_base_pre_q"] = str(_signed_40(base_total))
            row["i_total_base_applied_q"] = row["i_total_base_pre_q"]
            row["i_total_adapt_live_pre_q"] = str(
                _signed_40(adapt_live_total)
            )
            row["i_total_adapt_applied_pre_q"] = str(
                _signed_40(adapt_applied_total)
            )
            row["i_total_adapt_applied_q"] = row[
                "i_total_adapt_applied_pre_q"
            ]

            row["baseline_nominal_ionic_formula_count_post"] = str((cycle + 1) * 6)
            if refresh:
                adaptive_count += 6
            row["adaptive_recomputation_counter_post"] = str(adaptive_count)
            row["refresh_counter_post"] = str(0 if refresh else age + 1)

            voltage_error = 3 if scenario == 0 and cycle == 1 else 0
            for base_key, adapt_key, _ in POST_STATE_PAIRS:
                base_value = 2000 + cycle
                difference = (
                    voltage_error if base_key == "v_base_post_q" else 0
                )
                row[base_key] = str(base_value)
                row[adapt_key] = str(base_value + difference)
            rows.append(row)
            if not refresh:
                age += 1
    return rows


def _scenario_zero(rows):
    return [row for row in rows if int(row["scenario"]) == 0]


def test_metrics_validate_trace_and_calculate_observed_errors():
    result = summarize_rows(_trace())[0]
    assert result["scenario"] == 0
    assert result["cycles"] == 40
    assert result["refresh_events"] == 5
    assert result["adaptive_nominal_refresh_evaluations"] == 30
    assert result["full_update_reference_evaluations"] == 240
    assert result["nominal_refresh_count_reduction_percent"] == pytest.approx(87.5)
    assert result["v_membrane_observed_max_abs_error_raw"] == 3
    assert result["v_membrane_observed_rms_error_raw"] == pytest.approx(
        math.sqrt(9 / 40)
    )
    assert result["applied_total_current_observed_max_abs_difference_raw"] == 42
    assert result["applied_total_current_observed_max_abs_difference_pA"] == pytest.approx(
        42 / (1 << 24)
    )
    assert result["hardware_activity_measured"] is False
    assert result["voltage_error_is_guaranteed_bound"] is False


def test_rejects_missing_scenarios_and_wrong_row_count():
    rows = _trace()
    with pytest.raises(ValueError, match="missing scenarios"):
        summarize_rows([row for row in rows if row["scenario"] != "3"])
    with pytest.raises(ValueError, match="expected 40 rows"):
        summarize_rows(rows[:-1])


def test_rejects_duplicate_nonconsecutive_and_out_of_order_cycles():
    rows = _trace()
    scenario_rows = _scenario_zero(rows)
    duplicate = copy.deepcopy(rows)
    duplicate[1]["cycle_id"] = "0"
    with pytest.raises(ValueError, match="cycle IDs"):
        summarize_rows(duplicate)

    nonconsecutive = copy.deepcopy(rows)
    nonconsecutive[1]["cycle_id"] = "3"
    with pytest.raises(ValueError, match="cycle IDs"):
        summarize_rows(nonconsecutive)

    out_of_order = copy.deepcopy(rows)
    out_of_order[0], out_of_order[1] = out_of_order[1], out_of_order[0]
    with pytest.raises(ValueError, match="cycle IDs"):
        summarize_rows(out_of_order)
    assert len(scenario_rows) == EXPECTED_CYCLES


def test_rejects_scenario_blocks_out_of_file_order():
    rows = _trace()
    reordered = rows[EXPECTED_CYCLES:] + rows[:EXPECTED_CYCLES]
    with pytest.raises(ValueError, match="scenario-major file order"):
        summarize_rows(reordered)


def test_rejects_missing_columns_invalid_samples_and_bad_numeric_values():
    rows = _trace()
    missing_column = copy.deepcopy(rows)
    del missing_column[0]["v_adapt_post_q"]
    with pytest.raises(ValueError, match="missing required columns"):
        summarize_rows(missing_column)

    invalid_sample = copy.deepcopy(rows)
    invalid_sample[0]["valid_in"] = "0"
    with pytest.raises(ValueError, match="invalid samples"):
        summarize_rows(invalid_sample)

    malformed_number = copy.deepcopy(rows)
    malformed_number[0]["i_total_base_applied_q"] = "not-an-integer"
    with pytest.raises(ValueError, match="malformed integer"):
        summarize_rows(malformed_number)


def test_rejects_baseline_adaptive_input_mismatch_and_bad_current_sum():
    mismatched_input = copy.deepcopy(_trace())
    mismatched_input[0]["light_adapt_q"] = "1"
    with pytest.raises(ValueError, match="inputs differ"):
        summarize_rows(mismatched_input)

    invalid_sum = copy.deepcopy(_trace())
    invalid_sum[0]["ih_base_applied_q"] = "999"
    with pytest.raises(ValueError, match="pre-edge/applied"):
        summarize_rows(invalid_sum)


def test_rejects_missing_scenario_and_unexpected_scenario_id():
    rows = _trace()
    unexpected = copy.deepcopy(rows)
    for row in unexpected:
        if row["scenario"] == "3":
            row["scenario"] = "4"
    with pytest.raises(ValueError, match="missing scenarios.*unexpected scenarios"):
        summarize_rows(unexpected)


def test_schema_covers_all_required_trace_columns():
    rows = _trace()
    assert REQUIRED_COLUMNS.issubset(rows[0])
