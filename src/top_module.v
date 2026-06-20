module top_module(
input i_clk,
input i_reset,
input data_valid_in,
input [7:0] i_pixel,
input mode,

output [7:0] o_pixel,
output data_valid_out
);
    wire [7:0] q1, q2, q3;

    wire [7:0] p11, p12, p13;
    wire [7:0] p21, p22, p23;
    wire [7:0] p31, p32, p33;
    wire matrix_valid;

wire [7:0] sharp_pixel, blur_pixel;
wire sharp_valid, blur_valid;

line_buffer line_buffer_inst (
        .i_clk(i_clk),
        .i_reset(i_reset),
        .i_pixel(i_pixel),
        .data_valid_in(data_valid_in),
        

        .q1(q1),
        .q2(q2),
        .q3(q3)
    );

window_3x3 window_inst (
        .i_clk(i_clk),
        .i_reset(i_reset),
        .data_valid_in(data_valid_in),
        .q1(q1),
        .q2(q2),
        .q3(q3),
        

        .p11(p11), .p12(p12), .p13(p13),
        .p21(p21), .p22(p22), .p23(p23),
        .p31(p31), .p32(p32), .p33(p33)
    );

cnn_sharpening cnn_sharpening_inst (
        .i_clk(i_clk),
        .i_reset(i_reset),
        .data_valid_in(data_valid_in),

       
        .p11(p11), .p12(p12), .p13(p13),
        .p21(p21), .p22(p22), .p23(p23),
        .p31(p31), .p32(p32), .p33(p33),
        
        
        .o_pixel(sharp_pixel),
        .data_valid_out(data_valid_out)
    );

cnn_blur cnn_blur_inst (
        .i_clk(i_clk),
        .i_reset(i_reset),
        .data_valid_in(data_valid_in),

       
        .p11(p11), .p12(p12), .p13(p13),
        .p21(p21), .p22(p22), .p23(p23),
        .p31(p31), .p32(p32), .p33(p33),
        
        
        .o_pixel(blur_pixel),
        .data_valid_out(data_valid_out)
    );

assign o_pixel = (mode) ? blur_pixel : sharp_pixel;
assign data_valid_out = (mode) ? blur_valid : sharp_valid;


endmodule