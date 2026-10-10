import csv
from pathlib import Path
from typing import Dict, List

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
STIMULI_DIR = BASE_DIR / "data" / "stimuli"


def generate_step_stimulus(duration: float = 1.0, dt: float = 1e-4, amplitude: float = 1.0, t_on: float = 0.1):
    t = np.arange(0.0, duration + dt, dt)
    stim = np.zeros_like(t)
    stim[t >= t_on] = amplitude
    return t, stim


def generate_light_suite(duration: float = 1.0, dt: float = 1e-4) -> Dict[str, Dict[str, np.ndarray]]:
    suite: Dict[str, Dict[str, np.ndarray]] = {}
    t = np.arange(0.0, duration + dt, dt)
    suite["dark"] = {"t": t, "amplitude": np.zeros_like(t)}
    suite["step_up"] = {"t": t, "amplitude": np.where(t >= 0.2, 1.0, 0.0)}
    suite["step_down"] = {"t": t, "amplitude": np.where(t < 0.4, 1.0, 0.0)}
    suite["pulse"] = {"t": t, "amplitude": np.where((t >= 0.15) & (t <= 0.35), 1.0, 0.0)}
    suite["repeated_pulses"] = {"t": t, "amplitude": np.where(((t % 0.25) >= 0.05) & ((t % 0.25) <= 0.15), 1.0, 0.0)}
    suite["ramp"] = {"t": t, "amplitude": np.clip((t - 0.1) / 0.4, 0.0, 1.0)}
    suite["periodic"] = {"t": t, "amplitude": 0.5 * (1.0 + np.sin(2.0 * np.pi * 2.0 * t))}
    suite["abrupt_transitions"] = {"t": t, "amplitude": np.where(t < 0.2, 0.0, np.where(t < 0.4, 1.0, 0.2))}
    suite["steady_state"] = {"t": t, "amplitude": np.ones_like(t)}
    return suite


def save_suite_csv(suite: Dict[str, Dict[str, np.ndarray]], prefix: str = "stimulus") -> None:
    STIMULI_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in suite.items():
        path = STIMULI_DIR / f"{prefix}_{name}.csv"
        with path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["t", "amplitude"])
            for i in range(len(data["t"])):
                writer.writerow([float(data["t"][i]), float(data["amplitude"][i])])


def main() -> None:
    suite = generate_light_suite(duration=1.0, dt=1e-4)
    save_suite_csv(suite)
    print(f"Saved stimulus files to {STIMULI_DIR}")


if __name__ == "__main__":
    main()
