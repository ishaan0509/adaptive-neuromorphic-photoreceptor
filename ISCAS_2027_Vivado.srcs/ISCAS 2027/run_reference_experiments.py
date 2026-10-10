import csv
from pathlib import Path

import numpy as np

from generate_stimuli import generate_light_suite
from photoreceptor_reference import save_reference_trace, simulate_reference_model

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results" / "metrics"


def run_suite() -> None:
    suite = generate_light_suite(duration=1.0, dt=1e-4)
    for name, payload in suite.items():
        stimulus = {"type": "custom", "signal": payload["amplitude"], "time": payload["t"]}
        sim = simulate_reference_model(stimulus=stimulus)
        save_reference_trace(sim, f"{name}_trace.csv")
        metrics = {
            "name": name,
            "v_min": float(np.min(sim["V"])),
            "v_max": float(np.max(sim["V"])),
            "v_rms": float(np.sqrt(np.mean(np.square(sim["V"])))),
            "i_max": float(np.max(sim["I_total"])),
        }
        path = RESULTS_DIR / f"{name}_metrics.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["name", "v_min", "v_max", "v_rms", "i_max"])
            writer.writerow([metrics["name"], metrics["v_min"], metrics["v_max"], metrics["v_rms"], metrics["i_max"]])
    print(f"Completed reference experiments in {RESULTS_DIR}")


def main() -> None:
    run_suite()


if __name__ == "__main__":
    main()
