"""Validate and summarize paired pre-edge/post-edge adaptive RTL traces."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

SCALE = 1 << 24
EXPECTED_SCENARIOS = (0, 1, 2, 3)
EXPECTED_CYCLES = 40
MAX_REFRESH_INTERVAL = 8
IONIC_CURRENTS = ("ih", "ikv", "ica", "iclca", "ikca", "il")
POST_STATE_PAIRS = (
    ("v_base_post_q", "v_adapt_post_q", "v_membrane"),
    ("ca_i_base_post_q", "ca_i_adapt_post_q", "ca_i"),
    ("ca_s_base_post_q", "ca_s_adapt_post_q", "ca_s"),
    ("ca_f_base_post_q", "ca_f_adapt_post_q", "ca_f"),
    ("mh_base_post_q", "mh_adapt_post_q", "mh"),
    ("mkv_base_post_q", "mkv_adapt_post_q", "mkv"),
    ("mca_base_post_q", "mca_adapt_post_q", "mca"),
    ("mclca_base_post_q", "mclca_adapt_post_q", "mclca"),
    ("mkca_base_post_q", "mkca_adapt_post_q", "mkca"),
)

REQUIRED_COLUMNS = {
    "scenario",
    "cycle_id",
    "valid_in",
    "light_base_q",
    "light_adapt_q",
    "refresh_decision_pre",
    "refresh_counter_pre",
    "refresh_counter_post",
    "baseline_nominal_ionic_formula_count_pre",
    "baseline_nominal_ionic_formula_count_post",
    "adaptive_recomputation_counter_pre",
    "adaptive_recomputation_counter_post",
    "i_photo_base_pre_q",
    "i_photo_adapt_pre_q",
    "i_photo_base_applied_q",
    "i_photo_adapt_applied_q",
    "i_total_base_pre_q",
    "i_total_adapt_live_pre_q",
    "i_total_adapt_applied_pre_q",
    "i_total_base_applied_q",
    "i_total_adapt_applied_q",
    "v_base_pre_q",
    "v_adapt_pre_q",
}
for _current in IONIC_CURRENTS:
    REQUIRED_COLUMNS.update(
        {
            f"{_current}_base_pre_q",
            f"{_current}_base_applied_q",
            f"{_current}_adapt_live_pre_q",
            f"{_current}_adapt_applied_q",
        }
    )
for _base_key, _adapt_key, _ in POST_STATE_PAIRS:
    REQUIRED_COLUMNS.update({_base_key, _adapt_key})


def _integer(row: Mapping[str, str], column: str, location: str) -> int:
    value = row.get(column)
    if value is None or value.strip() == "":
        raise ValueError(f"{location}: missing value for {column}")
    try:
        return int(value, 10)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{location}: malformed integer in {column}: {value!r}"
        ) from exc


def _signed_40_bit(value: int) -> int:
    value &= (1 << 40) - 1
    return value - (1 << 40) if value & (1 << 39) else value


def _validate_rows(
    rows: Iterable[Mapping[str, str]], fieldnames: List[str] | None = None
) -> Dict[int, List[Mapping[str, str]]]:
    if fieldnames is not None:
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("CSV contains duplicate column names")
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    scenarios: Dict[int, List[Mapping[str, str]]] = defaultdict(list)
    scenario_order: List[int] = []
    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"row {row_number}: unexpected extra CSV fields")
        if not REQUIRED_COLUMNS.issubset(row):
            missing = REQUIRED_COLUMNS - set(row)
            raise ValueError(
                f"row {row_number}: missing required columns: {', '.join(sorted(missing))}"
            )
        scenario = _integer(row, "scenario", f"row {row_number}")
        scenarios[scenario].append(row)
        scenario_order.append(scenario)
        for column in REQUIRED_COLUMNS:
            _integer(row, column, f"row {row_number}")

    unexpected = set(scenarios) - set(EXPECTED_SCENARIOS)
    missing_scenarios = set(EXPECTED_SCENARIOS) - set(scenarios)
    if unexpected or missing_scenarios:
        parts = []
        if missing_scenarios:
            parts.append(f"missing scenarios {sorted(missing_scenarios)}")
        if unexpected:
            parts.append(f"unexpected scenarios {sorted(unexpected)}")
        raise ValueError("; ".join(parts))

    for scenario in EXPECTED_SCENARIOS:
        trace = scenarios[scenario]
        if len(trace) != EXPECTED_CYCLES:
            raise ValueError(
                f"scenario {scenario}: expected {EXPECTED_CYCLES} rows, got {len(trace)}"
            )
        actual_cycles = [
            _integer(row, "cycle_id", f"scenario {scenario} row {index}")
            for index, row in enumerate(trace, start=1)
        ]
        expected_cycles = list(range(EXPECTED_CYCLES))
        if actual_cycles != expected_cycles:
            raise ValueError(
                f"scenario {scenario}: cycle IDs must occur in file order as "
                f"0..{EXPECTED_CYCLES - 1}; got {actual_cycles}"
            )

        last_refresh_light = 0
        refreshes = 0
        for cycle, row in enumerate(trace):
            location = f"scenario {scenario} cycle {cycle}"
            if _integer(row, "valid_in", location) != 1:
                raise ValueError(f"{location}: invalid samples are not accepted in this trace")
            base_light = _integer(row, "light_base_q", location)
            adapt_light = _integer(row, "light_adapt_q", location)
            if base_light != adapt_light:
                raise ValueError(f"{location}: baseline/adaptive light inputs differ")
            refresh = _integer(row, "refresh_decision_pre", location)
            if refresh not in (0, 1):
                raise ValueError(f"{location}: refresh decision must be 0 or 1")
            if cycle == 0 and refresh != 1:
                raise ValueError(f"{location}: first accepted sample must refresh")
            if base_light != last_refresh_light and not refresh:
                raise ValueError(f"{location}: light transition lacked a refresh")
            if refresh:
                refreshes += 1
                last_refresh_light = base_light

            baseline_pre = _integer(
                row, "baseline_nominal_ionic_formula_count_pre", location
            )
            baseline_post = _integer(
                row, "baseline_nominal_ionic_formula_count_post", location
            )
            adaptive_pre = _integer(row, "adaptive_recomputation_counter_pre", location)
            adaptive_post = _integer(
                row, "adaptive_recomputation_counter_post", location
            )
            expected_baseline_pre = cycle * len(IONIC_CURRENTS)
            expected_adaptive_pre = (
                refreshes - int(bool(refresh))
            ) * len(IONIC_CURRENTS)
            if baseline_pre != expected_baseline_pre:
                raise ValueError(f"{location}: baseline evaluation counter mismatch")
            if baseline_post != expected_baseline_pre + len(IONIC_CURRENTS):
                raise ValueError(f"{location}: baseline post-edge counter mismatch")
            if adaptive_pre != expected_adaptive_pre:
                raise ValueError(f"{location}: adaptive pre-edge counter mismatch")
            if adaptive_post != refreshes * len(IONIC_CURRENTS):
                raise ValueError(f"{location}: adaptive post-edge counter mismatch")

            base_components = _integer(row, "i_photo_base_applied_q", location)
            adapt_live_components = _integer(row, "i_photo_adapt_pre_q", location)
            adapt_applied_components = _integer(
                row, "i_photo_adapt_applied_q", location
            )
            for current in IONIC_CURRENTS:
                base_pre = _integer(row, f"{current}_base_pre_q", location)
                base_applied = _integer(row, f"{current}_base_applied_q", location)
                adapt_live = _integer(row, f"{current}_adapt_live_pre_q", location)
                adapt_applied = _integer(row, f"{current}_adapt_applied_q", location)
                if base_pre != base_applied:
                    raise ValueError(
                        f"{location}: baseline {current} pre-edge/applied values differ"
                    )
                if refresh and adapt_live != adapt_applied:
                    raise ValueError(
                        f"{location}: refreshed adaptive {current} is not the live value"
                    )
                base_components += base_applied
                adapt_live_components += adapt_live
                adapt_applied_components += adapt_applied

            for current in ("i_photo_base", "i_photo_adapt"):
                if _integer(row, f"{current}_pre_q", location) != _integer(
                    row, f"{current}_applied_q", location
                ):
                    raise ValueError(
                        f"{location}: {current} pre-edge/applied values differ"
                    )
            base_total = _integer(row, "i_total_base_applied_q", location)
            adapt_live_total = _integer(row, "i_total_adapt_live_pre_q", location)
            adapt_applied_total = _integer(row, "i_total_adapt_applied_q", location)
            if _integer(row, "i_total_base_pre_q", location) != base_total:
                raise ValueError(f"{location}: baseline total pre-edge/applied differs")
            if _integer(row, "i_total_adapt_applied_pre_q", location) != adapt_applied_total:
                raise ValueError(f"{location}: adaptive applied total differs")
            if _signed_40_bit(base_components) != base_total:
                raise ValueError(f"{location}: baseline total is not its Q16.24 sum")
            if _signed_40_bit(adapt_live_components) != adapt_live_total:
                raise ValueError(f"{location}: adaptive live total is not its Q16.24 sum")
            if _signed_40_bit(adapt_applied_components) != adapt_applied_total:
                raise ValueError(
                    f"{location}: adaptive applied total is not its Q16.24 sum"
                )
            if refresh and adapt_live_total != adapt_applied_total:
                raise ValueError(
                    f"{location}: adaptive refresh sample did not apply live total current"
                )

            refresh_counter = _integer(row, "refresh_counter_pre", location)
            refresh_counter_post = _integer(row, "refresh_counter_post", location)
            if refresh_counter < 0 or refresh_counter >= MAX_REFRESH_INTERVAL:
                raise ValueError(f"{location}: refresh counter violates maximum interval")
            expected_counter_post = 0 if refresh else refresh_counter + 1
            if refresh_counter_post != expected_counter_post:
                raise ValueError(f"{location}: post-edge refresh counter mismatch")

    expected_scenario_order = [
        scenario
        for scenario in EXPECTED_SCENARIOS
        for _ in range(EXPECTED_CYCLES)
    ]
    if scenario_order != expected_scenario_order:
        raise ValueError("scenario rows must remain in scenario-major file order")

    return scenarios


def summarize_rows(
    rows: Iterable[Mapping[str, str]], fieldnames: List[str] | None = None
) -> List[Dict[str, object]]:
    scenarios = _validate_rows(rows, fieldnames)
    summaries: List[Dict[str, object]] = []
    for scenario in EXPECTED_SCENARIOS:
        trace = scenarios[scenario]
        refreshes = sum(
            _integer(row, "refresh_decision_pre", f"scenario {scenario}")
            for row in trace
        )
        nominal_evaluations = refreshes * len(IONIC_CURRENTS)
        full_update_reference = len(trace) * len(IONIC_CURRENTS)
        metrics: Dict[str, object] = {
            "scenario": scenario,
            "cycles": len(trace),
            "refresh_events": refreshes,
            "adaptive_nominal_refresh_evaluations": nominal_evaluations,
            "full_update_reference_evaluations": full_update_reference,
            "nominal_refresh_count_reduction_percent": 100.0
            * (1.0 - nominal_evaluations / full_update_reference),
            "hardware_activity_measured": False,
            "voltage_error_is_guaranteed_bound": False,
        }
        for baseline_key, adaptive_key, key in POST_STATE_PAIRS:
            diffs = [
                _integer(row, adaptive_key, f"scenario {scenario}")
                - _integer(row, baseline_key, f"scenario {scenario}")
                for row in trace
            ]
            max_abs_raw = max(abs(value) for value in diffs)
            rms_raw = math.sqrt(sum(value * value for value in diffs) / len(diffs))
            metrics[f"{key}_observed_max_abs_error_raw"] = max_abs_raw
            metrics[f"{key}_observed_max_abs_error_q"] = max_abs_raw / SCALE
            metrics[f"{key}_observed_rms_error_raw"] = rms_raw
            metrics[f"{key}_observed_rms_error_q"] = rms_raw / SCALE

        applied_diffs = [
            _integer(row, "i_total_adapt_applied_q", f"scenario {scenario}")
            - _integer(row, "i_total_base_applied_q", f"scenario {scenario}")
            for row in trace
        ]
        max_applied_abs_raw = max(abs(value) for value in applied_diffs)
        rms_applied_raw = math.sqrt(
            sum(value * value for value in applied_diffs) / len(applied_diffs)
        )
        metrics["applied_total_current_observed_max_abs_difference_raw"] = (
            max_applied_abs_raw
        )
        metrics["applied_total_current_observed_max_abs_difference_pA"] = (
            max_applied_abs_raw / SCALE
        )
        metrics["applied_total_current_observed_rms_difference_raw"] = rms_applied_raw
        metrics["applied_total_current_observed_rms_difference_pA"] = (
            rms_applied_raw / SCALE
        )
        summaries.append(metrics)
    return summaries


def summarize_csv(path: Path) -> List[Dict[str, object]]:
    with path.open(newline="", encoding="ascii") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("CSV is empty or has no header")
        return summarize_rows(reader, reader.fieldnames)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate paired 4x40-cycle Vivado traces and report observed "
            "Q16.24 differences plus nominal refresh counts."
        )
    )
    parser.add_argument("trace_csv", type=Path)
    args = parser.parse_args()
    for summary in summarize_csv(args.trace_csv):
        print(
            f"scenario={summary['scenario']} cycles={summary['cycles']} "
            f"refreshes={summary['refresh_events']} "
            f"nominal_refresh_evaluations="
            f"{summary['adaptive_nominal_refresh_evaluations']}/"
            f"{summary['full_update_reference_evaluations']} "
            f"nominal_refresh_count_reduction="
            f"{summary['nominal_refresh_count_reduction_percent']:.2f}% "
            f"observed_v_max_abs_mV="
            f"{summary['v_membrane_observed_max_abs_error_q']:.9g} "
            f"observed_v_rms_mV="
            f"{summary['v_membrane_observed_rms_error_q']:.9g} "
            f"applied_i_total_max_abs_pA="
            f"{summary['applied_total_current_observed_max_abs_difference_pA']:.9g} "
            f"applied_i_total_rms_pA="
            f"{summary['applied_total_current_observed_rms_difference_pA']:.9g} "
            "hardware_activity_measured=False voltage_error_guaranteed_bound=False"
        )


if __name__ == "__main__":
    main()
