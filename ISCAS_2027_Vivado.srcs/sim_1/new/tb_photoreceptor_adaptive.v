`timescale 1ns / 1ps

module tb_photoreceptor_adaptive;
    reg clk = 0;
    reg reset = 0;
    reg valid_in = 0;
    reg signed [39:0] light_q = 0;
    wire signed [39:0] v_mem_q;
    wire signed [39:0] i_total_q;
    wire refresh_event;
    wire [15:0] refresh_counter;
    wire [31:0] recomputation_count;
    wire valid_out;
    wire divide_by_zero;
    reg sampled_refresh;
    reg signed [39:0] held_voltage;
    reg signed [39:0] held_calcium;
    reg signed [39:0] refresh_input_voltage;
    reg signed [39:0] held_isolated_voltage;
    wire signed [39:0] ca_i_q;

    photoreceptor_adaptive #(
        .VOLTAGE_THRESHOLD_Q(40'sh7ffffffff),
        .ERROR_BUDGET_Q(40'hffffffffff),
        .MAX_REFRESH_INTERVAL(8),
        .OPERAND_ISOLATION_ENABLE(1)
    ) uut (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(v_mem_q), .i_total_q(i_total_q), .ca_i_q(ca_i_q),
        .refresh_event(refresh_event), .refresh_counter(refresh_counter),
        .recomputation_count(recomputation_count), .valid_out(valid_out),
        .divide_by_zero(divide_by_zero)
    );

    always #5 clk = ~clk;

    initial begin
        reset = 1;
        @(negedge clk);
        reset = 0;
        valid_in = 1;
        #1;
        sampled_refresh = refresh_event;
        if (!sampled_refresh) begin
            $display("FAIL first accepted sample did not refresh");
            $finish;
        end
        refresh_input_voltage = uut.current_v_q;
        if (refresh_input_voltage !== v_mem_q) begin
            $display("FAIL first refresh did not present live voltage to isolated datapath");
            $finish;
        end
        @(posedge clk);
        #1;
        if (!valid_out || recomputation_count != 6 ||
            uut.current_v_q !== refresh_input_voltage) begin
            $display("FAIL first accepted sample/cache initialization");
            $finish;
        end

        @(negedge clk);
        valid_in = 0;
        light_q = 40'sd16777216;
        held_voltage = v_mem_q;
        held_calcium = ca_i_q;
        #1;
        if (refresh_event) begin
            $display("FAIL invalid cycle requested refresh");
            $finish;
        end
        if (uut.current_v_q !== refresh_input_voltage) begin
            $display("FAIL invalid input changed operand-isolated current datapath");
            $finish;
        end
        @(posedge clk);
        #1;
        if (valid_out || v_mem_q !== held_voltage || ca_i_q !== held_calcium ||
            recomputation_count != 32'd6 ||
            uut.current_v_q !== refresh_input_voltage) begin
            $display("FAIL adaptive invalid-cycle state hold");
            $finish;
        end

        @(negedge clk);
        valid_in = 1;
        #1;
        sampled_refresh = refresh_event;
        if (!sampled_refresh) begin
            $display("FAIL light transition did not refresh");
            $finish;
        end
        refresh_input_voltage = uut.current_v_q;
        if (refresh_input_voltage !== v_mem_q) begin
            $display("FAIL light-triggered refresh did not use live voltage");
            $finish;
        end
        @(posedge clk);
        #1;
        if (!valid_out || recomputation_count != 12 ||
            uut.current_v_q !== refresh_input_voltage) begin
            $display("FAIL light-triggered recomputation count");
            $finish;
        end

        @(negedge clk);
        held_isolated_voltage = uut.current_v_q;
        valid_in = 1;
        #1;
        if (refresh_event) begin
            $display("FAIL unexpected refresh before max interval");
            $finish;
        end
        @(posedge clk);
        #1;
        if (uut.current_v_q !== held_isolated_voltage) begin
            $display("FAIL cached-current operand isolation did not hold snapshot");
            $finish;
        end

        $display("PASS tb_photoreceptor_adaptive initialization, refresh, operand-isolation, and idle-hold checks");
        $finish;
    end
endmodule
