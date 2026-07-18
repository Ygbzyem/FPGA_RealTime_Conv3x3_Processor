module line_buffer (
input i_clk,
input i_reset,
input [7:0] i_pixel,
input data_valid_in,
output [7:0] q1, q2, q3 		//3 linebuffer chay theo nguyen ly FIFO voi q3 dai dien cho hang vao 1st
);

parameter image_width = 64;

assign q3 = i_pixel;

reg [7:0] line2 [0:image_width-1];
reg [7:0] line1 [0:image_width-1];

integer i;
always @(posedge i_clk or posedge i_reset) begin
	if(i_reset) begin
	for (i = 0; i < image_width; i = i+1) begin
line2[i] <= 8'd0;
line1[i] <= 8'd0;
	end
end
	else if (data_valid_in) begin
for (i = image_width-1; i > 0; i = i-1) begin
	line2[i] <= line2[i-1];
end
line2[0] <= q3;

for (i = image_width-1; i>0; i = i-1) begin
	line1[i] <= line1[i-1];
end
line1[0] <= q2;

end
end
assign q2 = line2[image_width-1];
assign q1 = line1[image_width-1]; 
//2 cai assign ket hop voi pixel_in cho ra 1 cot co 3 phan tu

endmodule