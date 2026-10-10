`timescale 1ns / 1ps

module leakage_current #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] v_mem_q,
    input  signed [DATA_WIDTH-1:0] g_l_q,
    input  signed [DATA_WIDTH-1:0] e_l_q,
    output signed [DATA_WIDTH-1:0] i_l_q
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

    wire signed [DATA_WIDTH-1:0] driving_force_q = v_mem_q - e_l_q;
    assign i_l_q = qmul(g_l_q, driving_force_q);
endmodule
