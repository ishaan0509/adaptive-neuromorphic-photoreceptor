`timescale 1ns / 1ps

module fixed_point_math #(
    parameter integer WIDTH = 16,
    parameter integer FRAC_BITS = 8,
    parameter integer SATURATE = 1
)(
    input  signed [WIDTH-1:0] a,
    input  signed [WIDTH-1:0] b,
    output reg signed [WIDTH-1:0] sum_out,
    output reg signed [WIDTH-1:0] diff_out,
    output wire signed [2*WIDTH-1:0] product_out,
    output reg overflow
);

    wire signed [WIDTH:0] a_ext = {a[WIDTH-1], a};
    wire signed [WIDTH:0] b_ext = {b[WIDTH-1], b};
    wire signed [WIDTH:0] sum_temp = a_ext + b_ext;
    wire signed [WIDTH:0] diff_temp = a_ext - b_ext;

    assign product_out = a * b;

    always @* begin
        overflow = (sum_temp[WIDTH] != sum_temp[WIDTH-1]) ||
                   (diff_temp[WIDTH] != diff_temp[WIDTH-1]);

        if (SATURATE && (sum_temp[WIDTH] != sum_temp[WIDTH-1])) begin
            sum_out = sum_temp[WIDTH] ? {1'b1, {(WIDTH-1){1'b0}}}
                                     : {1'b0, {(WIDTH-1){1'b1}}};
        end else begin
            sum_out = sum_temp[WIDTH-1:0];
        end

        if (SATURATE && (diff_temp[WIDTH] != diff_temp[WIDTH-1])) begin
            diff_out = diff_temp[WIDTH] ? {1'b1, {(WIDTH-1){1'b0}}}
                                        : {1'b0, {(WIDTH-1){1'b1}}};
        end else begin
            diff_out = diff_temp[WIDTH-1:0];
        end
    end

endmodule
