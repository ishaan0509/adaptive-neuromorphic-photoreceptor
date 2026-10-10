import math
from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import numpy as np


@dataclass(frozen=True)
class FixedPointConfig:
    """Two's-complement fixed-point format: signed Q(I).F with I excluding sign."""

    width: int = 32
    fractional_bits: int = 16
    signed: bool = True
    rounding_mode: str = "nearest_even"
    saturation: bool = True

    def __post_init__(self) -> None:
        if self.width < 2:
            raise ValueError("width must be at least 2 bits")
        if self.fractional_bits < 0 or self.fractional_bits >= self.width:
            raise ValueError("fractional_bits must be in [0, width)")
        if not self.signed:
            raise ValueError("Only signed two's-complement formats are supported")
        if self.rounding_mode not in {"nearest_even", "half_away_from_zero", "truncate"}:
            raise ValueError(f"Unsupported rounding mode: {self.rounding_mode}")

    @property
    def integer_bits(self) -> int:
        return self.width - self.fractional_bits - 1

    @property
    def scale(self) -> int:
        return 1 << self.fractional_bits

    @property
    def raw_min(self) -> int:
        return -(1 << (self.width - 1))

    @property
    def raw_max(self) -> int:
        return (1 << (self.width - 1)) - 1

    @property
    def min_value(self) -> float:
        return self.raw_min / self.scale

    @property
    def max_value(self) -> float:
        return self.raw_max / self.scale


def quantize_fixed_point(value: float, config: FixedPointConfig) -> int:
    if not math.isfinite(value):
        raise ValueError(f"Cannot quantize non-finite value: {value}")
    scaled = value * config.scale
    if config.rounding_mode == "nearest_even":
        raw = round(scaled)
    elif config.rounding_mode == "half_away_from_zero":
        raw = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    else:
        raw = math.trunc(scaled)

    if config.saturation:
        return min(config.raw_max, max(config.raw_min, raw))
    if raw < config.raw_min or raw > config.raw_max:
        raise OverflowError(f"Fixed-point overflow: raw={raw}, width={config.width}")
    return raw


def fixed_point_to_float(raw: int, config: FixedPointConfig) -> float:
    if raw < config.raw_min or raw > config.raw_max:
        raise ValueError(f"Raw value {raw} is outside the configured signed range")
    return raw / config.scale


def decode_twos_complement(word: int, config: FixedPointConfig) -> float:
    """Decode an unsigned integer containing a width-bit two's-complement word."""
    if word < 0 or word >= (1 << config.width):
        raise ValueError(f"Encoded word {word} does not fit in {config.width} bits")
    raw = word - (1 << config.width) if word & (1 << (config.width - 1)) else word
    return raw / config.scale


def saturate_to_range(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError("low must not exceed high")
    return min(high, max(low, value))


def stable_sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def euler_step(states: np.ndarray, rhs_func: Callable[[np.ndarray], np.ndarray], dt: float) -> np.ndarray:
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be a finite positive number")
    states = np.asarray(states, dtype=np.float64)
    derivative = np.asarray(rhs_func(states), dtype=np.float64)
    if derivative.shape != states.shape:
        raise ValueError("rhs_func must return a derivative with the same shape as states")
    next_states = states + dt * derivative
    if not np.all(np.isfinite(next_states)):
        raise FloatingPointError("Euler step produced a non-finite state")
    return next_states


def solve_with_euler(
    rhs_func: Callable[[np.ndarray], np.ndarray],
    y0: np.ndarray,
    t_eval: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    times = np.asarray(t_eval, dtype=np.float64)
    if times.ndim != 1 or len(times) == 0 or not np.all(np.isfinite(times)):
        raise ValueError("t_eval must be a non-empty finite one-dimensional array")
    if len(times) > 1 and np.any(np.diff(times) <= 0):
        raise ValueError("t_eval must be strictly increasing")

    states = np.asarray(y0, dtype=np.float64)
    solution = np.zeros((len(times), len(states)), dtype=np.float64)
    solution[0] = states
    for idx in range(1, len(times)):
        dt = times[idx] - times[idx - 1]
        states = euler_step(states, rhs_func, dt)
        solution[idx] = states
    return times, solution


def report_solver_diagnostics(t: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    states = np.asarray(y, dtype=np.float64)
    times = np.asarray(t, dtype=np.float64)
    finite = np.isfinite(states)
    return {
        "min_voltage": float(np.nanmin(states[:, 0])) if states.ndim == 2 and states.shape[0] else float("nan"),
        "max_voltage": float(np.nanmax(states[:, 0])) if states.ndim == 2 and states.shape[0] else float("nan"),
        "nan_count": int(np.count_nonzero(~finite)),
        "finite_fraction": float(np.mean(finite)) if finite.size else 1.0,
        "t_duration": float(times[-1] - times[0]) if len(times) > 1 else 0.0,
    }
