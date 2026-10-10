"""Run a solver-convergence check, not a paper-stimulus validation.

The deliberate zero J_hv input is an engineering test condition, not a
stimulus specified by Shah et al. Results are written to results/metrics.
"""

import csv
from pathlib import Path

from paper_biological_model import STATE_NAMES, simulate


def zero_input(_time_s: float) -> float:
    return 0.0


def main() -> None:
    duration_s = 0.005
    log_bases = ("e", "10")
    cases = (
        ("step", "coarse", 1e-4, 1e-10, 1e-12),
        ("step", "medium", 5e-5, 1e-10, 1e-12),
        ("step", "fine", 2.5e-5, 1e-10, 1e-12),
        ("tolerance", "coarse", 1e-4, 1e-5, 1e-7),
        ("tolerance", "medium", 1e-4, 1e-7, 1e-9),
        ("tolerance", "tight", 1e-4, 1e-9, 1e-11),
    )
    rows = []

    for log_base in log_bases:
        reference = simulate(
            duration_s,
            1.25e-5,
            zero_input,
            log_base,
            rtol=1e-12,
            atol=1e-14,
        )
        reference_end = reference["states"][-1]
        for sweep, name, max_step, rtol, atol in cases:
            result = simulate(
                duration_s,
                max_step,
                zero_input,
                log_base,
                rtol=rtol,
                atol=atol,
            )
            end = result["states"][-1]
            errors = {
                state_name: abs(end[state_name] - reference_end[state_name])
                for state_name in STATE_NAMES
            }
            row = {
                "condition": "synthetic zero input; not paper stimulus",
                "duration_s": duration_s,
                "log_base_branch": log_base,
                "sweep": sweep,
                "case": name,
                "max_step_s": max_step,
                "rtol": rtol,
                "atol": atol,
                "nfev": result["nfev"],
                "max_unscaled_abs_endpoint_state_difference": max(errors.values()),
                "reference_max_step_s": 1.25e-5,
                "reference_rtol": 1e-12,
                "reference_atol": 1e-14,
            }
            row.update({f"absdiff_{state_name}": error for state_name, error in errors.items()})
            rows.append(row)

    output = (
        Path(__file__).resolve().parent
        / "results"
        / "metrics"
        / "paper_model_solver_convergence.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(
            f"log={row['log_base_branch']} case={row['case']} "
            f"sweep={row['sweep']} "
            f"nfev={row['nfev']} max endpoint abs diff="
            f"{row['max_unscaled_abs_endpoint_state_difference']:.6g}"
        )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
