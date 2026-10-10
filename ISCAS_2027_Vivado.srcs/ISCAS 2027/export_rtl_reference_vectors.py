"""Export bit-accurate Q16.24 vectors for extra fixed and held-out stimuli."""

from __future__ import annotations

import csv
from pathlib import Path

from baseline_fixed_point import OBSERVABLE_ORDER, SCALE, simulate_stimulus

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "results" / "rtl_reference_vectors"
CYCLES = 40


def _inputs(light_values: list[int]) -> list[dict[str, int]]:
    return [
        {
            "cycle": index,
            "reset": int(index == 0),
            "valid_in": int(index != 0),
            "light_q": value,
        }
        for index, value in enumerate(light_values)
    ]


def _round_scaled(value: float) -> int:
    return int(round(value * SCALE))


def build_vectors() -> dict[str, list[dict[str, int]]]:
    cycle = list(range(CYCLES))
    return {
        "alternating": _inputs([SCALE if index % 2 else 0 for index in cycle]),
        "heldout_step": _inputs([_round_scaled(0.7 if index >= 7 else 0.0) for index in cycle]),
        "heldout_pulse": _inputs([
            _round_scaled(0.65 if 5 <= index < 8 or 26 <= index < 31 else 0.0)
            for index in cycle
        ]),
        "heldout_ramp": _inputs([_round_scaled(0.8 * index / (CYCLES - 1)) for index in cycle]),
        "heldout_rapid": _inputs([
            _round_scaled(0.8 if index % 7 < 2 else 0.0) for index in cycle
        ]),
    }


def export_vectors() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, stimulus in build_vectors().items():
        path = OUTPUT_DIR / f"baseline_{name}_q16_24.csv"
        trace = simulate_stimulus(stimulus)
        with path.open("w", newline="", encoding="ascii") as stream:
            writer = csv.DictWriter(stream, fieldnames=OBSERVABLE_ORDER)
            writer.writeheader()
            writer.writerows(trace)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for output in export_vectors():
        print(output)
