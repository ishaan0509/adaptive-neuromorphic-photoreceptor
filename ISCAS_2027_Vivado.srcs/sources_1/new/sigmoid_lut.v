`timescale 1ns / 1ps

module sigmoid_lut #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input signed [DATA_WIDTH-1:0] x_q,
    output reg signed [DATA_WIDTH-1:0] y_q
);
    localparam signed [DATA_WIDTH-1:0] SCALE = (1 << FRAC_BITS);
    localparam signed [DATA_WIDTH-1:0] X_LIMIT = 8 * SCALE;
    localparam signed [DATA_WIDTH-1:0] HALF_STEP = SCALE >>> 1;
    reg signed [2*DATA_WIDTH-1:0] shifted_x;
    integer index;

    always @* begin
        shifted_x = {2*DATA_WIDTH{1'b0}};
        index = 0;
        if (x_q <= -X_LIMIT) begin
            index = 0;
        end else if (x_q >= X_LIMIT) begin
            index = 32;
        end else begin
            shifted_x = x_q;
            shifted_x = shifted_x + X_LIMIT + (SCALE >>> 2);
            index = shifted_x >>> (FRAC_BITS - 1);
            if (index < 0) index = 0;
            if (index > 32) index = 32;
        end

        case (index)
            0: y_q = 40'sd5626;
            1: y_q = 40'sd9274;
            2: y_q = 40'sd15285;
            3: y_q = 40'sd25186;
            4: y_q = 40'sd41484;
            5: y_q = 40'sd68286;
            6: y_q = 40'sd112287;
            7: y_q = 40'sd184330;
            8: y_q = 40'sd301759;
            9: y_q = 40'sd491778;
            10: y_q = 40'sd795674;
            11: y_q = 40'sd1272689;
            12: y_q = 40'sd1999893;
            13: y_q = 40'sd3060592;
            14: y_q = 40'sd4512088;
            15: y_q = 40'sd6334081;
            16: y_q = 40'sd8388608;
            17: y_q = 40'sd10443135;
            18: y_q = 40'sd12265128;
            19: y_q = 40'sd13716624;
            20: y_q = 40'sd14777323;
            21: y_q = 40'sd15504527;
            22: y_q = 40'sd15981542;
            23: y_q = 40'sd16285438;
            24: y_q = 40'sd16475457;
            25: y_q = 40'sd16592886;
            26: y_q = 40'sd16664929;
            27: y_q = 40'sd16708930;
            28: y_q = 40'sd16735732;
            29: y_q = 40'sd16752030;
            30: y_q = 40'sd16761931;
            31: y_q = 40'sd16767942;
            default: y_q = 40'sd16771590;
        endcase
    end
endmodule
