`timescale 1ns / 1ps

module kv_current #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] v_mem_q,
    input  signed [DATA_WIDTH-1:0] m_kv_q,
    input  signed [DATA_WIDTH-1:0] g_kv_q,
    input  signed [DATA_WIDTH-1:0] e_k_q,
    output signed [DATA_WIDTH-1:0] i_kv_q
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

    wire signed [DATA_WIDTH-1:0] m2_q = qmul(m_kv_q, m_kv_q);
    wire signed [DATA_WIDTH-1:0] m3_q = qmul(m2_q, m_kv_q);
    wire signed [DATA_WIDTH-1:0] driving_force_q = v_mem_q - e_k_q;
    assign i_kv_q = qmul(qmul(g_kv_q, m3_q), driving_force_q);
endmodule
