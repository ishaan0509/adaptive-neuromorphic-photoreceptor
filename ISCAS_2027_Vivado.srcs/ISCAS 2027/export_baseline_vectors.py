"""Export deterministic default-baseline Q16.24 traces as comparison CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, Mapping

from baseline_fixed_point import OBSERVABLE_ORDER, make_stimuli, simulate_stimulus


def export_scenario(output_dir: Path, name: str,
                    inputs: Iterable[Mapping[str, int]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"baseline_{name}_q16_24.csv"
    with target.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=OBSERVABLE_ORDER)
        writer.writeheader()
        writer.writerows(simulate_stimulus(inputs))
    return target


def export_all(output_dir: Path, cycles: int = 40) -> Dict[str, Path]:
    return {
        name: export_scenario(output_dir, name, inputs)
        for name, inputs in make_stimuli(cycles).items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export default baseline RTL expected values as raw integer CSVs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results" / "rtl_reference_vectors",
        help="destination folder (default: ISCAS 2027/results/rtl_reference_vectors)",
    )
    parser.add_argument("--cycles", type=int, default=40)
    args = parser.parse_args()
    for scenario, path in export_all(args.output_dir, args.cycles).items():
        print(f"{scenario}: {path}")


if __name__ == "__main__":
    main()
