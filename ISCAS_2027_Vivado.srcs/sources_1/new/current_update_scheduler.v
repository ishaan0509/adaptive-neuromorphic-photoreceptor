`timescale 1ns / 1ps

module current_update_scheduler #(
    parameter integer DATA_WIDTH = 40,
    parameter signed [DATA_WIDTH-1:0] VOLTAGE_THRESHOLD_Q = 40'sd16777216,
    parameter signed [DATA_WIDTH-1:0] LIGHT_THRESHOLD_Q = 40'sd0,
    parameter integer MAX_REFRESH_INTERVAL = 8
)(
    input clk,
    input reset,
    input valid_in,
    input signed [DATA_WIDTH-1:0] voltage_q,
    input signed [DATA_WIDTH-1:0] voltage_at_refresh_q,
    input signed [DATA_WIDTH-1:0] light_q,
    input signed [DATA_WIDTH-1:0] light_at_refresh_q,
    input force_refresh,
    input budget_exhausted,
    output wire refresh_all,
    output reg [15:0] refresh_counter,
    output reg valid_out
);
    reg initialized;
    localparam integer EFFECTIVE_MAX_REFRESH_INTERVAL =
        (MAX_REFRESH_INTERVAL > 65536) ? 65536 : MAX_REFRESH_INTERVAL;
    wire signed [DATA_WIDTH:0] voltage_delta_wide =
        {voltage_q[DATA_WIDTH-1], voltage_q} -
        {voltage_at_refresh_q[DATA_WIDTH-1], voltage_at_refresh_q};
    wire signed [DATA_WIDTH:0] light_delta_wide =
        {light_q[DATA_WIDTH-1], light_q} -
        {light_at_refresh_q[DATA_WIDTH-1], light_at_refresh_q};
    wire [DATA_WIDTH:0] voltage_magnitude =
        voltage_delta_wide[DATA_WIDTH] ? -voltage_delta_wide : voltage_delta_wide;
    wire [DATA_WIDTH:0] light_magnitude =
        light_delta_wide[DATA_WIDTH] ? -light_delta_wide : light_delta_wide;
    wire [DATA_WIDTH:0] voltage_limit_wide =
        {VOLTAGE_THRESHOLD_Q[DATA_WIDTH-1], VOLTAGE_THRESHOLD_Q};
    wire [DATA_WIDTH:0] light_limit_wide =
        {LIGHT_THRESHOLD_Q[DATA_WIDTH-1], LIGHT_THRESHOLD_Q};
    wire interval_due = (EFFECTIVE_MAX_REFRESH_INTERVAL <= 1) ||
                        (refresh_counter >= EFFECTIVE_MAX_REFRESH_INTERVAL - 1);

    assign refresh_all = valid_in &&
        (!initialized || force_refresh || budget_exhausted || interval_due ||
         (voltage_magnitude >= voltage_limit_wide) ||
         (light_magnitude > light_limit_wide));

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            refresh_counter <= 16'd0;
            valid_out <= 1'b0;
            initialized <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                if (refresh_all)
                    refresh_counter <= 16'd0;
                else if (refresh_counter != 16'hffff)
                    refresh_counter <= refresh_counter + 1'b1;
                initialized <= 1'b1;
            end
        end
    end
endmodule
