"""Bit-accurate cycle reference for the current default photoreceptor baseline RTL.

This models the RTL's 40-bit signed Q16.24 words, wrapped intermediate
assignments, arithmetic shifts, LUT, and synchronous state-update ordering.
It is a hardware-reference model only; the biological equations remain
provisional and unverified against the cited paper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

WIDTH = 40
FRAC_BITS = 24
SCALE = 1 << FRAC_BITS
MASK = (1 << WIDTH) - 1

LUT_VALUES = (
    5626, 9274, 15285, 25186, 41484, 68286, 112287, 184330,
    301759, 491778, 795674, 1272689, 1999893, 3060592, 4512088,
    6334081, 8388608, 10443135, 12265128, 13716624, 14777323,
    15504527, 15981542, 16285438, 16475457, 16592886, 16664929,
    16708930, 16735732, 16752030, 16761931, 16767942, 16771590,
)

CONSTANTS = {
    "g_h": 2013265920,
    "g_kv": 4194304000,
    "g_ca": 2348810240,
    "g_clca": 1509949440,
    "g_kca": 1342177280,
    "g_l": 335544320,
    "e_h": -335544320,
    "e_k": -1342177280,
    "e_ca": 1006632960,
    "e_cl": -1174405120,
    "e_l": -838860800,
    "k_clca": 6710886,
    "k_kca": 5872026,
    "cap_pf": 503316480,
    "dt_ms": 1677722,
    "photo_gain": 33554432000,
    "v_half_h": -754974720,
    "slope_h": 134217728,
    "dt_over_tau_h": 167772,
    "v_half_kv": -587202560,
    "slope_kv": 167772160,
    "dt_over_tau_kv": 83886,
    "v_half_ca": -503316480,
    "slope_ca": 134217728,
    "dt_over_tau_ca": 67109,
    "v_half_clca": -335544320,
    "slope_clca": 83886080,
    "dt_over_tau_clca": 55924,
    "v_half_kca": -419430400,
    "slope_kca": 100663296,
    "dt_over_tau_kca": 41943,
}

INITIAL_STATE = {
    "v_mem_q": -1006632960,
    "m_h_q": 2013266,
    "m_kv_q": 3019899,
    "m_ca_q": 3690988,
    "m_clca_q": 2516582,
    "m_kca_q": 1677722,
    "ca_i_q": 1845494,
    "ca_s_q": 1342177,
    "ca_f_q": 838861,
}

OBSERVABLE_ORDER = (
    "cycle", "reset", "valid_in", "light_q", "v_mem_q", "i_photo_q",
    "i_h_q", "i_kv_q", "i_ca_q", "i_clca_q", "i_kca_q", "i_l_q",
    "i_total_q", "m_h_q_out", "m_kv_q_out", "m_ca_q_out",
    "m_clca_q_out", "m_kca_q_out",
    "ca_i_q", "ca_s_q", "ca_f_q", "valid_out", "divide_by_zero",
)


def wrap_signed(value: int, width: int = WIDTH) -> int:
    """Return the signed two's-complement interpretation of a width-bit word."""
    mask = (1 << width) - 1
    value &= mask
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def qmul(lhs: int, rhs: int, width: int = WIDTH, frac_bits: int = FRAC_BITS) -> int:
    """RTL qmul: signed full-width product, arithmetic shift, low-width result."""
    product = wrap_signed(lhs, width) * wrap_signed(rhs, width)
    product = wrap_signed(product, 2 * width)
    return wrap_signed(product >> frac_bits, width)


def _trunc_div(numerator: int, denominator: int) -> int:
    """Signed integer division with Verilog's truncation toward zero."""
    if denominator == 0:
        raise ZeroDivisionError("RTL division by zero is guarded at its call site")
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def qdiv(numerator: int, denominator: int, width: int = WIDTH,
         frac_bits: int = FRAC_BITS) -> int:
    """RTL qdiv: sign-extend, left shift in 2W bits, divide, retain W bits."""
    numerator = wrap_signed(numerator, width)
    denominator = wrap_signed(denominator, width)
    scaled = wrap_signed(numerator, 2 * width) << frac_bits
    scaled = wrap_signed(scaled, 2 * width)
    quotient = _trunc_div(scaled, denominator)
    return wrap_signed(quotient, width)


def qadd(lhs: int, rhs: int, width: int = WIDTH) -> int:
    return wrap_signed(lhs + rhs, width)


def qsub(lhs: int, rhs: int, width: int = WIDTH) -> int:
    return wrap_signed(lhs - rhs, width)


def sigmoid_lut(x_q: int, width: int = WIDTH, frac_bits: int = FRAC_BITS) -> int:
    """Match sigmoid_lut.v's 33 entries, clipping, and integer index expression."""
    scale = wrap_signed(1 << frac_bits, width)
    x_limit = wrap_signed(8 * scale, width)
    half_step = wrap_signed(scale >> 1, width)
    x_q = wrap_signed(x_q, width)

    if x_q <= -x_limit:
        index = 0
    elif x_q >= x_limit:
        index = 32
    else:
        shifted = wrap_signed(x_q, width)
        shifted = wrap_signed(shifted + x_limit, 2 * width)
        shifted = wrap_signed(shifted + (scale >> 2), 2 * width)
        index = _trunc_div(shifted, half_step)
        index = max(0, min(32, index))
    return LUT_VALUES[index]


def _gate_next(v_mem_q: int, gate_q: int, v_half_q: int,
               slope_q: int, dt_over_tau_q: int) -> int:
    normalized_v = qdiv(qsub(v_mem_q, v_half_q), slope_q)
    target = sigmoid_lut(normalized_v)
    delta = qsub(target, gate_q)
    increment = qmul(delta, dt_over_tau_q)
    return qadd(gate_q, increment)


def _currents(state: Mapping[str, int], light_q: int) -> Dict[str, int]:
    v = state["v_mem_q"]
    photo = qmul(light_q, CONSTANTS["photo_gain"])

    ih = qmul(
        qmul(CONSTANTS["g_h"], state["m_h_q"]),
        qsub(v, CONSTANTS["e_h"]),
    )

    mkv2 = qmul(state["m_kv_q"], state["m_kv_q"])
    mkv3 = qmul(mkv2, state["m_kv_q"])
    ikv = qmul(qmul(CONSTANTS["g_kv"], mkv3), qsub(v, CONSTANTS["e_k"]))

    mca2 = qmul(state["m_ca_q"], state["m_ca_q"])
    mca3 = qmul(mca2, state["m_ca_q"])
    ica = qmul(qmul(CONSTANTS["g_ca"], mca3), qsub(v, CONSTANTS["e_ca"]))

    ca_clca_den = qadd(state["ca_i_q"], CONSTANTS["k_clca"])
    clca_invalid = ca_clca_den == 0
    if clca_invalid:
        iclca = 0
    else:
        clca_activation = qdiv(state["ca_i_q"], ca_clca_den)
        iclca = qmul(
            qmul(qmul(CONSTANTS["g_clca"], state["m_clca_q"]), clca_activation),
            qsub(v, CONSTANTS["e_cl"]),
        )

    ca_kca_den = qadd(state["ca_i_q"], CONSTANTS["k_kca"])
    kca_invalid = ca_kca_den == 0
    if kca_invalid:
        ikca = 0
    else:
        kca_activation = qdiv(state["ca_i_q"], ca_kca_den)
        ikca = qmul(
            qmul(qmul(CONSTANTS["g_kca"], state["m_kca_q"]), kca_activation),
            qsub(v, CONSTANTS["e_k"]),
        )

    leak = qmul(CONSTANTS["g_l"], qsub(v, CONSTANTS["e_l"]))
    total = 0
    for current in (photo, ih, ikv, ica, iclca, ikca, leak):
        total = qadd(total, current)

    return {
        "i_photo_q": photo,
        "i_h_q": ih,
        "i_kv_q": ikv,
        "i_ca_q": ica,
        "i_clca_q": iclca,
        "i_kca_q": ikca,
        "i_l_q": leak,
        "i_total_q": total,
        "clca_invalid_denominator": int(clca_invalid),
        "kca_invalid_denominator": int(kca_invalid),
    }


@dataclass
class BaselineFixedPoint:
    """Stateful cycle model of the current default baseline RTL."""

    width: int = WIDTH
    frac_bits: int = FRAC_BITS

    def __post_init__(self) -> None:
        if self.width != WIDTH or self.frac_bits != FRAC_BITS:
            raise ValueError("Only the RTL's default DATA_WIDTH=40, FRAC_BITS=24 is modeled")
        self.state: Dict[str, int] = {}
        self.membrane_valid = 0
        self.calcium_valid = 0
        self.membrane_divide_by_zero = 0
        self.reset()

    def reset(self) -> None:
        self.state = dict(INITIAL_STATE)
        self.membrane_valid = 0
        self.calcium_valid = 0
        self.membrane_divide_by_zero = 0

    def cycle(self, light_q: int = 0, valid_in: bool = True,
              reset: bool = False, cycle: int = 0) -> Dict[str, int]:
        """Apply one active-edge input and return post-edge combinational outputs.

        Currents and next-state equations are sampled from the pre-edge state.
        Output currents are then evaluated again from the post-edge state,
        matching continuous assignments observed after nonblocking assignments
        settle in a simulator.
        """
        light_q = wrap_signed(light_q, self.width)
        reset = bool(reset)
        valid_in = bool(valid_in)
        pre_state = dict(self.state)
        pre_currents = _currents(pre_state, light_q)

        if reset:
            self.reset()
        elif valid_in:
            cap = CONSTANTS["cap_pf"]
            if cap == 0:
                self.membrane_divide_by_zero = 1
            else:
                voltage_rate = qdiv(pre_currents["i_total_q"], cap)
                voltage_delta = qmul(voltage_rate, CONSTANTS["dt_ms"])
                self.state["v_mem_q"] = qsub(pre_state["v_mem_q"], voltage_delta)
                self.membrane_divide_by_zero = 0

            self.state["m_h_q"] = _gate_next(
                pre_state["v_mem_q"], pre_state["m_h_q"],
                CONSTANTS["v_half_h"], CONSTANTS["slope_h"],
                CONSTANTS["dt_over_tau_h"],
            )
            self.state["m_kv_q"] = _gate_next(
                pre_state["v_mem_q"], pre_state["m_kv_q"],
                CONSTANTS["v_half_kv"], CONSTANTS["slope_kv"],
                CONSTANTS["dt_over_tau_kv"],
            )
            self.state["m_ca_q"] = _gate_next(
                pre_state["v_mem_q"], pre_state["m_ca_q"],
                CONSTANTS["v_half_ca"], CONSTANTS["slope_ca"],
                CONSTANTS["dt_over_tau_ca"],
            )
            self.state["m_clca_q"] = _gate_next(
                pre_state["v_mem_q"], pre_state["m_clca_q"],
                CONSTANTS["v_half_clca"], CONSTANTS["slope_clca"],
                CONSTANTS["dt_over_tau_clca"],
            )
            self.state["m_kca_q"] = _gate_next(
                pre_state["v_mem_q"], pre_state["m_kca_q"],
                CONSTANTS["v_half_kca"], CONSTANTS["slope_kca"],
                CONSTANTS["dt_over_tau_kca"],
            )

            ca_i_recovery = qmul(
                qsub(pre_state["ca_i_q"], 503316), 419430
            )
            ca_s_delta = qmul(
                qsub(pre_state["ca_i_q"], pre_state["ca_s_q"]), 838861
            )
            ca_f_delta = qmul(
                qsub(pre_state["ca_s_q"], pre_state["ca_f_q"]), 419430
            )
            self.state["ca_i_q"] = qsub(pre_state["ca_i_q"], ca_i_recovery)
            self.state["ca_s_q"] = qadd(pre_state["ca_s_q"], ca_s_delta)
            self.state["ca_f_q"] = qadd(pre_state["ca_f_q"], ca_f_delta)
            self.calcium_valid = 1
            self.membrane_valid = 1
        else:
            self.membrane_valid = 0
            self.calcium_valid = 0
            self.membrane_divide_by_zero = 0

        post_currents = _currents(self.state, light_q)
        divide_by_zero = int(
            bool(self.membrane_divide_by_zero)
            or bool(post_currents["clca_invalid_denominator"])
            or bool(post_currents["kca_invalid_denominator"])
        )
        row = {
            "cycle": int(cycle),
            "reset": int(reset),
            "valid_in": int(valid_in),
            "light_q": light_q,
            **self.state,
            "m_h_q_out": self.state["m_h_q"],
            "m_kv_q_out": self.state["m_kv_q"],
            "m_ca_q_out": self.state["m_ca_q"],
            "m_clca_q_out": self.state["m_clca_q"],
            "m_kca_q_out": self.state["m_kca_q"],
            **{key: post_currents[key] for key in (
                "i_photo_q", "i_h_q", "i_kv_q", "i_ca_q", "i_clca_q",
                "i_kca_q", "i_l_q", "i_total_q",
            )},
            "valid_out": int(bool(self.membrane_valid and self.calcium_valid)),
            "divide_by_zero": divide_by_zero,
        }
        return {key: row[key] for key in OBSERVABLE_ORDER}


def make_stimuli(cycles: int = 40) -> Dict[str, List[Dict[str, int]]]:
    """Return deterministic all-valid dark, step, and pulse raw-Q stimuli."""
    if cycles < 2:
        raise ValueError("cycles must be at least 2")
    unit_light = SCALE
    step_start = max(1, cycles // 4)
    pulse_start = max(1, cycles // 4)
    pulse_stop = max(pulse_start + 1, (3 * cycles) // 8)

    def build(kind: str) -> List[Dict[str, int]]:
        result = []
        for idx in range(cycles):
            if kind == "dark":
                light = 0
            elif kind == "step":
                light = unit_light if idx >= step_start else 0
            else:
                light = unit_light if pulse_start <= idx < pulse_stop else 0
            result.append({"cycle": idx, "reset": int(idx == 0),
                           "valid_in": int(idx != 0), "light_q": light})
        return result

    return {name: build(name) for name in ("dark", "step", "pulse")}


def simulate_stimulus(inputs: Iterable[Mapping[str, int]]) -> List[Dict[str, int]]:
    model = BaselineFixedPoint()
    trace = []
    for item in inputs:
        trace.append(model.cycle(
            light_q=item.get("light_q", 0),
            valid_in=bool(item.get("valid_in", 1)),
            reset=bool(item.get("reset", 0)),
            cycle=int(item.get("cycle", len(trace))),
        ))
    return trace
