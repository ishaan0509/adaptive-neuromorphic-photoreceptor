`timescale 1ns / 1ps

module phototransduction #(
    parameter integer DATA_WIDTH = 40,
    parameter integer FRAC_BITS = 24
)(
    input  signed [DATA_WIDTH-1:0] light_q,
    output signed [DATA_WIDTH-1:0] i_photo_q
);
    // Provisional Python model: I_photo = 2e-9 * light A.
    // In these engineering units, 1e-9 A = 1000 pA.
    localparam signed [DATA_WIDTH-1:0] G_PHOTO_P_A_Q =
        40'sd33554432000; // 2000 pA per normalized light unit, Q16.24
    localparam integer PRODUCT_WIDTH =
        (FRAC_BITS <= DATA_WIDTH) ? (DATA_WIDTH + FRAC_BITS) : (2 * DATA_WIDTH);
    wire signed [PRODUCT_WIDTH-1:0] product;

    assign product = light_q * G_PHOTO_P_A_Q;
    assign i_photo_q = product >>> FRAC_BITS;
endmodule
