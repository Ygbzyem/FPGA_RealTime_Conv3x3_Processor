module cnn_blur (
input i_clk,
input i_reset,
input data_valid_in,

input [7:0] p11, p12, p13,
input [7:0] p21, p22, p23,
input [7:0] p31, p32, p33,
output reg [7:0] o_pixel,
output reg data_valid_out
);	

reg signed [15:0] mult11, mult12, mult13;
reg signed [15:0] mult21, mult22, mult23;
reg signed [15:0] mult31, mult32, mult33;
reg delay_valid_1;
reg signed [19:0] sum_p;
reg delay_valid_2;
reg [30:0] temp_sum;

always @(posedge i_clk or posedge i_reset) begin
        if (i_reset) begin
            mult11 <= 16'd0; mult12 <= 16'd0; mult13 <= 16'd0;
            mult21 <= 16'd0; mult22 <= 16'd0; mult23 <= 16'd0;
            mult31 <= 16'd0; mult32 <= 16'd0; mult33 <= 16'd0;
            delay_valid_1  <= 1'b0;
end
	else if(data_valid_in) begin

mult11 <= $signed({1'b0, p11});
mult12 <= $signed({1'b0, p12});
mult13 <= $signed({1'b0, p13});
mult21 <= $signed({1'b0, p21});
mult22 <= $signed({1'b0, p22});
mult23 <= $signed({1'b0, p23});
mult31 <= $signed({1'b0, p31}); 
mult32 <= $signed({1'b0, p32});
mult33 <= $signed({1'b0, p33});

delay_valid_1 <= data_valid_in;
end

end

// Adder Tree (Sum)


always @(posedge i_clk or posedge i_reset) begin
	if (i_reset) begin
sum_p <= 20'd0;
delay_valid_2 <= 1'b0;
end
	else if(delay_valid_1) begin
sum_p <= mult11 + mult12 + mult13 + mult21 + mult22 + mult23 + mult31 + mult32 +mult33;
delay_valid_2 <= delay_valid_1;
end
	else begin
delay_valid_2 <= 1'b0;
end

end

// Ouput and Overflow check

always @(posedge i_clk or posedge i_reset) begin
	if (i_reset) begin
o_pixel <= 8'd0;
data_valid_out <= 1'b0;
temp_sum <= 31'b0;
end
	else if (delay_valid_2) begin
temp_sum <= sum_p * 114;  // do 1/9 nhan voi 2^10
	if((temp_sum >> 10) > 8'd255) begin 
	o_pixel <= 8'd255;

end

	else begin
o_pixel <= temp_sum[17:10];    //17-10 +1 = 8 bit
end

data_valid_out <= delay_valid_2;
end
	else begin
data_valid_out <= 1'b0;
end

end



endmodule
