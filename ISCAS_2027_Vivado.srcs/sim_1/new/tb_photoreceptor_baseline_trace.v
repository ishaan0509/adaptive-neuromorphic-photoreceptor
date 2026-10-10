`timescale 1ns / 1ps

module tb_photoreceptor_baseline_trace;
    localparam integer DATA_WIDTH = 40;
    localparam integer FRAC_BITS = 24;
    localparam integer TRACE_CYCLES = 40;

    reg clk = 1'b0;
    reg reset = 1'b0;
    reg valid_in = 1'b0;
    reg signed [DATA_WIDTH-1:0] light_q = 0;

    wire signed [DATA_WIDTH-1:0] v_mem_q;
    wire signed [DATA_WIDTH-1:0] i_photo_q;
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
    wire signed [DATA_WIDTH-1:0] m_h_q_out;
    wire signed [DATA_WIDTH-1:0] m_kv_q_out;
    wire signed [DATA_WIDTH-1:0] m_ca_q_out;
    wire signed [DATA_WIDTH-1:0] m_clca_q_out;
    wire signed [DATA_WIDTH-1:0] m_kca_q_out;
    wire valid_out;
    wire divide_by_zero;

    integer total_failures = 0;
    integer file_handle;
    integer scan_count;
    integer row_index;
    reg [8*1024-1:0] csv_header;
    reg signed [DATA_WIDTH-1:0] expected_light_q;
    reg signed [DATA_WIDTH-1:0] expected_v_mem_q;
    reg signed [DATA_WIDTH-1:0] expected_i_photo_q;
    reg signed [DATA_WIDTH-1:0] expected_i_h_q;
    reg signed [DATA_WIDTH-1:0] expected_i_kv_q;
    reg signed [DATA_WIDTH-1:0] expected_i_ca_q;
    reg signed [DATA_WIDTH-1:0] expected_i_clca_q;
    reg signed [DATA_WIDTH-1:0] expected_i_kca_q;
    reg signed [DATA_WIDTH-1:0] expected_i_l_q;
    reg signed [DATA_WIDTH-1:0] expected_i_total_q;
    reg signed [DATA_WIDTH-1:0] expected_m_h_q;
    reg signed [DATA_WIDTH-1:0] expected_m_kv_q;
    reg signed [DATA_WIDTH-1:0] expected_m_ca_q;
    reg signed [DATA_WIDTH-1:0] expected_m_clca_q;
    reg signed [DATA_WIDTH-1:0] expected_m_kca_q;
    reg signed [DATA_WIDTH-1:0] expected_ca_i_q;
    reg signed [DATA_WIDTH-1:0] expected_ca_s_q;
    reg signed [DATA_WIDTH-1:0] expected_ca_f_q;
    integer expected_cycle;
    integer expected_reset;
    integer expected_valid_in;
    integer expected_valid_out;
    integer expected_divide_by_zero;

    photoreceptor_baseline #(
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_BITS(FRAC_BITS)
    ) uut (
        .clk(clk),
        .reset(reset),
        .valid_in(valid_in),
        .light_q(light_q),
        .v_mem_q(v_mem_q),
        .i_photo_q(i_photo_q),
        .i_h_q(i_h_q),
        .i_kv_q(i_kv_q),
        .i_ca_q(i_ca_q),
        .i_clca_q(i_clca_q),
        .i_kca_q(i_kca_q),
        .i_l_q(i_l_q),
        .i_total_q(i_total_q),
        .ca_i_q(ca_i_q),
        .ca_s_q(ca_s_q),
        .ca_f_q(ca_f_q),
        .m_h_q_out(m_h_q_out),
        .m_kv_q_out(m_kv_q_out),
        .m_ca_q_out(m_ca_q_out),
        .m_clca_q_out(m_clca_q_out),
        .m_kca_q_out(m_kca_q_out),
        .valid_out(valid_out),
        .divide_by_zero(divide_by_zero)
    );

    always #5 clk = ~clk;

    task compare_trace_file;
        input integer scenario_id;
        integer local_failures;
        begin
            case (scenario_id)
                0: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_dark_q16_24.csv",
                    "r"
                );
                1: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_step_q16_24.csv",
                    "r"
                );
                2: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_pulse_q16_24.csv",
                    "r"
                );
                3: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_alternating_q16_24.csv",
                    "r"
                );
                4: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_heldout_step_q16_24.csv",
                    "r"
                );
                5: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_heldout_pulse_q16_24.csv",
                    "r"
                );
                6: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_heldout_ramp_q16_24.csv",
                    "r"
                );
                7: file_handle = $fopen(
                    "C:/VivadoProjects/ISCAS_2027_Vivado/ISCAS_2027_Vivado.srcs/ISCAS 2027/results/rtl_reference_vectors/baseline_heldout_rapid_q16_24.csv",
                    "r"
                );
                default: file_handle = 0;
            endcase
            if (file_handle == 0) begin
                $display("FAIL: cannot open trace CSV for scenario ID %0d", scenario_id);
                total_failures = total_failures + 1;
            end else begin
                scan_count = $fgets(csv_header, file_handle);
                if (scan_count == 0) begin
                    $display("FAIL: missing CSV header for scenario ID %0d", scenario_id);
                    total_failures = total_failures + 1;
                end else begin
                    local_failures = 0;
                    for (row_index = 0; row_index < TRACE_CYCLES; row_index = row_index + 1) begin
                        scan_count = $fscanf(
                            file_handle,
                            "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                            expected_cycle,
                            expected_reset,
                            expected_valid_in,
                            expected_light_q,
                            expected_v_mem_q,
                            expected_i_photo_q,
                            expected_i_h_q,
                            expected_i_kv_q,
                            expected_i_ca_q,
                            expected_i_clca_q,
                            expected_i_kca_q,
                            expected_i_l_q,
                            expected_i_total_q,
                            expected_m_h_q,
                            expected_m_kv_q,
                            expected_m_ca_q,
                            expected_m_clca_q,
                            expected_m_kca_q,
                            expected_ca_i_q,
                            expected_ca_s_q,
                            expected_ca_f_q,
                            expected_valid_out,
                            expected_divide_by_zero
                        );
                        if (scan_count != 23) begin
                            $display("FAIL scenario %0d cycle %0d: expected 23 CSV fields, scanned %0d",
                                     scenario_id, row_index, scan_count);
                            local_failures = local_failures + 1;
                            row_index = TRACE_CYCLES;
                        end else begin
                            @(negedge clk);
                            reset = expected_reset[0];
                            valid_in = expected_valid_in[0];
                            light_q = expected_light_q;
                            @(posedge clk);
                            #1;

                            if (expected_cycle != row_index ||
                                v_mem_q !== expected_v_mem_q ||
                                i_photo_q !== expected_i_photo_q ||
                                i_h_q !== expected_i_h_q ||
                                i_kv_q !== expected_i_kv_q ||
                                i_ca_q !== expected_i_ca_q ||
                                i_clca_q !== expected_i_clca_q ||
                                i_kca_q !== expected_i_kca_q ||
                                i_l_q !== expected_i_l_q ||
                                i_total_q !== expected_i_total_q ||
                                m_h_q_out !== expected_m_h_q ||
                                m_kv_q_out !== expected_m_kv_q ||
                                m_ca_q_out !== expected_m_ca_q ||
                                m_clca_q_out !== expected_m_clca_q ||
                                m_kca_q_out !== expected_m_kca_q ||
                                ca_i_q !== expected_ca_i_q ||
                                ca_s_q !== expected_ca_s_q ||
                                ca_f_q !== expected_ca_f_q ||
                                valid_out !== expected_valid_out[0] ||
                                divide_by_zero !== expected_divide_by_zero[0]) begin
                                $display("FAIL scenario %0d cycle %0d", scenario_id, row_index);
                                $display("  expected V=%0d Iphoto=%0d Ih=%0d Ikv=%0d Ica=%0d Iclca=%0d Ikca=%0d Il=%0d Itotal=%0d",
                                         expected_v_mem_q, expected_i_photo_q, expected_i_h_q,
                                         expected_i_kv_q, expected_i_ca_q, expected_i_clca_q,
                                         expected_i_kca_q, expected_i_l_q, expected_i_total_q);
                                $display("  actual   V=%0d Iphoto=%0d Ih=%0d Ikv=%0d Ica=%0d Iclca=%0d Ikca=%0d Il=%0d Itotal=%0d",
                                         v_mem_q, i_photo_q, i_h_q, i_kv_q, i_ca_q,
                                         i_clca_q, i_kca_q, i_l_q, i_total_q);
                                $display("  expected gates=%0d,%0d,%0d,%0d,%0d calcium=%0d,%0d,%0d valid=%0d div0=%0d",
                                         expected_m_h_q, expected_m_kv_q, expected_m_ca_q,
                                         expected_m_clca_q, expected_m_kca_q,
                                         expected_ca_i_q, expected_ca_s_q, expected_ca_f_q,
                                         expected_valid_out, expected_divide_by_zero);
                                $display("  actual   gates=%0d,%0d,%0d,%0d,%0d calcium=%0d,%0d,%0d valid=%0d div0=%0d",
                                         m_h_q_out, m_kv_q_out, m_ca_q_out, m_clca_q_out,
                                         m_kca_q_out, ca_i_q, ca_s_q, ca_f_q,
                                         valid_out, divide_by_zero);
                                local_failures = local_failures + 1;
                            end
                        end
                    end
                    if (local_failures == 0) begin
                        $display("PASS scenario %0d: all %0d post-edge rows matched",
                                 scenario_id, TRACE_CYCLES);
                    end else begin
                        $display("FAIL scenario %0d: %0d of %0d rows differ",
                                 scenario_id, local_failures, TRACE_CYCLES);
                        total_failures = total_failures + local_failures;
                    end
                end
                $fclose(file_handle);
            end
        end
    endtask

    initial begin
        compare_trace_file(0);
        compare_trace_file(1);
        compare_trace_file(2);
        compare_trace_file(3);
        compare_trace_file(4);
        compare_trace_file(5);
        compare_trace_file(6);
        compare_trace_file(7);
        reset = 1'b0;
        valid_in = 1'b0;
        if (total_failures == 0)
            $display("PASS tb_photoreceptor_baseline_trace: 8 Python-generated Q16.24 trace comparisons");
        else
            $display("FAIL tb_photoreceptor_baseline_trace: total mismatches or file errors = %0d",
                     total_failures);
        $finish;
    end
endmodule
