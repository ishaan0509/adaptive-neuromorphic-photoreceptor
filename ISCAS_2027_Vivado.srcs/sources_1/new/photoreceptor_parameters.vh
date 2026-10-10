`ifndef PHOTORECEPTOR_PARAMETERS_VH
`define PHOTORECEPTOR_PARAMETERS_VH

`define Q_FORMAT_WIDTH 16
`define Q_FORMAT_FRAC 8
`define Q_FORMAT_INT 7

`define VOLTAGE_SCALE 8'd128
`define CURRENT_SCALE 8'd64
`define LIGHT_SCALE   8'd128

`define V_INIT -16'sd60
`define I_PHOTO_INIT 16'sd0
`define M_H_INIT 16'sd12
`define M_KV_INIT 16'sd18
`define M_CA_INIT 16'sd22
`define M_CLCA_INIT 16'sd15
`define M_KCA_INIT 16'sd10

`endif
