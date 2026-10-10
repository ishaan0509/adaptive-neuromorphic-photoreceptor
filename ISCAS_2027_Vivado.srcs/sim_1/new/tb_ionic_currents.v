`timescale 1ns / 1ps

module tb_ionic_currents;
    localparam integer DATA_WIDTH = 40;
    localparam integer FRAC_BITS = 24;
    localparam signed [DATA_WIDTH-1:0] V_MEM = -40'sd1006632960;
    localparam signed [DATA_WIDTH-1:0] M_H = 40'sd2013266;
    localparam signed [DATA_WIDTH-1:0] M_KV = 40'sd3019899;
    localparam signed [DATA_WIDTH-1:0] M_CA = 40'sd3690988;
    localparam signed [DATA_WIDTH-1:0] M_CLCA = 40'sd2516582;
    localparam signed [DATA_WIDTH-1:0] M_KCA = 40'sd1677722;
    localparam signed [DATA_WIDTH-1:0] CA_I = 40'sd1845494;
    localparam signed [DATA_WIDTH-1:0] G_H = 40'sd2013265920;
    localparam signed [DATA_WIDTH-1:0] G_KV = 40'sd4194304000;
    localparam signed [DATA_WIDTH-1:0] G_CA = 40'sd2348810240;
    localparam signed [DATA_WIDTH-1:0] G_CLCA = 40'sd1509949440;
    localparam signed [DATA_WIDTH-1:0] G_KCA = 40'sd1342177280;
    localparam signed [DATA_WIDTH-1:0] G_L = 40'sd335544320;
    localparam signed [DATA_WIDTH-1:0] E_H = -40'sd335544320;
    localparam signed [DATA_WIDTH-1:0] E_K = -40'sd1342177280;
    localparam signed [DATA_WIDTH-1:0] E_CA = 40'sd1006632960;
    localparam signed [DATA_WIDTH-1:0] E_CL = -40'sd1174405120;
    localparam signed [DATA_WIDTH-1:0] E_L = -40'sd838860800;
    localparam signed [DATA_WIDTH-1:0] K_CLCA = 40'sd6710886;
    localparam signed [DATA_WIDTH-1:0] K_KCA = 40'sd5872026;

    reg signed [DATA_WIDTH-1:0] ca_clca;
    reg signed [DATA_WIDTH-1:0] ca_kca;
    wire signed [DATA_WIDTH-1:0] i_h;
    wire signed [DATA_WIDTH-1:0] i_kv;
    wire signed [DATA_WIDTH-1:0] i_ca;
    wire signed [DATA_WIDTH-1:0] i_clca;
    wire signed [DATA_WIDTH-1:0] i_kca;
    wire signed [DATA_WIDTH-1:0] i_l;
    wire clca_invalid;
    wire kca_invalid;

    ih_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ih (
        .v_mem_q(V_MEM), .m_h_q(M_H), .g_h_q(G_H), .e_h_q(E_H), .i_h_q(i_h)
    );
    kv_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kv (
        .v_mem_q(V_MEM), .m_kv_q(M_KV), .g_kv_q(G_KV), .e_k_q(E_K), .i_kv_q(i_kv)
    );
    ca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_ca (
        .v_mem_q(V_MEM), .m_ca_q(M_CA), .g_ca_q(G_CA), .e_ca_q(E_CA), .i_ca_q(i_ca)
    );
    clca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_clca (
        .v_mem_q(V_MEM), .m_clca_q(M_CLCA), .ca_i_q(ca_clca),
        .g_clca_q(G_CLCA), .e_cl_q(E_CL), .k_clca_q(K_CLCA),
        .i_clca_q(i_clca), .invalid_denominator(clca_invalid)
    );
    kca_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_kca (
        .v_mem_q(V_MEM), .m_kca_q(M_KCA), .ca_i_q(ca_kca),
        .g_kca_q(G_KCA), .e_k_q(E_K), .k_kca_q(K_KCA),
        .i_kca_q(i_kca), .invalid_denominator(kca_invalid)
    );
    leakage_current #(.DATA_WIDTH(DATA_WIDTH), .FRAC_BITS(FRAC_BITS)) u_leak (
        .v_mem_q(V_MEM), .g_l_q(G_L), .e_l_q(E_L), .i_l_q(i_l)
    );

    initial begin
        ca_clca = CA_I;
        ca_kca = CA_I;
        #1;

        if (i_h !== -40'sd9663676800) begin
            $display("FAIL Ih: got %0d expected -9663676800", i_h);
            $finish;
        end
        if (i_kv !== 40'sd489220000) begin
            $display("FAIL Ikv: got %0d expected 489220000", i_kv);
            $finish;
        end
        if (i_ca !== -40'sd3001202400) begin
            $display("FAIL Ica: got %0d expected -3001202400", i_ca);
            $finish;
        end
        if (i_clca !== 40'sd488512940) begin
            $display("FAIL Iclca: got %0d expected 488512940", i_clca);
            $finish;
        end
        if (i_kca !== 40'sd641911020) begin
            $display("FAIL Ikca: got %0d expected 641911020", i_kca);
            $finish;
        end
        if (i_l !== -40'sd3355443200) begin
            $display("FAIL Ileak: got %0d expected -3355443200", i_l);
            $finish;
        end
        if (clca_invalid || kca_invalid) begin
            $display("FAIL valid calcium denominator reported invalid");
            $finish;
        end

        ca_clca = -K_CLCA;
        ca_kca = -K_KCA;
        #1;
        if (!clca_invalid || i_clca !== 0 || !kca_invalid || i_kca !== 0) begin
            $display("FAIL zero-denominator guard: Iclca=%0d invalid=%b; Ikca=%0d invalid=%b",
                     i_clca, clca_invalid, i_kca, kca_invalid);
            $finish;
        end

        $display("PASS tb_ionic_currents: six Q16.24 golden vectors and zero-denominator guards");
        $finish;
    end
endmodule
