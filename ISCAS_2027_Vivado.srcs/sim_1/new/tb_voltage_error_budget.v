`timescale 1ns / 1ps

module tb_voltage_error_budget;
    reg clk = 0;
    reg reset = 0;
    reg valid_in = 0;
    reg clear = 0;
    reg [39:0] estimated_error_increment_q = 0;
    wire [39:0] budget_value_q;
    wire budget_exhausted;
    wire valid_out;

    voltage_error_budget #(
        .DATA_WIDTH(40), .BUDGET_LIMIT_Q(40'd10)
    ) uut (
        .clk(clk), .reset(reset), .valid_in(valid_in), .clear(clear),
        .estimated_error_increment_q(estimated_error_increment_q),
        .budget_value_q(budget_value_q), .budget_exhausted(budget_exhausted),
        .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    task apply_increment;
        input [39:0] increment;
        begin
            @(negedge clk);
            valid_in = 1;
            estimated_error_increment_q = increment;
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        reset = 1;
        @(negedge clk);
        reset = 0;
        apply_increment(40'd4);
        if (budget_value_q != 4 || budget_exhausted || !valid_out) begin
            $display("FAIL budget first accumulation");
            $finish;
        end
        apply_increment(40'd4);
        if (budget_value_q != 8 || !budget_exhausted) begin
            $display("FAIL projected threshold crossing not detected");
            $finish;
        end
        apply_increment(40'd4);
        if (budget_value_q != 12 || !budget_exhausted) begin
            $display("FAIL threshold-crossing increment accumulation");
            $finish;
        end
        apply_increment(40'd20);
        if (budget_value_q != 32 || !budget_exhausted) begin
            $display("FAIL budget threshold accumulation");
            $finish;
        end
        @(negedge clk);
        clear = 1;
        estimated_error_increment_q = 40'hffffffffff;
        @(posedge clk);
        #1;
        if (budget_value_q != 0) begin
            $display("FAIL refresh did not clear accumulated budget");
            $finish;
        end
        clear = 0;
        estimated_error_increment_q = 40'hffffffffff;
        @(posedge clk);
        #1;
        if (budget_value_q != 40'hffffffffff || !budget_exhausted) begin
            $display("FAIL maximum budget word accumulation");
            $finish;
        end
        estimated_error_increment_q = 40'd1;
        @(posedge clk);
        #1;
        if (budget_value_q != 40'hffffffffff) begin
            $display("FAIL unsigned budget overflow did not saturate");
            $finish;
        end
        valid_in = 0;
        @(posedge clk);
        #1;
        if (valid_out || budget_value_q != 40'hffffffffff) begin
            $display("FAIL invalid-cycle valid or budget hold");
            $finish;
        end
        $display("PASS tb_voltage_error_budget");
        $finish;
    end
endmodule
