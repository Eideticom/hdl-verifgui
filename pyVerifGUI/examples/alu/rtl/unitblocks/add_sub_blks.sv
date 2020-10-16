//-----------------------------------------------------------------------------
// File: examples/alu/rtl/unitblocks/add_sub_blks.sv
// Author: Danilo Ramos
// Copyright (c) 2019. Eidetic Communications Inc.
// All rights reserved.
// Licensed under the BSD 3-Clause license.
// This license message must appear in all versions of this code including
// modified versions.
//----------------------------------------------------------------------------

module add
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
  
  always_ff@(posedge clk) begin: main_ff
    if(rstb == 1'b0)
      r <= '0;
    else begin
      r <= {a[IN_WL-1], a} + {b[IN_WL-1], b};
    end
  end: main_ff
endmodule: add

module sub
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
  
  always_ff@(posedge clk) begin: main_ff
    if(rstb == 1'b0)
      r <= '0;
    else begin
      r <= {a[IN_WL-1], a} - {b[IN_WL-1], b};
    end
  end: main_ff
endmodule: sub

module dummy
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
  
  always_ff@(posedge clk) begin: main_ff
    if(rstb == 1'b0)
      r <= '0;
    else begin
      r <= {a[IN_WL-1], a} - {b[IN_WL-1], b};
    end
  end: main_ff
endmodule: dummy