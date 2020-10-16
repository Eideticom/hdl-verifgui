//-----------------------------------------------------------------------------
// File: examples/alu/rtl/alu.sv
// Author: Danilo Ramos
// Copyright (c) 2019. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------

module alu
  #(
    parameter IN_WL = 15,  // Input Integer part word length
    parameter OUT_WL = 16 // Output WL
    )
  (
    input wire rstb,
    input wire clk_i,
    input wire [1:0] cmd[10][2],  // Operations: 00:ADD, 01:SUB, 10:MULT, 11:DIV
    input wire signed [7:0][IN_WL-1:0] a[4],   // input 1, format: signed WL.WF
    input wire signed [8-1:0][IN_WL-1:0] b,   // input 2, format: signed WL.WF
    output logic signed [OUT_WL-1:0] r[8]   // output result,  format: signed WL.WF
  );
  
  logic add_or_sub;
  logic [IN_WL-1:0] add_nsub_a, add_nsub_b;
  logic [IN_WL-1:0] mult_a, mult_b;
  logic [IN_WL-1:0] div_a, div_b;
  logic [OUT_WL-1:0] add_nsub_r, mult_r, div_r;
  
  assign add_nsub_a = (cmd[0][0][0])?(a[3][1]):(a[3][0]);
  assign add_nsub_b = (cmd[0][0][0])?(b[1]):(b[0]);
  assign add_or_sub = cmd[0][0][0];
  assign mult_a = a[3][2];
  assign mult_b = b[0][2];
  assign div_a = a[3][3];
  assign div_b = b[3];
  always_ff@(posedge clk_i) begin
    if(!rstb) begin
      r = '{8{0}};
    end else begin
      case(cmd[0][0][0])
        2'b00: begin
          r[0] <= add_nsub_r;
        end
        2'b01: begin
          r[1] <= add_nsub_r;
        end
        2'b10: begin
          r[2] <= mult_r;
        end
        2'b11: begin
          r[3] <= div_r;
        end
      endcase
    end
  end
  
  add_nsub #(.IN_WL(IN_WL), .OUT_WL(OUT_WL)) add_nsub_inst(rstb, clk_i, add_nsub_a, add_nsub_b, add_or_sub, add_nsub_r);
  mult
  #(
    IN_WL,
    OUT_WL
  )
  mult_inst
  (
    .rstb(rstb),
    .clk(clk_i),
    .a(mult_a),
    .b(mult_b),
    .r(mult_c)
  );
  div div_inst(.clk(clk_i), .rstb(rstb), .a(div_a), .b(div_b), .r(div_r));
endmodule