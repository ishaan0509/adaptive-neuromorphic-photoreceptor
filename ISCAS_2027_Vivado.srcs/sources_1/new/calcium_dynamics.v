`timescale 1ns / 1ps

module calcium_dynamics #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input clk,
    input reset,
    input valid_in,
    input signed [DATA_WIDTH-1:0] i_ca_pA_q,
    output reg signed [DATA_WIDTH-1:0] ca_i_mM_q,
    output reg signed [DATA_WIDTH-1:0] ca_s_mM_q,
    output reg signed [DATA_WIDTH-1:0] ca_f_mM_q,
    output reg valid_out
);
    localparam signed [DATA_WIDTH-1:0] CA_I_INIT_Q = 40'sd1845494;
    localparam signed [DATA_WIDTH-1:0] CA_S_INIT_Q = 40'sd1342177;
    localparam signed [DATA_WIDTH-1:0] CA_F_INIT_Q = 40'sd838861;
    localparam signed [DATA_WIDTH-1:0] CA_REST_Q = 40'sd503316;
    localparam signed [DATA_WIDTH-1:0] CA_I_RECOVERY_Q = 40'sd419430;
    localparam signed [DATA_WIDTH-1:0] CA_S_TRANSFER_Q = 40'sd838861;
    localparam signed [DATA_WIDTH-1:0] CA_F_TRANSFER_Q = 40'sd419430;
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

    wire signed [DATA_WIDTH-1:0] ca_i_recovery_q =
        qmul(ca_i_mM_q - CA_REST_Q, CA_I_RECOVERY_Q);
    wire signed [DATA_WIDTH-1:0] ca_s_delta_q =
        qmul(ca_i_mM_q - ca_s_mM_q, CA_S_TRANSFER_Q);
    wire signed [DATA_WIDTH-1:0] ca_f_delta_q =
        qmul(ca_s_mM_q - ca_f_mM_q, CA_F_TRANSFER_Q);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            ca_i_mM_q <= CA_I_INIT_Q;
            ca_s_mM_q <= CA_S_INIT_Q;
            ca_f_mM_q <= CA_F_INIT_Q;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            // The provisional calcium-current term is below one Q16.24 LSB.
            ca_i_mM_q <= ca_i_mM_q - ca_i_recovery_q;
            ca_s_mM_q <= ca_s_mM_q + ca_s_delta_q;
            ca_f_mM_q <= ca_f_mM_q + ca_f_delta_q;
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end
endmodule
