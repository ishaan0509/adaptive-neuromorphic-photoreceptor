"""Equivalence checks for narrower exact-width fixed-point intermediates."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from baseline_fixed_point import _trunc_div, wrap_signed


def _arith_width(width: int, frac_bits: int) -> int:
    return width + frac_bits if frac_bits <= width else 2 * width


def _old_qmul(lhs: int, rhs: int, width: int, frac_bits: int) -> int:
    product = wrap_signed(lhs, width) * wrap_signed(rhs, width)
    product = wrap_signed(product, 2 * width)
    return wrap_signed(product >> frac_bits, width)


def _narrow_qmul(lhs: int, rhs: int, width: int, frac_bits: int) -> int:
    product = wrap_signed(lhs, width) * wrap_signed(rhs, width)
    product = wrap_signed(product, _arith_width(width, frac_bits))
    return wrap_signed(product >> frac_bits, width)


def _old_qdiv(numerator: int, denominator: int, width: int, frac_bits: int) -> int:
    scaled = wrap_signed(wrap_signed(numerator, width) << frac_bits, 2 * width)
    return wrap_signed(_trunc_div(scaled, wrap_signed(denominator, width)), width)


def _narrow_qdiv(
    numerator: int, denominator: int, width: int, frac_bits: int
) -> int:
    scaled = wrap_signed(
        wrap_signed(numerator, width) << frac_bits,
        _arith_width(width, frac_bits),
    )
    return wrap_signed(_trunc_div(scaled, wrap_signed(denominator, width)), width)


@pytest.mark.parametrize("width", range(4, 9))
def test_narrowed_multiply_is_exhaustively_equivalent(width):
    values = range(-(1 << (width - 1)), 1 << (width - 1))
    for frac_bits in range(width + 1):
        for lhs in values:
            for rhs in values:
                assert _narrow_qmul(lhs, rhs, width, frac_bits) == _old_qmul(
                    lhs, rhs, width, frac_bits
                )


def test_q16_24_multiply_matches_full_width_at_extremes_and_random_values():
    width = 40
    frac_bits = 24
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    boundary_values = (minimum, minimum + 1, -1, 0, 1, maximum - 1, maximum)
    pairs = [(lhs, rhs) for lhs in boundary_values for rhs in boundary_values]
    rng = random.Random(0xCA1C1A)
    pairs.extend(
        (
            rng.randrange(minimum, maximum + 1),
            rng.randrange(minimum, maximum + 1),
        )
        for _ in range(3000)
    )
    for lhs, rhs in pairs:
        assert _narrow_qmul(lhs, rhs, width, frac_bits) == _old_qmul(
            lhs, rhs, width, frac_bits
        )


def test_narrowed_division_matches_full_width_with_signed_extremes():
    width = 40
    frac_bits = 24
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    numerators = (minimum, minimum + 1, -3, -1, 0, 1, 3, maximum - 1, maximum)
    denominators = (minimum, -17, -3, -1, 1, 2, 17, maximum)
    cases = [(n, d) for n in numerators for d in denominators]
    rng = random.Random(0xD171DE)
    cases.extend(
        (
            rng.randrange(minimum, maximum + 1),
            rng.choice((-maximum, -17, -3, -1, 1, 2, 17, maximum)),
        )
        for _ in range(3000)
    )
    for numerator, denominator in cases:
        assert _narrow_qdiv(numerator, denominator, width, frac_bits) == _old_qdiv(
            numerator, denominator, width, frac_bits
        )


def test_sigmoid_index_shift_matches_positive_power_of_two_division():
    frac_bits = 24
    scale = 1 << frac_bits
    limit = 8 * scale
    values = {-limit + 1, -limit + scale // 4, -1, 0, 1, limit - 1}
    rng = random.Random(0x519A01D)
    values.update(rng.randrange(-limit + 1, limit) for _ in range(3000))
    for x_q in values:
        shifted_x = x_q + limit + scale // 4
        old_index = _trunc_div(shifted_x, scale // 2)
        assert shifted_x > 0
        assert old_index == shifted_x >> (frac_bits - 1)


@pytest.mark.parametrize(
    ("slope_q", "v_half_q"),
    (
        (134217728, -754974720),
        (167772160, -587202560),
        (134217728, -503316480),
        (83886080, -335544320),
        (100663296, -419430400),
    ),
)
def test_gate_integer_slope_reduction_matches_qdiv(slope_q, v_half_q):
    width = 40
    frac_bits = 24
    scale = 1 << frac_bits
    assert slope_q % scale == 0
    slope_units = slope_q // scale
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    values = (minimum, minimum + 1, -1, 0, 1, maximum - 1, maximum)
    inputs = [(v, v_half_q) for v in values]
    rng = random.Random(slope_q ^ 0x6A7E)
    inputs.extend(
        (rng.randrange(minimum, maximum + 1), v_half_q)
        for _ in range(500)
    )
    for voltage, v_half in inputs:
        numerator = wrap_signed(voltage - v_half, width)
        original = _old_qdiv(numerator, slope_q, width, frac_bits)
        reduced = wrap_signed(_trunc_div(numerator, slope_units), width)
        assert reduced == original


def test_rtl_uses_reduced_intermediate_widths_in_both_shared_paths():
    rtl_dir = Path(__file__).resolve().parent.parent / "sources_1" / "new"
    multiply_modules = (
        "calcium_dynamics.v",
        "ca_current.v",
        "clca_current.v",
        "gate_update.v",
        "ih_current.v",
        "kca_current.v",
        "kv_current.v",
        "leakage_current.v",
        "membrane_voltage.v",
    )
    divide_modules = (
        "clca_current.v",
        "gate_update.v",
        "kca_current.v",
        "membrane_voltage.v",
    )
    for filename in multiply_modules:
        text = (rtl_dir / filename).read_text(encoding="ascii")
        assert "localparam integer Q_ARITH_WIDTH" in text
        assert "reg signed [Q_ARITH_WIDTH-1:0] product;" in text
    for filename in divide_modules:
        text = (rtl_dir / filename).read_text(encoding="ascii")
        assert "reg signed [Q_ARITH_WIDTH-1:0] scaled;" in text

    photo = (rtl_dir / "phototransduction.v").read_text(encoding="ascii")
    assert "wire signed [PRODUCT_WIDTH-1:0] product;" in photo
    sigmoid = (rtl_dir / "sigmoid_lut.v").read_text(encoding="ascii")
    assert "index = shifted_x >>> (FRAC_BITS - 1);" in sigmoid
    gate = (rtl_dir / "gate_update.v").read_text(encoding="ascii")
    assert "if ((SLOPE_Q != 0) && ((SLOPE_Q % SCALE_Q) == 0))" in gate
    assert "assign x_q = (v_mem_q - V_HALF_Q) / SLOPE_UNITS_Q;" in gate
