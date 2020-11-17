//-----------------------------------------------------------------------------
// File: examples/alu/rtl/dummy_test.sv
// Author: Danilo Ramos
// Copyright (c) 2019. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------

module dummy_test
  #(
    parameter IN_WL = 15,  // Input Integer part word length
    parameter OUT_WL = 16 // Output WL
    )
  (
    input wire rstb,
    input wire clk,
    input wire [1:0] cmd,  // Operations: 00:ADD, 01:SUB, 10:MULT, 11:DIV
    input wire signed [IN_WL-1:0] a,   // input 1, format: signed WL.WF
    input wire signed [IN_WL-1:0] b,   // input 2, format: signed WL.WF
    output logic signed [OUT_WL-1:0] r   // output result,  format: signed WL.WF
  );
  
  logic add_or_sub;
  logic [IN_WL-1:0] add_nsub_a, add_nsub_b;
  logic [IN_WL-1:0] mult_a, mult_b;
  logic [IN_WL-1:0] div_a, div_b;
  logic [OUT_WL-1:0] add_nsub_r, mult_r, div_r;
  
  add_nsub #(.IN_WL(INWL), .OUT_WL(OUT_WL)) add_nsub_inst(rstb, clk, add_nsub_a, add_nsub_b, add_or_sub, add_nsub_r);
  mult
  #(
    IN_WL,
    OUT_WL
  )
  mult_inst
  (
    .rstb(rstb),
    .clk(clk),
    .a(mult_a),
    .b(mult_b),
    .r(mult_c)
  );
  div div_inst(.clk(clk), .rstb(rstb), .a(div_a), .b(div_b), .r(div_r));
endmodule