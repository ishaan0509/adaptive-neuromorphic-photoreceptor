`timescale 1ns / 1ps

module tb_photoreceptor_baseline;
    localparam integer DATA_WIDTH = 40;
    localparam integer FRAC_BITS = 24;
    localparam signed [DATA_WIDTH-1:0] Q_ONE = 40'sd16777216;
    localparam signed [DATA_WIDTH-1:0] V_INIT = -40'sd1006632960;
    localparam signed [DATA_WIDTH-1:0] V_AFTER_DARK_STEP = -40'sd958630687;
    localparam signed [DATA_WIDTH-1:0] IONIC_TOTAL_INIT = -40'sd14400678440;

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
    wire signed [DATA_WIDTH-1:0] m_h_q;
    wire signed [DATA_WIDTH-1:0] m_kv_q;
    wire signed [DATA_WIDTH-1:0] m_ca_q;
    wire signed [DATA_WIDTH-1:0] m_clca_q;
    wire signed [DATA_WIDTH-1:0] m_kca_q;
    wire valid_out;
    wire divide_by_zero;
    reg signed [DATA_WIDTH-1:0] v_after_first;
    reg signed [DATA_WIDTH-1:0] v_before_idle;
    reg signed [DATA_WIDTH-1:0] gate_h_after_reset;
    reg signed [DATA_WIDTH-1:0] ca_i_after_reset;

    photoreceptor_baseline #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) uut (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(v_mem_q), .i_photo_q(i_photo_q),
        .i_h_q(i_h_q), .i_kv_q(i_kv_q), .i_ca_q(i_ca_q),
        .i_clca_q(i_clca_q), .i_kca_q(i_kca_q), .i_l_q(i_l_q),
        .i_total_q(i_total_q), .ca_i_q(ca_i_q), .ca_s_q(ca_s_q), .ca_f_q(ca_f_q),
        .m_h_q_out(m_h_q), .m_kv_q_out(m_kv_q), .m_ca_q_out(m_ca_q),
        .m_clca_q_out(m_clca_q), .m_kca_q_out(m_kca_q),
        .valid_out(valid_out), .divide_by_zero(divide_by_zero)
    );

    always #5 clk = ~clk;

    initial begin
        reset = 1'b1;
        #2;
        if (v_mem_q !== V_INIT || m_h_q !== 40'sd2013266 ||
            m_kv_q !== 40'sd3019899 || m_ca_q !== 40'sd3690988 ||
            m_clca_q !== 40'sd2516582 || m_kca_q !== 40'sd1677722 ||
            ca_i_q !== 40'sd1845494 || ca_s_q !== 40'sd1342177 ||
            ca_f_q !== 40'sd838861 || valid_out || divide_by_zero) begin
            $display("FAIL reset state: V=%0d gates=%0d,%0d,%0d,%0d,%0d calcium=%0d,%0d,%0d valid=%b div0=%b",
                     v_mem_q, m_h_q, m_kv_q, m_ca_q, m_clca_q, m_kca_q,
                     ca_i_q, ca_s_q, ca_f_q, valid_out, divide_by_zero);
            $finish;
        end
        gate_h_after_reset = m_h_q;
        ca_i_after_reset = ca_i_q;

        reset = 1'b0;
        #1;
        if (i_photo_q !== 0 || i_total_q !== IONIC_TOTAL_INIT ||
            i_h_q !== -40'sd9663676800 || i_kv_q !== 40'sd489220000 ||
            i_ca_q !== -40'sd3001202400 || i_clca_q !== 40'sd488512940 ||
            i_kca_q !== 40'sd641911020 || i_l_q !== -40'sd3355443200) begin
            $display("FAIL initial dark currents: total=%0d Ih=%0d Ikv=%0d Ica=%0d Iclca=%0d Ikca=%0d Il=%0d",
                     i_total_q, i_h_q, i_kv_q, i_ca_q, i_clca_q, i_kca_q, i_l_q);
            $finish;
        end

        valid_in = 1'b1;
        @(posedge clk);
        #1;
        if (!valid_out || divide_by_zero || v_mem_q !== V_AFTER_DARK_STEP) begin
            $display("FAIL first dark update: valid=%b div0=%b V=%0d expected=%0d",
                     valid_out, divide_by_zero, v_mem_q, V_AFTER_DARK_STEP);
            $finish;
        end
        if (m_h_q === gate_h_after_reset || ca_i_q >= ca_i_after_reset) begin
            $display("FAIL gate/calcium state did not update: mh=%0d Cai=%0d", m_h_q, ca_i_q);
            $finish;
        end
        v_after_first = v_mem_q;

        light_q = Q_ONE;
        #1;
        if (i_photo_q !== 40'sd33554432000) begin
            $display("FAIL baseline photocurrent during light step: %0d", i_photo_q);
            $finish;
        end
        @(posedge clk);
        #1;
        if (!valid_out || divide_by_zero || v_mem_q >= v_after_first) begin
            $display("FAIL light-driven voltage update: valid=%b div0=%b V=%0d previous=%0d",
                     valid_out, divide_by_zero, v_mem_q, v_after_first);
            $finish;
        end

        v_before_idle = v_mem_q;
        valid_in = 1'b0;
        @(posedge clk);
        #1;
        if (valid_out || v_mem_q !== v_before_idle) begin
            $display("FAIL idle-cycle valid/voltage hold: valid=%b V=%0d", valid_out, v_mem_q);
            $finish;
        end

        $display("PASS tb_photoreceptor_baseline: reset, dark golden step, light response and valid timing");
        $finish;
    end
endmodule
