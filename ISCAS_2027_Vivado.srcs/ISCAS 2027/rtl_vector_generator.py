import csv
from pathlib import Path

import numpy as np

from generate_stimuli import generate_light_suite
from photoreceptor_parameters import DEFAULT_PARAMETERS
from photoreceptor_reference import simulate_reference_model

BASE_DIR = Path(__file__).resolve().parent
VECTORS_DIR = BASE_DIR / "data" / "rtl_vectors"


def generate_fixed_point_vectors(stimulus_name: str, stimulus_payload: dict, width: int = 16, fractional_bits: int = 8):
    V = simulate_reference_model(stimulus=stimulus_payload, t_end=1.0, dt=1e-4)["V"]
    scale = 2 ** fractional_bits
    q_values = np.round(V * scale).astype(np.int64)
    q_values = np.clip(q_values, -(2 ** (width - 1)), 2 ** (width - 1) - 1)
    VECTORS_DIR.mkdir(parents=True, exist_ok=True)
    path = VECTORS_DIR / f"{stimulus_name}_rtl_vectors.csv"
    with path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time_index", "v_q"])
        for i, value in enumerate(q_values):
            writer.writerow([i, int(value)])
    return path


def main() -> None:
    suite = generate_light_suite(duration=1.0, dt=1e-4)
    for name, payload in suite.items():
        stim = {"type": "custom", "time": payload["t"], "signal": payload["amplitude"]}
        path = generate_fixed_point_vectors(name, stim)
        print(f"Saved RTL vector file: {path}")


if __name__ == "__main__":
    main()
