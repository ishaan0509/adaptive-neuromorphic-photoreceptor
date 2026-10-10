`timescale 1ns / 1ps

module clca_current #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] v_mem_q,
    input  signed [DATA_WIDTH-1:0] m_clca_q,
    input  signed [DATA_WIDTH-1:0] ca_i_q,
    input  signed [DATA_WIDTH-1:0] g_clca_q,
    input  signed [DATA_WIDTH-1:0] e_cl_q,
    input  signed [DATA_WIDTH-1:0] k_clca_q,
    output reg signed [DATA_WIDTH-1:0] i_clca_q,
    output reg invalid_denominator
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

    wire signed [DATA_WIDTH-1:0] denominator_q = ca_i_q + k_clca_q;
    reg signed [DATA_WIDTH-1:0] activation_q;
    wire signed [DATA_WIDTH-1:0] driving_force_q = v_mem_q - e_cl_q;

    always @* begin
        invalid_denominator = (denominator_q == {DATA_WIDTH{1'b0}});
        if (invalid_denominator) begin
            activation_q = {DATA_WIDTH{1'b0}};
            i_clca_q = {DATA_WIDTH{1'b0}};
        end else begin
            activation_q = qdiv(ca_i_q, denominator_q);
            i_clca_q = qmul(qmul(qmul(g_clca_q, m_clca_q), activation_q), driving_force_q);
        end
    end
endmodule
