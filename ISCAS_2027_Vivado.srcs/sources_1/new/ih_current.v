`timescale 1ns / 1ps

module ih_current #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] v_mem_q,
    input  signed [DATA_WIDTH-1:0] m_h_q,
    input  signed [DATA_WIDTH-1:0] g_h_q,
    input  signed [DATA_WIDTH-1:0] e_h_q,
    output signed [DATA_WIDTH-1:0] i_h_q
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

    wire signed [DATA_WIDTH-1:0] driving_force = v_mem_q - e_h_q;
    assign i_h_q = qmul(qmul(g_h_q, m_h_q), driving_force);
endmodule
