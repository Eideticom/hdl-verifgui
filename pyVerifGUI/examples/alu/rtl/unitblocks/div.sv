module div
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
      r <= a >> b;
    end
  end: main_ff
endmodule: div
