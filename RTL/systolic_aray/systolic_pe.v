module systolic_pe #(
    parameter ACC_WIDTH = 20   // do rong bit accumulator, giong ACC_WIDTH cua adder-tree version
)(
    input  i_clk,
    input  i_reset,
    input  [7:0] i_pixel,                 // 1 pixel cua cua so 3x3, da duoc tre dung so chu ky
    input  signed [7:0] i_weight,         // he so kernel tuong ung, da duoc chon dung theo mode
    input  i_valid,                       // valid cuc bo, da duoc tre dung so chu ky nhu i_pixel
    input  signed [ACC_WIDTH-1:0] i_partial_sum_in,  // tong don tu PE truoc (hoac 0 neu la PE dau tien)
    output reg signed [ACC_WIDTH-1:0] o_partial_sum  // tong don sau khi cong them, da dang ky (1 chu ky)
);

    // Nhan 1 pixel (khong dau, 8-bit) voi 1 he so kernel (co dau, 8-bit).
    // Mo rong dau cho khop ACC_WIDTH truoc khi cong, tranh loi tran/sai dau.
    wire signed [16:0] product_raw = $signed({1'b0, i_pixel}) * i_weight;
    wire signed [ACC_WIDTH-1:0] product = {{(ACC_WIDTH-17){product_raw[16]}}, product_raw};

    always @(posedge i_clk or posedge i_reset) begin
        if (i_reset)
            o_partial_sum <= {ACC_WIDTH{1'b0}};
        else if (i_valid)
            // DAY LA DIEM KHAC BIET CHINH so voi adder tree: moi PE chi lam
            // 1 phep nhan + 1 phep cong duy nhat, roi dang ky ngay - khong
            // co tang cong dồn 9-so trong 1 chu ky nhu adder tree.
            o_partial_sum <= i_partial_sum_in + product;
        else
            o_partial_sum <= {ACC_WIDTH{1'b0}};
    end

endmodule
