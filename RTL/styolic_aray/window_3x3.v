module window_3x3 (
input i_clk,
input i_reset,
input [7:0] q1, q2, q3,
input data_valid_in,

output reg [7:0] p11, p12, p13,
output reg [7:0] p21, p22, p23,
output reg [7:0] p31, p32, p33
);

always @(posedge i_clk or posedge i_reset) begin
if (i_reset) begin
	p11 <= 8'd0;
	p12 <= 8'd0;
	p13 <= 8'd0;
	p21 <= 8'd0;
	p22 <= 8'd0;
	p23 <= 8'd0;
	p31 <= 8'd0;
	p32 <= 8'd0;
	p33 <= 8'd0;
end
else if (data_valid_in) begin
	p11 <= p12; p12 <= p13; p13 <= q1;
	p21 <= p22; p22 <= p23; p23 <= q2;
	p31 <= p32; p32 <= p33; p33 <= q3; 
end
end

endmodule