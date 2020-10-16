//-----------------------------------------------------------------------------
// File: examples/alu/rtl/unitblocks/mult.sv
// Author: Danilo Ramos
// Copyright (c) 2019. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------

module mult
  #(
    parameter IN_WL = 15,  // Input Integer part word length
    parameter OUT_WL = 16 // Output WL
    )
  (
    input wire rstb,  
    input wire clk,
    
    input wire [IN_WL-1:0] a,     // input 1
    input wire [IN_WL-1:0] b,     // input 2
    output logic [OUT_WL-1:0] r   // output result
  );
  
  logic [2*IN_WL-1:0] mult_r;
  assign r = mult_r[OUT_WL-1:0];
  always_ff@(posedge clk) begin: main_ff
    if(rstb == 1'b0)
      mult_r <= '0;
    else begin
      mult_r <= a*b;
    end
  end: main_ff
endmodule: mult
