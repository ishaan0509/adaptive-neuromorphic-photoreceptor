import csv
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "rtl_outputs"


def decode_fixed_point(raw_values, width: int = 16, fractional_bits: int = 8):
    values = np.asarray(raw_values, dtype=np.int64)
    scale = 2 ** fractional_bits
    signed = values < 0
    decoded = values.astype(np.float64) / scale
    return decoded


def analyze_outputs(csv_path: str) -> dict:
    path = Path(csv_path)
    rows = []
    with path.open("r", newline="") as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    if len(rows) < 2:
        raise ValueError(f"{path} has insufficient rows")
    vals = [int(row[1]) for row in rows[1:]]
    decoded = decode_fixed_point(vals)
    return {"count": len(decoded), "mean": float(np.mean(decoded)), "std": float(np.std(decoded))}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = [0, 128, -128, 256, -256]
    decoded = decode_fixed_point(sample)
    print(decoded)


if __name__ == "__main__":
    main()
