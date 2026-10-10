`timescale 1ns / 1ps

module gate_update #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24,
    parameter signed [DATA_WIDTH-1:0] V_HALF_Q = 0,
    parameter signed [DATA_WIDTH-1:0] SLOPE_Q = 1,
    parameter signed [DATA_WIDTH-1:0] DT_OVER_TAU_Q = 1
)(
    input signed [DATA_WIDTH-1:0] v_mem_q,
    input signed [DATA_WIDTH-1:0] gate_q,
    output signed [DATA_WIDTH-1:0] gate_next_q
);
    localparam integer Q_ARITH_WIDTH =
        (FRAC_BITS <= DATA_WIDTH) ? (DATA_WIDTH + FRAC_BITS) : (2 * DATA_WIDTH);
    localparam signed [DATA_WIDTH-1:0] SCALE_Q = (1 << FRAC_BITS);
    localparam signed [DATA_WIDTH-1:0] SLOPE_UNITS_Q = SLOPE_Q >>> FRAC_BITS;

    function signed [DATA_WIDTH-1:0] qmul;
        input signed [DATA_WIDTH-1:0] lhs;
        input signed [DATA_WIDTH-1:0] rhs;
        reg signed [Q_ARITH_WIDTH-1:0] product;
        begin
            product = lhs * rhs;
            qmul = product >>> FRAC_BITS;
        end
    endfunction

    function signed [DATA_WIDTH-1:0] qdiv;
        input signed [DATA_WIDTH-1:0] numerator;
        input signed [DATA_WIDTH-1:0] denominator;
        reg signed [Q_ARITH_WIDTH-1:0] scaled;
        begin
            scaled = numerator;
            scaled = scaled <<< FRAC_BITS;
            qdiv = scaled / denominator;
        end
    endfunction

    wire signed [DATA_WIDTH-1:0] x_q;
    wire signed [DATA_WIDTH-1:0] gate_inf_q;
    wire signed [DATA_WIDTH-1:0] delta_q = gate_inf_q - gate_q;
    wire signed [DATA_WIDTH-1:0] increment_q;

    sigmoid_lut #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_sigmoid (
        .x_q(x_q),
        .y_q(gate_inf_q)
    );

    generate
        if ((SLOPE_Q != 0) && ((SLOPE_Q % SCALE_Q) == 0)) begin : g_integer_slope
            assign x_q = (v_mem_q - V_HALF_Q) / SLOPE_UNITS_Q;
        end else begin : g_general_slope
            assign x_q = qdiv(v_mem_q - V_HALF_Q, SLOPE_Q);
        end
    endgenerate

    assign increment_q = qmul(delta_q, DT_OVER_TAU_Q);
    assign gate_next_q = gate_q + increment_q;
endmodule
