`timescale 1ns / 1ps

module tb_edge_cases;
    reg clk = 0;
    reg reset = 0;
    reg valid_in = 0;
    reg signed [39:0] light_q = 0;
    wire signed [39:0] v_mem_q;
    wire signed [39:0] i_photo_q;
    wire signed [39:0] i_total_q;
    wire valid_out;
    wire divide_by_zero;

    photoreceptor_adaptive uut (
        .clk(clk), .reset(reset), .valid_in(valid_in), .light_q(light_q),
        .v_mem_q(v_mem_q), .i_photo_q(i_photo_q), .i_total_q(i_total_q),
        .valid_out(valid_out), .divide_by_zero(divide_by_zero)
    );

    always #5 clk = ~clk;

    initial begin
        reset = 1;
        light_q = 0;
        #10;
        reset = 0;
        valid_in = 1;
        @(posedge clk);
        #1;
        light_q = 40'sd16777216;
        @(posedge clk);
        #1;
        if ((^v_mem_q === 1'bx) || (^i_photo_q === 1'bx) ||
            (^i_total_q === 1'bx) || !valid_out || divide_by_zero) begin
            $display("FAIL adaptive light-edge outputs invalid or unknown");
            $finish;
        end
        if (i_photo_q !== 40'sd33554432000) begin
            $display("FAIL unit-light photocurrent raw Q16.24 vector");
            $finish;
        end
        $display("PASS tb_edge_cases known-value and valid checks");
        $finish;
    end
endmodule
