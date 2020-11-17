//-----------------------------------------------------------------------------
// File: examples/alu/rtl/unitblocks/adder.sv
// Author: Danilo Ramos
// Copyright (c) 2019. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------

module add_nsub
  #(
    parameter IN_WL = 15,  // Input Integer part word length
    parameter OUT_WL = 16 // Output WL
    )
  (
    input wire rstb,  
    input wire clk,
    
    input wire [IN_WL-1:0] a,     // input 1
    input wire [IN_WL-1:0] b,     // input 2
    input add_nsub,               // 0:a-b, 1:a+b
    output logic [OUT_WL-1:0] r   // output result
  );
  
  logic [IN_WL-1:0] add_a, add_b;
  logic [IN_WL-1:0] sub_a, sub_b;
  logic [OUT_WL-1:0] add_r, sub_r;
  
  add #(.IN_WL(IN_WL), .OUT_WL(OUT_WL)) add_inst(rstb, clk, add_a, add_b, add_r);
  sub #(.IN_WL(IN_WL), .OUT_WL(OUT_WL)) sub_inst(rstb, clk, add_a, add_b, add_r);

  always_ff@(posedge clk) begin: main_ff
    if(rstb == 1'b0)
      r <= '0;
    else begin
      if(add_nsub == 1'b1)
        r <= add_r;
      else
        r <= sub_r;
    end
  end: main_ff
endmodule: add_nsub
