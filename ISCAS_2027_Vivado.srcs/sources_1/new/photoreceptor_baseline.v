`timescale 1ns / 1ps

module photoreceptor_baseline #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input clk,
    input reset,
    input valid_in,
    input signed [DATA_WIDTH-1:0] light_q,
    output signed [DATA_WIDTH-1:0] v_mem_q,
    output signed [DATA_WIDTH-1:0] i_photo_q,
    output signed [DATA_WIDTH-1:0] i_h_q,
    output signed [DATA_WIDTH-1:0] i_kv_q,
    output signed [DATA_WIDTH-1:0] i_ca_q,
    output signed [DATA_WIDTH-1:0] i_clca_q,
    output signed [DATA_WIDTH-1:0] i_kca_q,
    output signed [DATA_WIDTH-1:0] i_l_q,
    output signed [DATA_WIDTH-1:0] i_total_q,
    output signed [DATA_WIDTH-1:0] ca_i_q,
    output signed [DATA_WIDTH-1:0] ca_s_q,
    output signed [DATA_WIDTH-1:0] ca_f_q,
    output signed [DATA_WIDTH-1:0] m_h_q_out,
    output signed [DATA_WIDTH-1:0] m_kv_q_out,
    output signed [DATA_WIDTH-1:0] m_ca_q_out,
    output signed [DATA_WIDTH-1:0] m_clca_q_out,
    output signed [DATA_WIDTH-1:0] m_kca_q_out,
    output valid_out,
    output divide_by_zero
);
    localparam signed [DATA_WIDTH-1:0] G_H_Q = 40'sd2013265920;
    localparam signed [DATA_WIDTH-1:0] G_KV_Q = 40'sd4194304000;
    localparam signed [DATA_WIDTH-1:0] G_CA_Q = 40'sd2348810240;
    localparam signed [DATA_WIDTH-1:0] G_CLCA_Q = 40'sd1509949440;
    localparam signed [DATA_WIDTH-1:0] G_KCA_Q = 40'sd1342177280;
    localparam signed [DATA_WIDTH-1:0] G_L_Q = 40'sd335544320;
    localparam signed [DATA_WIDTH-1:0] E_H_Q = -40'sd335544320;
    localparam signed [DATA_WIDTH-1:0] E_K_Q = -40'sd1342177280;
    localparam signed [DATA_WIDTH-1:0] E_CA_Q = 40'sd1006632960;
    localparam signed [DATA_WIDTH-1:0] E_CL_Q = -40'sd1174405120;
    localparam signed [DATA_WIDTH-1:0] E_L_Q = -40'sd838860800;
    localparam signed [DATA_WIDTH-1:0] K_CLCA_Q = 40'sd6710886;
    localparam signed [DATA_WIDTH-1:0] K_KCA_Q = 40'sd5872026;
    localparam signed [DATA_WIDTH-1:0] CAP_PF_Q = 40'sd503316480;
    localparam signed [DATA_WIDTH-1:0] DT_MS_Q = 40'sd1677722;

    reg signed [DATA_WIDTH-1:0] m_h_q;
    reg signed [DATA_WIDTH-1:0] m_kv_q;
    reg signed [DATA_WIDTH-1:0] m_ca_q;
    reg signed [DATA_WIDTH-1:0] m_clca_q;
    reg signed [DATA_WIDTH-1:0] m_kca_q;
    wire signed [DATA_WIDTH-1:0] m_h_next_q;
    wire signed [DATA_WIDTH-1:0] m_kv_next_q;
    wire signed [DATA_WIDTH-1:0] m_ca_next_q;
    wire signed [DATA_WIDTH-1:0] m_clca_next_q;
    wire signed [DATA_WIDTH-1:0] m_kca_next_q;
    wire signed [DATA_WIDTH-1:0] ca_i_wire_q;
    wire signed [DATA_WIDTH-1:0] ca_s_wire_q;
    wire signed [DATA_WIDTH-1:0] ca_f_wire_q;
    wire calcium_valid;
    wire signed [DATA_WIDTH-1:0] net_current_q;
    wire membrane_valid;
    wire membrane_divide_by_zero;
    wire clca_invalid_denominator;
    wire kca_invalid_denominator;

    assign ca_i_q = ca_i_wire_q;
    assign ca_s_q = ca_s_wire_q;
    assign ca_f_q = ca_f_wire_q;
    assign m_h_q_out = m_h_q;
    assign m_kv_q_out = m_kv_q;
    assign m_ca_q_out = m_ca_q;
    assign m_clca_q_out = m_clca_q;
    assign m_kca_q_out = m_kca_q;
    assign valid_out = membrane_valid && calcium_valid;
    assign divide_by_zero = membrane_divide_by_zero |
                            clca_invalid_denominator | kca_invalid_denominator;

    phototransduction #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_photo (
        .light_q(light_q),
        .i_photo_q(i_photo_q)
    );

    ih_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ih (
        .v_mem_q(v_mem_q), .m_h_q(m_h_q), .g_h_q(G_H_Q), .e_h_q(E_H_Q), .i_h_q(i_h_q)
    );
    kv_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kv (
        .v_mem_q(v_mem_q), .m_kv_q(m_kv_q), .g_kv_q(G_KV_Q), .e_k_q(E_K_Q), .i_kv_q(i_kv_q)
    );
    ca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ca (
        .v_mem_q(v_mem_q), .m_ca_q(m_ca_q), .g_ca_q(G_CA_Q), .e_ca_q(E_CA_Q), .i_ca_q(i_ca_q)
    );
    clca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_clca (
        .v_mem_q(v_mem_q), .m_clca_q(m_clca_q), .ca_i_q(ca_i_wire_q),
        .g_clca_q(G_CLCA_Q), .e_cl_q(E_CL_Q), .k_clca_q(K_CLCA_Q),
        .i_clca_q(i_clca_q), .invalid_denominator(clca_invalid_denominator)
    );
    kca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kca (
        .v_mem_q(v_mem_q), .m_kca_q(m_kca_q), .ca_i_q(ca_i_wire_q),
        .g_kca_q(G_KCA_Q), .e_k_q(E_K_Q), .k_kca_q(K_KCA_Q),
        .i_kca_q(i_kca_q), .invalid_denominator(kca_invalid_denominator)
    );
    leakage_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_leak (
        .v_mem_q(v_mem_q), .g_l_q(G_L_Q), .e_l_q(E_L_Q), .i_l_q(i_l_q)
    );

    assign i_total_q = i_photo_q + i_h_q + i_kv_q + i_ca_q + i_clca_q + i_kca_q + i_l_q;

    membrane_voltage #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_membrane (
        .clk(clk), .reset(reset), .valid_in(valid_in),
        .net_current_pA_q(i_total_q), .cap_pF_q(CAP_PF_Q), .dt_ms_q(DT_MS_Q),
        .v_mem_mV_q(v_mem_q), .valid_out(membrane_valid),
        .divide_by_zero(membrane_divide_by_zero)
    );

    calcium_dynamics #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_calcium (
        .clk(clk), .reset(reset), .valid_in(valid_in), .i_ca_pA_q(i_ca_q),
        .ca_i_mM_q(ca_i_wire_q), .ca_s_mM_q(ca_s_wire_q),
        .ca_f_mM_q(ca_f_wire_q), .valid_out(calcium_valid)
    );

    gate_update #(
        .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
        .V_HALF_Q(-40'sd754974720), .SLOPE_Q(40'sd134217728),
        .DT_OVER_TAU_Q(40'sd167772)
    ) u_gate_h (.v_mem_q(v_mem_q), .gate_q(m_h_q), .gate_next_q(m_h_next_q));
    gate_update #(
        .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
        .V_HALF_Q(-40'sd587202560), .SLOPE_Q(40'sd167772160),
        .DT_OVER_TAU_Q(40'sd83886)
    ) u_gate_kv (.v_mem_q(v_mem_q), .gate_q(m_kv_q), .gate_next_q(m_kv_next_q));
    gate_update #(
        .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
        .V_HALF_Q(-40'sd503316480), .SLOPE_Q(40'sd134217728),
        .DT_OVER_TAU_Q(40'sd67109)
    ) u_gate_ca (.v_mem_q(v_mem_q), .gate_q(m_ca_q), .gate_next_q(m_ca_next_q));
    gate_update #(
        .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
        .V_HALF_Q(-40'sd335544320), .SLOPE_Q(40'sd83886080),
        .DT_OVER_TAU_Q(40'sd55924)
    ) u_gate_clca (.v_mem_q(v_mem_q), .gate_q(m_clca_q), .gate_next_q(m_clca_next_q));
    gate_update #(
        .DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS),
        .V_HALF_Q(-40'sd419430400), .SLOPE_Q(40'sd100663296),
        .DT_OVER_TAU_Q(40'sd41943)
    ) u_gate_kca (.v_mem_q(v_mem_q), .gate_q(m_kca_q), .gate_next_q(m_kca_next_q));

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            m_h_q <= 40'sd2013266;
            m_kv_q <= 40'sd3019899;
            m_ca_q <= 40'sd3690988;
            m_clca_q <= 40'sd2516582;
            m_kca_q <= 40'sd1677722;
        end else if (valid_in) begin
            m_h_q <= m_h_next_q;
            m_kv_q <= m_kv_next_q;
            m_ca_q <= m_ca_next_q;
            m_clca_q <= m_clca_next_q;
            m_kca_q <= m_kca_next_q;
        end
    end
endmodule
