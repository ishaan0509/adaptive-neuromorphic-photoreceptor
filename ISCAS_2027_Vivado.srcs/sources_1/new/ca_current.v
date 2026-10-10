`timescale 1ns / 1ps

module ca_current #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] v_mem_q,
    input  signed [DATA_WIDTH-1:0] m_ca_q,
    input  signed [DATA_WIDTH-1:0] g_ca_q,
    input  signed [DATA_WIDTH-1:0] e_ca_q,
    output signed [DATA_WIDTH-1:0] i_ca_q
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

    wire signed [DATA_WIDTH-1:0] m2_q = qmul(m_ca_q, m_ca_q);
    wire signed [DATA_WIDTH-1:0] m3_q = qmul(m2_q, m_ca_q);
    wire signed [DATA_WIDTH-1:0] driving_force_q = v_mem_q - e_ca_q;
    assign i_ca_q = qmul(qmul(g_ca_q, m3_q), driving_force_q);
endmodule
