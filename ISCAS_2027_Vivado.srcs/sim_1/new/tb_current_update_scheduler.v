`timescale 1ns / 1ps

module tb_current_update_scheduler;
    reg clk = 0;
    reg reset = 0;
    reg valid_in = 0;
    reg signed [39:0] voltage_q = 0;
    reg signed [39:0] voltage_at_refresh_q = 0;
    reg signed [39:0] light_q = 0;
    reg signed [39:0] light_at_refresh_q = 0;
    reg force_refresh = 0;
    reg budget_exhausted = 0;
    wire refresh_all;
    wire [15:0] refresh_counter;
    wire valid_out;
    reg sampled_refresh;
    reg [15:0] counter_before_idle;

    current_update_scheduler #(
        .DATA_WIDTH(40),
        .VOLTAGE_THRESHOLD_Q(40'sd4),
        .LIGHT_THRESHOLD_Q(40'sd0),
        .MAX_REFRESH_INTERVAL(3)
    ) uut (
        .clk(clk), .reset(reset), .valid_in(valid_in),
        .voltage_q(voltage_q), .voltage_at_refresh_q(voltage_at_refresh_q),
        .light_q(light_q), .light_at_refresh_q(light_at_refresh_q),
        .force_refresh(force_refresh), .budget_exhausted(budget_exhausted),
        .refresh_all(refresh_all), .refresh_counter(refresh_counter),
        .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    task accept_cycle;
        begin
            @(negedge clk);
            valid_in = 1;
            #1;
            sampled_refresh = refresh_all;
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        reset = 1;
        @(negedge clk);
        reset = 0;
        accept_cycle();
        if (!sampled_refresh || !valid_out || refresh_counter != 0) begin
            $display("FAIL scheduler initialization refresh");
            $finish;
        end

        accept_cycle();
        if (sampled_refresh) begin
            $display("FAIL unexpected refresh without a trigger");
            $finish;
        end
        accept_cycle();
        if (sampled_refresh) begin
            $display("FAIL interval refreshed early");
            $finish;
        end
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL maximum interval did not force refresh");
            $finish;
        end

        voltage_q = 40'sd4;
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL voltage movement did not force refresh");
            $finish;
        end
        voltage_at_refresh_q = voltage_q;
        light_q = 40'sd1;
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL light change did not force refresh");
            $finish;
        end
        light_at_refresh_q = light_q;
        budget_exhausted = 1;
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL exhausted budget did not force refresh");
            $finish;
        end
        budget_exhausted = 0;
        force_refresh = 1;
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL explicit force did not force refresh");
            $finish;
        end
        force_refresh = 0;
        voltage_at_refresh_q = 40'sd4;
        voltage_q = -40'sd4;
        accept_cycle();
        if (!sampled_refresh) begin
            $display("FAIL negative voltage excursion did not force refresh");
            $finish;
        end

        @(negedge clk);
        valid_in = 0;
        counter_before_idle = refresh_counter;
        #1;
        if (refresh_all) begin
            $display("FAIL invalid cycle advertised a refresh");
            $finish;
        end
        @(posedge clk);
        #1;
        if (valid_out || refresh_counter != counter_before_idle) begin
            $display("FAIL invalid-cycle valid or refresh-counter hold");
            $finish;
        end
        $display("PASS tb_current_update_scheduler");
        $finish;
    end
endmodule
