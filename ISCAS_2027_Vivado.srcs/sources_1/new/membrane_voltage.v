`timescale 1ns / 1ps

module membrane_voltage #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24,
    parameter signed [DATA_WIDTH-1:0] V_INIT_Q = -40'sd1006632960
)(
    input clk,
    input reset,
    input valid_in,
    input signed [DATA_WIDTH-1:0] net_current_pA_q,
    input signed [DATA_WIDTH-1:0] cap_pF_q,
    input signed [DATA_WIDTH-1:0] dt_ms_q,
    output reg signed [DATA_WIDTH-1:0] v_mem_mV_q,
    output reg valid_out,
    output reg divide_by_zero
);
    localparam integer Q_ARITH_WIDTH =
        (FRAC_BITS <= DATA_WIDTH) ? (DATA_WIDTH + FRAC_BITS) : (2 * DATA_WIDTH);

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

    wire signed [DATA_WIDTH-1:0] voltage_rate_q =
        (cap_pF_q == {DATA_WIDTH{1'b0}}) ? {DATA_WIDTH{1'b0}} :
        qdiv(net_current_pA_q, cap_pF_q);
    wire signed [DATA_WIDTH-1:0] voltage_delta_q = qmul(voltage_rate_q, dt_ms_q);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            v_mem_mV_q <= V_INIT_Q;
            valid_out <= 1'b0;
            divide_by_zero <= 1'b0;
        end else if (valid_in) begin
            divide_by_zero <= (cap_pF_q == {DATA_WIDTH{1'b0}});
            if (cap_pF_q != {DATA_WIDTH{1'b0}})
                v_mem_mV_q <= v_mem_mV_q - voltage_delta_q;
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
            divide_by_zero <= 1'b0;
        end
    end
endmodule
