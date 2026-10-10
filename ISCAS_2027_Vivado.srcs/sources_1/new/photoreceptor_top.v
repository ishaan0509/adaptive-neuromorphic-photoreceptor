`timescale 1ns / 1ps

module photoreceptor_top #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24,
    parameter integer ADAPTIVE_ENABLE = 1,
    parameter integer MAX_REFRESH_INTERVAL = 8,
    parameter integer OPERAND_ISOLATION_ENABLE = 1
)(
    input clk,
    input reset,
    input valid_in,
    input signed [DATA_WIDTH-1:0] light_q,
    output signed [DATA_WIDTH-1:0] v_mem_q,
    output signed [DATA_WIDTH-1:0] i_photo_q,
    output refresh_event,
    output valid_out
);
    wire signed [DATA_WIDTH-1:0] i_h_q;
    wire signed [DATA_WIDTH-1:0] i_kv_q;
    wire signed [DATA_WIDTH-1:0] i_ca_q;
    wire signed [DATA_WIDTH-1:0] i_clca_q;
    wire signed [DATA_WIDTH-1:0] i_kca_q;
    wire signed [DATA_WIDTH-1:0] i_l_q;
    wire signed [DATA_WIDTH-1:0] i_total_q;
    wire signed [DATA_WIDTH-1:0] ca_i_q;
    wire signed [DATA_WIDTH-1:0] ca_s_q;
    wire signed [DATA_WIDTH-1:0] ca_f_q;
    wire signed [DATA_WIDTH-1:0] m_h_q;
    wire signed [DATA_WIDTH-1:0] m_kv_q;
    wire signed [DATA_WIDTH-1:0] m_ca_q;
    wire signed [DATA_WIDTH-1:0] m_clca_q;
    wire signed [DATA_WIDTH-1:0] m_kca_q;
    wire divide_by_zero;

    generate
        if (ADAPTIVE_ENABLE != 0) begin : g_adaptive
            wire [15:0] refresh_counter;
            wire [31:0] recomputation_count;

            photoreceptor_adaptive #(
                .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
                .MAX_REFRESH_INTERVAL(MAX_REFRESH_INTERVAL),
                .OPERAND_ISOLATION_ENABLE(OPERAND_ISOLATION_ENABLE)
            ) u_adaptive (
                .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
                .v_mem_q(v_mem_q), .i_photo_q(i_photo_q),
                .i_h_q(i_h_q), .i_kv_q(i_kv_q), .i_ca_q(i_ca_q),
                .i_clca_q(i_clca_q), .i_kca_q(i_kca_q), .i_l_q(i_l_q),
                .i_total_q(i_total_q), .ca_i_q(ca_i_q), .ca_s_q(ca_s_q),
                .ca_f_q(ca_f_q), .m_h_q_out(m_h_q), .m_kv_q_out(m_kv_q),
                .m_ca_q_out(m_ca_q), .m_clca_q_out(m_clca_q),
                .m_kca_q_out(m_kca_q), .refresh_event(refresh_event),
                .refresh_counter(refresh_counter),
                .recomputation_count(recomputation_count),
                .valid_out(valid_out), .divide_by_zero(divide_by_zero)
            );
        end else begin : g_baseline
            photoreceptor_baseline #(
                .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)
            ) u_baseline (
                .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
                .v_mem_q(v_mem_q), .i_photo_q(i_photo_q),
                .i_h_q(i_h_q), .i_kv_q(i_kv_q), .i_ca_q(i_ca_q),
                .i_clca_q(i_clca_q), .i_kca_q(i_kca_q), .i_l_q(i_l_q),
                .i_total_q(i_total_q), .ca_i_q(ca_i_q), .ca_s_q(ca_s_q),
                .ca_f_q(ca_f_q), .m_h_q_out(m_h_q), .m_kv_q_out(m_kv_q),
                .m_ca_q_out(m_ca_q), .m_clca_q_out(m_clca_q),
                .m_kca_q_out(m_kca_q), .valid_out(valid_out),
                .divide_by_zero(divide_by_zero)
            );

            assign refresh_event = valid_out;
        end
    endgenerate
endmodule
