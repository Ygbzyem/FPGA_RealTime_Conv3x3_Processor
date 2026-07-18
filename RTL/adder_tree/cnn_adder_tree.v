module conv_multi (
input i_clk,
input i_reset,
input data_valid_in,
input mode,                 // 0 = sharpening, 1 = blur (giu dung quy uoc cua top_module hien tai)

input [7:0] p11, p12, p13,
input [7:0] p21, p22, p23,
input [7:0] p31, p32, p33,
output reg [7:0] o_pixel,
output reg data_valid_out
);

// ============================================================================
// GHI CHU KHI GOP TU cnn_sharpening.v + cnn_blur.v:
//
//  mode duoc "bam" (latch) qua tung tang pipeline bang mode_d1, mode_d2,
//    de tang cuoi biet dung logic sharpen hay blur - vi 2 file goc xu ly
//    khac nhau hoan toan o tang cuoi (sharpen clip truc tiep, blur nhan 114
//    roi shift). Neu khong luu mode theo tung tang, mode doi giua chung
//    se lam sai ket qua cac pixel dang o giua pipeline.
// ============================================================================

reg signed [15:0] mult11, mult12, mult13;
reg signed [15:0] mult21, mult22, mult23;
reg signed [15:0] mult31, mult32, mult33;
reg delay_valid_1;
reg mode_d1;

reg signed [19:0] sum_p;   // 20-bit du cho ca 2 truong hop (blur can rong nhat: -2295..2295)
reg delay_valid_2;
reg mode_d2;

// --------------------------------------------------------------------------
// TANG 1: chon he so theo mode, nhan song song (giong cau truc parallel
// multipliers cua 2 file goc, chi khac la chon he so bang if/else theo mode)
// --------------------------------------------------------------------------
always @(posedge i_clk or posedge i_reset) begin
    if (i_reset) begin
        mult11 <= 16'd0; mult12 <= 16'd0; mult13 <= 16'd0;
        mult21 <= 16'd0; mult22 <= 16'd0; mult23 <= 16'd0;
        mult31 <= 16'd0; mult32 <= 16'd0; mult33 <= 16'd0;
        delay_valid_1 <= 1'b0;
        mode_d1 <= 1'b0;
    end
    else if (data_valid_in) begin
        if (mode == 1'b0) begin
            // SHARPENING - dung he so tu cnn_sharpening.v goc
            // (0 -1 0 / -1 5 -1 / 0 -1 0) - cac vi tri he so = 0 gan thang 0,
            // khong can nhan, giong cnn_sharpening.v goc luoc bo 11,13,31,33
            mult11 <= 16'sd0;
            mult12 <= $signed({1'b0, p12}) * -8'sd1;
            mult13 <= 16'sd0;
            mult21 <= $signed({1'b0, p21}) * -8'sd1;
            mult22 <= $signed({1'b0, p22}) * 8'sd5;
            mult23 <= $signed({1'b0, p23}) * -8'sd1;
            mult31 <= 16'sd0;
            mult32 <= $signed({1'b0, p32}) * -8'sd1;
            mult33 <= 16'sd0;
        end
        else begin
            // BLUR - dung he so tu cnn_blur.v goc (tat ca = 1, chia sau o tang cuoi)
            mult11 <= $signed({1'b0, p11});
            mult12 <= $signed({1'b0, p12});
            mult13 <= $signed({1'b0, p13});
            mult21 <= $signed({1'b0, p21});
            mult22 <= $signed({1'b0, p22});
            mult23 <= $signed({1'b0, p23});
            mult31 <= $signed({1'b0, p31});
            mult32 <= $signed({1'b0, p32});
            mult33 <= $signed({1'b0, p33});
        end
        delay_valid_1 <= data_valid_in;
        mode_d1 <= mode;
    end
    else begin
        // DA THEM nhanh nay (cnn_blur.v goc bi thieu) de dam bao delay_valid_1
        // luon ve 0 khi khong co du lieu vao, tranh valid gia khi dung streaming.
        delay_valid_1 <= 1'b0;
    end
end

// --------------------------------------------------------------------------
// TANG 2: Adder Tree - dung chung 1 phep cong cho ca 2 mode. Voi sharpening,
// mult11/13/31/33 luon = 0 nen khong anh huong ket qua, giu duoc dung ket qua
// nhu cnn_sharpening.v goc (chi cong 5 so hac).
// --------------------------------------------------------------------------
always @(posedge i_clk or posedge i_reset) begin
    if (i_reset) begin
        sum_p <= 20'sd0;
        delay_valid_2 <= 1'b0;
        mode_d2 <= 1'b0;
    end
    else if (delay_valid_1) begin
        sum_p <= mult11 + mult12 + mult13 + mult21 + mult22 + mult23 + mult31 + mult32 + mult33;
        delay_valid_2 <= delay_valid_1;
        mode_d2 <= mode_d1;
    end
    else begin
        delay_valid_2 <= 1'b0;
    end
end

// --------------------------------------------------------------------------
// TANG 3: Output + Overflow check - re nhanh theo mode_d2 vi sharpen va blur
// xu ly khac nhau hoan toan o day (sharpen clip truc tiep; blur nhan he so
// 114/1024 ~ 1/9 roi shift)
// --------------------------------------------------------------------------
wire signed [30:0] temp_sum_comb = sum_p * 114;   // 1/9 xap xi = 114 / 1024 (2^10)

always @(posedge i_clk or posedge i_reset) begin
    if (i_reset) begin
        o_pixel <= 8'd0;
        data_valid_out <= 1'b0;
    end
    else if (delay_valid_2) begin
        if (mode_d2 == 1'b0) begin
            // SHARPENING - giong het cnn_sharpening.v goc
            if (sum_p < 0)
                o_pixel <= 8'd0;
            else if (sum_p > 255)
                o_pixel <= 8'd255;
            else
                o_pixel <= sum_p[7:0];
        end
        else begin
            // BLUR - cung logic cnn_blur.v goc nhung tinh dung trong 1 chu ky
            if ((temp_sum_comb >>> 10) > 8'd255)
                o_pixel <= 8'd255;
            else
                o_pixel <= temp_sum_comb[17:10];
        end
        data_valid_out <= delay_valid_2;
    end
    else begin
        data_valid_out <= 1'b0;
    end
end

endmodule