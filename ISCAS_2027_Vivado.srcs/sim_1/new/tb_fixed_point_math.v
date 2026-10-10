`timescale 1ns / 1ps

module tb_fixed_point_math;
    reg signed [15:0] a;
    reg signed [15:0] b;
    wire signed [15:0] sum_out;
    wire signed [15:0] diff_out;
    wire signed [31:0] product_out;
    wire overflow;

    fixed_point_math #(.WIDTH(16), .FRAC_BITS(8), .SATURATE(1)) uut (
        .a(a),
        .b(b),
        .sum_out(sum_out),
        .diff_out(diff_out),
        .product_out(product_out),
        .overflow(overflow)
    );

    initial begin
        a = 16'sd128;
        b = 16'sd64;
        #1;
        if (sum_out == 16'sd192 && diff_out == 16'sd64 &&
            product_out == 32'sd8192 && !overflow) begin
        end else begin
            $display("FAIL tb_fixed_point_math");
            $finish;
        end

        a = 16'sh7fff;
        b = 16'sd1;
        #1;
        if (sum_out != 16'sh7fff || !overflow) begin
            $display("FAIL tb_fixed_point_math positive saturation");
            $finish;
        end

        a = 16'sh8000;
        b = 16'sd1;
        #1;
        if (diff_out != 16'sh8000 || !overflow) begin
            $display("FAIL tb_fixed_point_math negative saturation");
            $finish;
        end
        $display("PASS tb_fixed_point_math arithmetic and saturation");
        $finish;
    end
endmodule
