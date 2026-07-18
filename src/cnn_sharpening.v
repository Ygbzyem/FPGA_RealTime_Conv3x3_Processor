module cnn_sharpening (
input i_clk,
input i_reset,
input data_valid_in,

input [7:0] p11, p12, p13,
input [7:0] p21, p22, p23,
input [7:0] p31, p32, p33,
output reg [7:0] o_pixel,
output reg data_valid_out
);	

// parallel multipliers 9x9


reg signed [15:0] mult12;                                   // do ma tran sharpening la | 0 -1 0 |   signed dung de khai bao so co the am
reg signed [15:0] mult21, mult22, mult23;     			//			| -1 5 -1 |
reg signed [15:0] mult32;					//			| 0  -1  0 | nen luoc bo 11 13 31 33
reg delay_valid_1;
reg signed [18:0] sum_p;               //wcase min: -255 -255 +0 -255 -255 = -1020; wcase max: 0 + 0 +1275 + 0 + 0 = 1275 -> reg from -1020 to 1275 -> 11 bit + 1 bit signed = 11bit reg but for truncate case = reg input =16 + 3(5 < 2^3) mult caculate = 19 
reg delay_valid_2;

always @(posedge i_clk or posedge i_reset) begin
        if (i_reset) begin
            mult12 <= 16'd0;
            mult21 <= 16'd0; mult22 <= 16'd0; mult23 <= 16'd0;
            mult32 <= 16'd0;
            delay_valid_1  <= 1'b0;
end
	else if (data_valid_in) begin
mult12 <= $signed({1'b0, p12}) * -8'sd1;
mult21 <= $signed({1'b0, p21}) * -8'sd1;
mult22 <= $signed({1'b0, p22}) * 8'sd5;
mult23 <= $signed({1'b0, p23}) * -8'sd1;
mult32 <= $signed({1'b0, p32}) * -8'sd1;

delay_valid_1 <= data_valid_in;
end
	else begin 
delay_valid_1 <= 1'b0;
end
end


// Adder Tree (Sum)



always @(posedge i_clk or posedge i_reset) begin
	if(i_reset) begin
sum_p <= 19'd0;
delay_valid_2 <= 1'b0;
end
	else if(delay_valid_1) begin
sum_p <= mult12 + mult21 + mult22 + mult23 + mult32;
delay_valid_2 <= delay_valid_1;
end
	else begin
delay_valid_2 <= 1'b0;
end
end

// Ouput and Overflow check

always @(posedge i_clk or posedge i_reset) begin
	if(i_reset) begin
o_pixel <= 8'd0;
data_valid_out <= 1'b0;
end
	else if(delay_valid_2)begin
if( sum_p < 0) begin
	o_pixel <= 8'd0;
end
else if (sum_p > 255) begin
	o_pixel <= 8'd255;
end
else begin
o_pixel <= sum_p[7:0];
end
data_valid_out <= delay_valid_2;
end
else begin
data_valid_out <= 1'b0;
end
end
endmodule




