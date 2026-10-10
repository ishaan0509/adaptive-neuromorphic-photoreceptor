`timescale 1ns / 1ps

module photoreceptor_adaptive #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24,
    parameter signed [DATA_WIDTH-1:0] VOLTAGE_THRESHOLD_Q = 40'sd16777216,
    parameter [DATA_WIDTH-1:0] ERROR_BUDGET_Q = 40'd1677722,
    parameter integer MAX_REFRESH_INTERVAL = 8,
    parameter integer OPERAND_ISOLATION_ENABLE = 1
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
    output refresh_event,
    output [15:0] refresh_counter,
    output reg [31:0] recomputation_count,
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
    wire membrane_valid;
    wire membrane_divide_by_zero;
    wire clca_invalid_denominator;
    wire kca_invalid_denominator;
    wire scheduler_valid;

    wire signed [DATA_WIDTH-1:0] i_h_live_q;
    wire signed [DATA_WIDTH-1:0] i_kv_live_q;
    wire signed [DATA_WIDTH-1:0] i_ca_live_q;
    wire signed [DATA_WIDTH-1:0] i_clca_live_q;
    wire signed [DATA_WIDTH-1:0] i_kca_live_q;
    wire signed [DATA_WIDTH-1:0] i_l_live_q;
    reg signed [DATA_WIDTH-1:0] isolated_v_q;
    reg signed [DATA_WIDTH-1:0] isolated_m_h_q;
    reg signed [DATA_WIDTH-1:0] isolated_m_kv_q;
    reg signed [DATA_WIDTH-1:0] isolated_m_ca_q;
    reg signed [DATA_WIDTH-1:0] isolated_m_clca_q;
    reg signed [DATA_WIDTH-1:0] isolated_m_kca_q;
    reg signed [DATA_WIDTH-1:0] isolated_ca_i_q;
    wire signed [DATA_WIDTH-1:0] current_v_q;
    wire signed [DATA_WIDTH-1:0] current_m_h_q;
    wire signed [DATA_WIDTH-1:0] current_m_kv_q;
    wire signed [DATA_WIDTH-1:0] current_m_ca_q;
    wire signed [DATA_WIDTH-1:0] current_m_clca_q;
    wire signed [DATA_WIDTH-1:0] current_m_kca_q;
    wire signed [DATA_WIDTH-1:0] current_ca_i_q;
    reg signed [DATA_WIDTH-1:0] i_h_cache_q;
    reg signed [DATA_WIDTH-1:0] i_kv_cache_q;
    reg signed [DATA_WIDTH-1:0] i_ca_cache_q;
    reg signed [DATA_WIDTH-1:0] i_clca_cache_q;
    reg signed [DATA_WIDTH-1:0] i_kca_cache_q;
    reg signed [DATA_WIDTH-1:0] i_l_cache_q;
    reg cache_initialized;
    reg signed [DATA_WIDTH-1:0] voltage_at_refresh_q;
    reg signed [DATA_WIDTH-1:0] light_at_refresh_q;
    reg signed [DATA_WIDTH-1:0] previous_voltage_q;
    wire signed [DATA_WIDTH-1:0] selected_h_q;
    wire signed [DATA_WIDTH-1:0] selected_kv_q;
    wire signed [DATA_WIDTH-1:0] selected_ca_q;
    wire signed [DATA_WIDTH-1:0] selected_clca_q;
    wire signed [DATA_WIDTH-1:0] selected_kca_q;
    wire signed [DATA_WIDTH-1:0] selected_l_q;
    wire refresh_all;
    wire budget_exhausted;
    wire [DATA_WIDTH-1:0] budget_value_q;
    wire budget_valid;
    wire [DATA_WIDTH-1:0] estimated_error_increment_q;
    wire signed [DATA_WIDTH:0] voltage_step_wide =
        {v_mem_q[DATA_WIDTH-1], v_mem_q} -
        {previous_voltage_q[DATA_WIDTH-1], previous_voltage_q};
    wire [DATA_WIDTH:0] voltage_step_magnitude =
        voltage_step_wide[DATA_WIDTH] ? -voltage_step_wide : voltage_step_wide;

    assign estimated_error_increment_q = voltage_step_magnitude[DATA_WIDTH:4];
    assign current_v_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                         v_mem_q : isolated_v_q;
    assign current_m_h_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                           m_h_q : isolated_m_h_q;
    assign current_m_kv_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                            m_kv_q : isolated_m_kv_q;
    assign current_m_ca_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                            m_ca_q : isolated_m_ca_q;
    assign current_m_clca_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                              m_clca_q : isolated_m_clca_q;
    assign current_m_kca_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                             m_kca_q : isolated_m_kca_q;
    assign current_ca_i_q = (OPERAND_ISOLATION_ENABLE == 0 || refresh_all) ?
                            ca_i_wire_q : isolated_ca_i_q;
    assign selected_h_q = (refresh_all || !cache_initialized) ? i_h_live_q : i_h_cache_q;
    assign selected_kv_q = (refresh_all || !cache_initialized) ? i_kv_live_q : i_kv_cache_q;
    assign selected_ca_q = (refresh_all || !cache_initialized) ? i_ca_live_q : i_ca_cache_q;
    assign selected_clca_q = (refresh_all || !cache_initialized) ? i_clca_live_q : i_clca_cache_q;
    assign selected_kca_q = (refresh_all || !cache_initialized) ? i_kca_live_q : i_kca_cache_q;
    assign selected_l_q = (refresh_all || !cache_initialized) ? i_l_live_q : i_l_cache_q;
    assign ca_i_q = ca_i_wire_q;
    assign ca_s_q = ca_s_wire_q;
    assign ca_f_q = ca_f_wire_q;
    assign m_h_q_out = m_h_q;
    assign m_kv_q_out = m_kv_q;
    assign m_ca_q_out = m_ca_q;
    assign m_clca_q_out = m_clca_q;
    assign m_kca_q_out = m_kca_q;
    assign i_h_q = selected_h_q;
    assign i_kv_q = selected_kv_q;
    assign i_ca_q = selected_ca_q;
    assign i_clca_q = selected_clca_q;
    assign i_kca_q = selected_kca_q;
    assign i_l_q = selected_l_q;
    assign i_total_q = i_photo_q + selected_h_q + selected_kv_q +
                       selected_ca_q + selected_clca_q + selected_kca_q +
                       selected_l_q;
    assign valid_out = membrane_valid && calcium_valid && scheduler_valid;
    assign divide_by_zero = membrane_divide_by_zero |
                            clca_invalid_denominator | kca_invalid_denominator;
    assign refresh_event = refresh_all;

    phototransduction #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_photo (
        .light_q(light_q), .i_photo_q(i_photo_q)
    );
    ih_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ih (
        .v_mem_q(current_v_q), .m_h_q(current_m_h_q), .g_h_q(G_H_Q), .e_h_q(E_H_Q),
        .i_h_q(i_h_live_q)
    );
    kv_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kv (
        .v_mem_q(current_v_q), .m_kv_q(current_m_kv_q), .g_kv_q(G_KV_Q), .e_k_q(E_K_Q),
        .i_kv_q(i_kv_live_q)
    );
    ca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ca (
        .v_mem_q(current_v_q), .m_ca_q(current_m_ca_q), .g_ca_q(G_CA_Q), .e_ca_q(E_CA_Q),
        .i_ca_q(i_ca_live_q)
    );
    clca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_clca (
        .v_mem_q(current_v_q), .m_clca_q(current_m_clca_q), .ca_i_q(current_ca_i_q),
        .g_clca_q(G_CLCA_Q), .e_cl_q(E_CL_Q), .k_clca_q(K_CLCA_Q),
        .i_clca_q(i_clca_live_q), .invalid_denominator(clca_invalid_denominator)
    );
    kca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kca (
        .v_mem_q(current_v_q), .m_kca_q(current_m_kca_q), .ca_i_q(current_ca_i_q),
        .g_kca_q(G_KCA_Q), .e_k_q(E_K_Q), .k_kca_q(K_KCA_Q),
        .i_kca_q(i_kca_live_q), .invalid_denominator(kca_invalid_denominator)
    );
    leakage_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_leak (
        .v_mem_q(current_v_q), .g_l_q(G_L_Q), .e_l_q(E_L_Q), .i_l_q(i_l_live_q)
    );

    current_update_scheduler #(
        .DATA_WIDTH(DATA_WIDTH),
        .VOLTAGE_THRESHOLD_Q(VOLTAGE_THRESHOLD_Q),
        .MAX_REFRESH_INTERVAL(MAX_REFRESH_INTERVAL)
    ) u_scheduler (
        .clk(clk), .reset(reset), .valid_in(valid_in),
        .voltage_q(v_mem_q), .voltage_at_refresh_q(voltage_at_refresh_q),
        .light_q(light_q), .light_at_refresh_q(light_at_refresh_q),
        .force_refresh(1'b0), .budget_exhausted(budget_exhausted),
        .refresh_all(refresh_all), .refresh_counter(refresh_counter),
        .valid_out(scheduler_valid)
    );
    voltage_error_budget #(
        .DATA_WIDTH(DATA_WIDTH), .BUDGET_LIMIT_Q(ERROR_BUDGET_Q)
    ) u_error_budget (
        .clk(clk), .reset(reset), .valid_in(valid_in), .clear(refresh_all),
        .estimated_error_increment_q(estimated_error_increment_q),
        .budget_value_q(budget_value_q), .budget_exhausted(budget_exhausted),
        .valid_out(budget_valid)
    );

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
            isolated_v_q <= -40'sd1006632960;
            isolated_m_h_q <= 40'sd2013266;
            isolated_m_kv_q <= 40'sd3019899;
            isolated_m_ca_q <= 40'sd3690988;
            isolated_m_clca_q <= 40'sd2516582;
            isolated_m_kca_q <= 40'sd1677722;
            isolated_ca_i_q <= 40'sd1845494;
            i_h_cache_q <= {DATA_WIDTH{1'b0}};
            i_kv_cache_q <= {DATA_WIDTH{1'b0}};
            i_ca_cache_q <= {DATA_WIDTH{1'b0}};
            i_clca_cache_q <= {DATA_WIDTH{1'b0}};
            i_kca_cache_q <= {DATA_WIDTH{1'b0}};
            i_l_cache_q <= {DATA_WIDTH{1'b0}};
            cache_initialized <= 1'b0;
            voltage_at_refresh_q <= -40'sd1006632960;
            light_at_refresh_q <= {DATA_WIDTH{1'b0}};
            previous_voltage_q <= -40'sd1006632960;
            recomputation_count <= 32'd0;
        end else if (valid_in) begin
            m_h_q <= m_h_next_q;
            m_kv_q <= m_kv_next_q;
            m_ca_q <= m_ca_next_q;
            m_clca_q <= m_clca_next_q;
            m_kca_q <= m_kca_next_q;
            previous_voltage_q <= v_mem_q;
            if (refresh_all) begin
                i_h_cache_q <= i_h_live_q;
                i_kv_cache_q <= i_kv_live_q;
                i_ca_cache_q <= i_ca_live_q;
                i_clca_cache_q <= i_clca_live_q;
                i_kca_cache_q <= i_kca_live_q;
                i_l_cache_q <= i_l_live_q;
                if (OPERAND_ISOLATION_ENABLE != 0) begin
                    isolated_v_q <= v_mem_q;
                    isolated_m_h_q <= m_h_q;
                    isolated_m_kv_q <= m_kv_q;
                    isolated_m_ca_q <= m_ca_q;
                    isolated_m_clca_q <= m_clca_q;
                    isolated_m_kca_q <= m_kca_q;
                    isolated_ca_i_q <= ca_i_wire_q;
                end
                voltage_at_refresh_q <= v_mem_q;
                light_at_refresh_q <= light_q;
                if (recomputation_count > 32'hffff_fff9)
                    recomputation_count <= 32'hffff_ffff;
                else
                    recomputation_count <= recomputation_count + 32'd6;
                cache_initialized <= 1'b1;
            end
        end
    end
endmodule
