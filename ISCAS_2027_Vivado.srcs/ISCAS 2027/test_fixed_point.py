from numerical_methods import FixedPointConfig, quantize_fixed_point


def test_fixed_point_quantization_works():
    cfg = FixedPointConfig(width=16, fractional_bits=8)
    value = 1.5
    q = quantize_fixed_point(value, cfg)
    assert isinstance(q, int)
    assert q == 384


def test_fixed_point_config_ranges_are_consistent():
    cfg = FixedPointConfig(width=16, fractional_bits=8)
    assert cfg.integer_bits == 7
    assert cfg.scale == 256
