`timescale 1ns / 1ps

module tb_photoreceptor_comparison;
    localparam integer DATA_WIDTH = 40;
    localparam integer CYCLES = 40;
    localparam signed [DATA_WIDTH-1:0] UNIT_LIGHT_Q = 40'sd16777216;

    reg clk = 0;
    reg reset = 0;
    reg valid_in = 0;
    reg signed [DATA_WIDTH-1:0] light_q = 0;
    wire signed [DATA_WIDTH-1:0] v_base, i_photo_base, i_total_base;
    wire signed [DATA_WIDTH-1:0] ih_base, ikv_base, ica_base, iclca_base, ikca_base, il_base;
    wire signed [DATA_WIDTH-1:0] ca_i_base, ca_s_base, ca_f_base;
    wire signed [DATA_WIDTH-1:0] mh_base, mkv_base, mca_base, mclca_base, mkca_base;
    wire base_valid, base_divide_by_zero;
    wire signed [DATA_WIDTH-1:0] v_adapt, i_photo_adapt, i_total_adapt;
    wire signed [DATA_WIDTH-1:0] ih_adapt, ikv_adapt, ica_adapt, iclca_adapt, ikca_adapt, il_adapt;
    wire signed [DATA_WIDTH-1:0] ih_adapt_live, ikv_adapt_live, ica_adapt_live;
    wire signed [DATA_WIDTH-1:0] iclca_adapt_live, ikca_adapt_live, il_adapt_live;
    wire signed [DATA_WIDTH-1:0] i_total_adapt_live;
    wire signed [DATA_WIDTH-1:0] ca_i_adapt, ca_s_adapt, ca_f_adapt;
    wire signed [DATA_WIDTH-1:0] mh_adapt, mkv_adapt, mca_adapt, mclca_adapt, mkca_adapt;
    wire refresh_event, adapt_valid, adapt_divide_by_zero;
    wire [15:0] refresh_counter;
    wire [31:0] recomputation_count;
    wire signed [DATA_WIDTH-1:0] top_base_v, top_base_photo;
    wire top_base_refresh, top_base_valid;
    wire signed [DATA_WIDTH-1:0] top_adapt_v, top_adapt_photo;
    wire top_adapt_refresh, top_adapt_valid;
    wire signed [DATA_WIDTH-1:0] top_adapt_unisolated_v, top_adapt_unisolated_photo;
    wire top_adapt_unisolated_refresh, top_adapt_unisolated_valid;

    integer file_handle;
    integer scenario;
    integer cycle;
    integer failures = 0;
    integer baseline_ionic_evaluation_count = 0;
    reg signed [DATA_WIDTH-1:0] last_refresh_light;
    reg sampled_refresh;

    assign ih_adapt_live = adaptive.i_h_live_q;
    assign ikv_adapt_live = adaptive.i_kv_live_q;
    assign ica_adapt_live = adaptive.i_ca_live_q;
    assign iclca_adapt_live = adaptive.i_clca_live_q;
    assign ikca_adapt_live = adaptive.i_kca_live_q;
    assign il_adapt_live = adaptive.i_l_live_q;
    assign i_total_adapt_live = i_photo_adapt + ih_adapt_live + ikv_adapt_live +
                                ica_adapt_live + iclca_adapt_live +
                                ikca_adapt_live + il_adapt_live;

    photoreceptor_baseline baseline (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(v_base), .i_photo_q(i_photo_base), .i_h_q(ih_base),
        .i_kv_q(ikv_base), .i_ca_q(ica_base), .i_clca_q(iclca_base),
        .i_kca_q(ikca_base), .i_l_q(il_base), .i_total_q(i_total_base),
        .ca_i_q(ca_i_base), .ca_s_q(ca_s_base), .ca_f_q(ca_f_base),
        .m_h_q_out(mh_base), .m_kv_q_out(mkv_base), .m_ca_q_out(mca_base),
        .m_clca_q_out(mclca_base), .m_kca_q_out(mkca_base),
        .valid_out(base_valid), .divide_by_zero(base_divide_by_zero)
    );
    photoreceptor_adaptive adaptive (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(v_adapt), .i_photo_q(i_photo_adapt), .i_h_q(ih_adapt),
        .i_kv_q(ikv_adapt), .i_ca_q(ica_adapt), .i_clca_q(iclca_adapt),
        .i_kca_q(ikca_adapt), .i_l_q(il_adapt), .i_total_q(i_total_adapt),
        .ca_i_q(ca_i_adapt), .ca_s_q(ca_s_adapt), .ca_f_q(ca_f_adapt),
        .m_h_q_out(mh_adapt), .m_kv_q_out(mkv_adapt), .m_ca_q_out(mca_adapt),
        .m_clca_q_out(mclca_adapt), .m_kca_q_out(mkca_adapt),
        .refresh_event(refresh_event), .refresh_counter(refresh_counter),
        .recomputation_count(recomputation_count), .valid_out(adapt_valid),
        .divide_by_zero(adapt_divide_by_zero)
    );
    photoreceptor_top #(.ADAPTIVE_ENABLE(0)) baseline_top (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(top_base_v), .i_photo_q(top_base_photo),
        .refresh_event(top_base_refresh), .valid_out(top_base_valid)
    );
    photoreceptor_top #(.ADAPTIVE_ENABLE(1)) adaptive_top (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(top_adapt_v), .i_photo_q(top_adapt_photo),
        .refresh_event(top_adapt_refresh), .valid_out(top_adapt_valid)
    );
    photoreceptor_top #(
        .ADAPTIVE_ENABLE(1),
        .OPERAND_ISOLATION_ENABLE(0)
    ) adaptive_top_unisolated (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(top_adapt_unisolated_v),
        .i_photo_q(top_adapt_unisolated_photo),
        .refresh_event(top_adapt_unisolated_refresh),
        .valid_out(top_adapt_unisolated_valid)
    );

    always #5 clk = ~clk;

    function signed [DATA_WIDTH-1:0] scenario_light;
        input integer scenario_id;
        input integer cycle_id;
        begin
            case (scenario_id)
                0: scenario_light = 0;
                1: scenario_light = (cycle_id >= 10) ? UNIT_LIGHT_Q : 0;
                2: scenario_light = ((cycle_id >= 10) && (cycle_id < 16)) ?
                                      UNIT_LIGHT_Q : 0;
                default: scenario_light = (cycle_id % 2) ? UNIT_LIGHT_Q : 0;
            endcase
        end
    endfunction

    initial begin
        file_handle = $fopen(
            "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/metrics/adaptive_comparison_trace.csv",
            "w"
        );
        if (file_handle == 0) begin
            $display("FAIL could not create project results/metrics/adaptive_comparison_trace.csv");
            $finish;
        end
        $fdisplay(file_handle,
            "scenario,cycle_id,valid_in,light_base_q,light_adapt_q,refresh_decision_pre,refresh_counter_pre,baseline_nominal_ionic_formula_count_pre,adaptive_recomputation_counter_pre,i_photo_base_pre_q,i_photo_adapt_pre_q,i_photo_base_applied_q,i_photo_adapt_applied_q,ih_base_pre_q,ih_base_applied_q,ih_adapt_recompute_path_pre_q,ih_adapt_applied_q,ikv_base_pre_q,ikv_base_applied_q,ikv_adapt_recompute_path_pre_q,ikv_adapt_applied_q,ica_base_pre_q,ica_base_applied_q,ica_adapt_recompute_path_pre_q,ica_adapt_applied_q,iclca_base_pre_q,iclca_base_applied_q,iclca_adapt_recompute_path_pre_q,iclca_adapt_applied_q,ikca_base_pre_q,ikca_base_applied_q,ikca_adapt_recompute_path_pre_q,ikca_adapt_applied_q,il_base_pre_q,il_base_applied_q,il_adapt_recompute_path_pre_q,il_adapt_applied_q,i_total_base_pre_q,i_total_base_applied_q,i_total_adapt_recompute_path_pre_q,i_total_adapt_applied_pre_q,i_total_adapt_applied_q,v_base_pre_q,v_adapt_pre_q,baseline_nominal_ionic_formula_count_post,adaptive_recomputation_counter_post,refresh_counter_post,v_base_post_q,v_adapt_post_q,ca_i_base_post_q,ca_i_adapt_post_q,ca_s_base_post_q,ca_s_adapt_post_q,ca_f_base_post_q,ca_f_adapt_post_q,mh_base_post_q,mh_adapt_post_q,mkv_base_post_q,mkv_adapt_post_q,mca_base_post_q,mca_adapt_post_q,mclca_base_post_q,mclca_adapt_post_q,mkca_base_post_q,mkca_adapt_post_q");

        for (scenario = 0; scenario < 4; scenario = scenario + 1) begin
            @(negedge clk);
            reset = 1;
            valid_in = 0;
            light_q = 0;
            baseline_ionic_evaluation_count = 0;
            @(posedge clk);
            #1;
            @(negedge clk);
            reset = 0;
            last_refresh_light = 0;

            for (cycle = 0; cycle < CYCLES; cycle = cycle + 1) begin
                light_q = scenario_light(scenario, cycle);
                valid_in = 1;
                #1;
                sampled_refresh = refresh_event;
                if ((light_q != last_refresh_light) && !sampled_refresh) begin
                    $display("FAIL missed light-transition refresh scenario=%0d cycle=%0d",
                             scenario, cycle);
                    failures = failures + 1;
                end
                if (!sampled_refresh && refresh_counter >= 16'd7) begin
                    $display("FAIL maximum refresh interval exceeded scenario=%0d cycle=%0d",
                             scenario, cycle);
                    failures = failures + 1;
                end

                $fwrite(file_handle,
                    "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                    scenario, cycle, valid_in, light_q, light_q, sampled_refresh,
                    refresh_counter, baseline_ionic_evaluation_count,
                    recomputation_count);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    i_photo_base, i_photo_adapt, i_photo_base, i_photo_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    ih_base, ih_base, ih_adapt_live, ih_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    ikv_base, ikv_base, ikv_adapt_live, ikv_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    ica_base, ica_base, ica_adapt_live, ica_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    iclca_base, iclca_base, iclca_adapt_live, iclca_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    ikca_base, ikca_base, ikca_adapt_live, ikca_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d",
                    il_base, il_base, il_adapt_live, il_adapt);
                $fwrite(file_handle,
                    ",%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                    i_total_base, i_total_base, i_total_adapt_live,
                    i_total_adapt, i_total_adapt, v_base, v_adapt);

                @(posedge clk);
                #1;
                if (!base_valid || !adapt_valid || !top_base_valid ||
                    !top_adapt_valid || base_divide_by_zero ||
                    adapt_divide_by_zero || top_base_v !== v_base ||
                    top_base_photo !== i_photo_base ||
                    top_adapt_v !== v_adapt || top_adapt_photo !== i_photo_adapt ||
                    top_base_refresh !== top_base_valid ||
                    top_adapt_refresh !== refresh_event ||
                    top_adapt_unisolated_v !== top_adapt_v ||
                    top_adapt_unisolated_photo !== top_adapt_photo ||
                    top_adapt_unisolated_refresh !== top_adapt_refresh ||
                    top_adapt_unisolated_valid !== top_adapt_valid) begin
                    $display("FAIL validity or divide-by-zero scenario=%0d cycle=%0d",
                             scenario, cycle);
                    failures = failures + 1;
                end
                baseline_ionic_evaluation_count =
                    baseline_ionic_evaluation_count + 6;
                $fdisplay(file_handle,
                    ",%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                    baseline_ionic_evaluation_count, recomputation_count,
                    refresh_counter, v_base, v_adapt, ca_i_base, ca_i_adapt,
                    ca_s_base, ca_s_adapt, ca_f_base, ca_f_adapt,
                    mh_base, mh_adapt, mkv_base, mkv_adapt,
                    mca_base, mca_adapt, mclca_base, mclca_adapt,
                    mkca_base, mkca_adapt);

                if (sampled_refresh)
                    last_refresh_light = light_q;
                @(negedge clk);
            end
            valid_in = 0;
        end

        $fclose(file_handle);
        if (failures == 0)
            $display("PASS comparison trace captured: 4 scenarios x %0d cycles", CYCLES);
        else
            $display("FAIL comparison trace checks: %0d failures", failures);
        $finish;
    end
endmodule
