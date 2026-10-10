`timescale 1ns / 1ps

module tb_phototransduction;
    localparam integer DATA_WIDTH = 40;
    localparam integer FRAC_BITS = 24;
    localparam signed [DATA_WIDTH-1:0] Q_ONE = 40'sd16777216;
    localparam signed [DATA_WIDTH-1:0] EXPECTED_2000_PA_Q = 40'sd33554432000;
    localparam signed [DATA_WIDTH-1:0] EXPECTED_1000_PA_Q = 40'sd16777216000;

    reg signed [DATA_WIDTH-1:0] light_q;
    wire signed [DATA_WIDTH-1:0] i_photo_q;

    phototransduction #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) uut (
        .light_q(light_q),
        .i_photo_q(i_photo_q)
    );

    initial begin
        light_q = 0;
        #1;
        if (i_photo_q !== 0) begin
            $display("FAIL dark light current: got %0d expected 0", i_photo_q);
            $finish;
        end

        light_q = Q_ONE;
        #1;
        if (i_photo_q !== EXPECTED_2000_PA_Q) begin
            $display("FAIL unit light current: got %0d expected %0d", i_photo_q, EXPECTED_2000_PA_Q);
            $finish;
        end

        light_q = Q_ONE >>> 1;
        #1;
        if (i_photo_q !== EXPECTED_1000_PA_Q) begin
            $display("FAIL half light current: got %0d expected %0d", i_photo_q, EXPECTED_1000_PA_Q);
            $finish;
        end

        light_q = -(Q_ONE >>> 1);
        #1;
        if (i_photo_q !== -EXPECTED_1000_PA_Q) begin
            $display("FAIL negative light current: got %0d expected %0d", i_photo_q, -EXPECTED_1000_PA_Q);
            $finish;
        end

        $display("PASS tb_phototransduction: Q16.24 light-to-pA vectors");
        $finish;
    end
endmodule
