`timescale 1ns / 1ps

module voltage_error_budget #(
    parameter integer DATA_WIDTH = 40,
    parameter [DATA_WIDTH-1:0] BUDGET_LIMIT_Q = 40'd1677722
)(
    input clk,
    input reset,
    input valid_in,
    input clear,
    input [DATA_WIDTH-1:0] estimated_error_increment_q,
    output reg [DATA_WIDTH-1:0] budget_value_q,
    output wire budget_exhausted,
    output reg valid_out
);
    wire [DATA_WIDTH:0] accumulated_wide =
        {1'b0, budget_value_q} + {1'b0, estimated_error_increment_q};

    assign budget_exhausted = (budget_value_q >= BUDGET_LIMIT_Q) ||
        (valid_in &&
         ((accumulated_wide[DATA_WIDTH]) ||
          (accumulated_wide[DATA_WIDTH-1:0] >= BUDGET_LIMIT_Q)));

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            budget_value_q <= {DATA_WIDTH{1'b0}};
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (clear)
                budget_value_q <= {DATA_WIDTH{1'b0}};
            else if (valid_in) begin
                if (accumulated_wide[DATA_WIDTH])
                    budget_value_q <= {DATA_WIDTH{1'b1}};
                else
                    budget_value_q <= accumulated_wide[DATA_WIDTH-1:0];
            end
        end
    end
endmodule
