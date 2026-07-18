module conv_systolic (
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
// KIEN TRUC SYSTOLIC ARRAY - THAY THE CHO ADDER TREE (conv_multi.v)
// ----------------------------------------------------------------------------
// Thay vi cong dong thoi 9 tich trong 1 tang to hop (adder tree), 9 gia tri
// duoc dua qua CHUOI 9 PE noi tiep (systolic_pe.v), moi PE chi lam 1 phep
// nhan + 1 phep cong roi dang ky ngay. Vi 1 cua so 3x3 moi den MOI CHU KY
// (khong phai moi 9 chu ky), moi pixel/mode/valid phai duoc "tre" dung so
// chu ky bang (vi_tri - 1) truoc khi dua vao PE tuong ung, de dam bao PE
// thu k luon xu ly dung DU LIEU CUA CUNG 1 CUA SO voi PE truoc no.
//
// Do tre tong (latency): 9 PE (9 chu ky) + 1 tang dang ky output/clip
// (1 chu ky) = 10 chu ky, tinh tu luc p11..p33 hop le den luc o_pixel hop le.
// (So voi adder tree hien tai: chi 3 chu ky). Day chinh la trade-off
// Fmax/critical-path (systolic ngan hon, on dinh hon khi mo rong kernel)
// doi lay Latency (systolic cao hon) - se duoc bao cao so sanh trong paper.
// ============================================================================

// --------------------------------------------------------------------------
// BUOC 1: chuoi tre dung chung (shared shift chain) cho mode va valid.
// mode_chain[k]/valid_chain[k] = mode/valid da tre (k+1) chu ky.
// Vi tri POS (1..9) can tre (POS-1) chu ky:
//   POS=1 -> khong tre (dung truc tiep mode/data_valid_in)
//   POS=2..9 -> dung mode_chain[POS-2] / valid_chain[POS-2]
// Tang cuoi (final clip stage) can tre du 9 chu ky -> mode_chain[8]/valid_chain[8]
// --------------------------------------------------------------------------
reg mode_chain [0:8];
reg valid_chain [0:8];
integer ci;

always @(posedge i_clk or posedge i_reset) begin
    if (i_reset) begin
        for (ci = 0; ci < 9; ci = ci + 1) begin
            mode_chain[ci]  <= 1'b0;
            valid_chain[ci] <= 1'b0;
        end
    end
    else begin
        mode_chain[0]  <= mode;
        valid_chain[0] <= data_valid_in;
        for (ci = 1; ci < 9; ci = ci + 1) begin
            mode_chain[ci]  <= mode_chain[ci-1];
            valid_chain[ci] <= valid_chain[ci-1];
        end
    end
end

// --------------------------------------------------------------------------
// BUOC 2: tre rieng cho tung pixel p11..p33 (moi pixel can do tre khac nhau,
// nen khong dung chung 1 chain nhu mode/valid). Vi tri POS ung voi thu tu
// p11,p12,p13,p21,p22,p23,p31,p32,p33 = POS 1..9, do tre = POS-1.
// --------------------------------------------------------------------------
wire [7:0] p_delayed [1:9];

assign p_delayed[1] = p11;   // POS1, do tre 0 (khong can shift_delay)

shift_delay #(.WIDTH(8), .DEPTH(1)) sd_p2 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p12), .o_data(p_delayed[2]));
shift_delay #(.WIDTH(8), .DEPTH(2)) sd_p3 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p13), .o_data(p_delayed[3]));
shift_delay #(.WIDTH(8), .DEPTH(3)) sd_p4 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p21), .o_data(p_delayed[4]));
shift_delay #(.WIDTH(8), .DEPTH(4)) sd_p5 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p22), .o_data(p_delayed[5]));
shift_delay #(.WIDTH(8), .DEPTH(5)) sd_p6 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p23), .o_data(p_delayed[6]));
shift_delay #(.WIDTH(8), .DEPTH(6)) sd_p7 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p31), .o_data(p_delayed[7]));
shift_delay #(.WIDTH(8), .DEPTH(7)) sd_p8 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p32), .o_data(p_delayed[8]));
shift_delay #(.WIDTH(8), .DEPTH(8)) sd_p9 (.i_clk(i_clk), .i_reset(i_reset), .i_data(p33), .o_data(p_delayed[9]));

// --------------------------------------------------------------------------
// BUOC 3: mode/valid cuc bo cho tung PE, lay tu chain o Buoc 1
// --------------------------------------------------------------------------
wire mode_local  [1:9];
wire valid_local [1:9];

assign mode_local[1]  = mode;
assign valid_local[1] = data_valid_in;
assign mode_local[2]  = mode_chain[0];
assign valid_local[2] = valid_chain[0];
assign mode_local[3]  = mode_chain[1];
assign valid_local[3] = valid_chain[1];
assign mode_local[4]  = mode_chain[2];
assign valid_local[4] = valid_chain[2];
assign mode_local[5]  = mode_chain[3];
assign valid_local[5] = valid_chain[3];
assign mode_local[6]  = mode_chain[4];
assign valid_local[6] = valid_chain[4];
assign mode_local[7]  = mode_chain[5];
assign valid_local[7] = valid_chain[5];
assign mode_local[8]  = mode_chain[6];
assign valid_local[8] = valid_chain[6];
assign mode_local[9]  = mode_chain[7];
assign valid_local[9] = valid_chain[7];

// --------------------------------------------------------------------------
// BUOC 4: chon he so kernel theo vi tri POS va mode (thay cho case(mode)
// mot lan duy nhat trong adder tree - o day moi PE chi can biet he so
// cua rieng minh).
// He so giong het conv_multi.v: sharpen (0 -1 0/-1 5 -1/0 -1 0), blur (toan 1).
// --------------------------------------------------------------------------
function signed [7:0] get_weight;
    input integer pos;
    input mode_bit;
    begin
        if (mode_bit == 1'b0) begin
            case (pos)
                1: get_weight = 8'sd0;
                2: get_weight = -8'sd1;
                3: get_weight = 8'sd0;
                4: get_weight = -8'sd1;
                5: get_weight = 8'sd5;
                6: get_weight = -8'sd1;
                7: get_weight = 8'sd0;
                8: get_weight = -8'sd1;
                9: get_weight = 8'sd0;
                default: get_weight = 8'sd0;
            endcase
        end
        else begin
            get_weight = 8'sd1; // blur: tat ca he so = 1, chia sau o tang cuoi
        end
    end
endfunction

wire signed [7:0] w1 = get_weight(1, mode_local[1]);
wire signed [7:0] w2 = get_weight(2, mode_local[2]);
wire signed [7:0] w3 = get_weight(3, mode_local[3]);
wire signed [7:0] w4 = get_weight(4, mode_local[4]);
wire signed [7:0] w5 = get_weight(5, mode_local[5]);
wire signed [7:0] w6 = get_weight(6, mode_local[6]);
wire signed [7:0] w7 = get_weight(7, mode_local[7]);
wire signed [7:0] w8 = get_weight(8, mode_local[8]);
wire signed [7:0] w9 = get_weight(9, mode_local[9]);

// --------------------------------------------------------------------------
// BUOC 5: chuoi 9 PE noi tiep - day la "systolic array" thuc su
// --------------------------------------------------------------------------
wire signed [19:0] psum0 = 20'sd0;   // gia tri khoi dau cho PE dau tien
wire signed [19:0] psum1, psum2, psum3, psum4, psum5, psum6, psum7, psum8, psum9;

systolic_pe #(.ACC_WIDTH(20)) PE1 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[1]), .i_weight(w1), .i_valid(valid_local[1]), .i_partial_sum_in(psum0), .o_partial_sum(psum1));
systolic_pe #(.ACC_WIDTH(20)) PE2 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[2]), .i_weight(w2), .i_valid(valid_local[2]), .i_partial_sum_in(psum1), .o_partial_sum(psum2));
systolic_pe #(.ACC_WIDTH(20)) PE3 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[3]), .i_weight(w3), .i_valid(valid_local[3]), .i_partial_sum_in(psum2), .o_partial_sum(psum3));
systolic_pe #(.ACC_WIDTH(20)) PE4 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[4]), .i_weight(w4), .i_valid(valid_local[4]), .i_partial_sum_in(psum3), .o_partial_sum(psum4));
systolic_pe #(.ACC_WIDTH(20)) PE5 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[5]), .i_weight(w5), .i_valid(valid_local[5]), .i_partial_sum_in(psum4), .o_partial_sum(psum5));
systolic_pe #(.ACC_WIDTH(20)) PE6 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[6]), .i_weight(w6), .i_valid(valid_local[6]), .i_partial_sum_in(psum5), .o_partial_sum(psum6));
systolic_pe #(.ACC_WIDTH(20)) PE7 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[7]), .i_weight(w7), .i_valid(valid_local[7]), .i_partial_sum_in(psum6), .o_partial_sum(psum7));
systolic_pe #(.ACC_WIDTH(20)) PE8 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[8]), .i_weight(w8), .i_valid(valid_local[8]), .i_partial_sum_in(psum7), .o_partial_sum(psum8));
systolic_pe #(.ACC_WIDTH(20)) PE9 (.i_clk(i_clk), .i_reset(i_reset), .i_pixel(p_delayed[9]), .i_weight(w9), .i_valid(valid_local[9]), .i_partial_sum_in(psum8), .o_partial_sum(psum9));

// --------------------------------------------------------------------------
// BUOC 6: tang cuoi - Output + Overflow check, giong het logic tier3 cua
// conv_multi.v (dam bao ket qua toan hoc giong het, chi khac cach tinh tong).
// mode_final/valid_final = tre du 9 chu ky (mode_chain[8]/valid_chain[8]),
// khop voi sum_final = psum9 (cung la ket qua cua window tu 9 chu ky truoc).
// --------------------------------------------------------------------------
wire signed [19:0] sum_final  = psum9;
wire               mode_final  = mode_chain[8];
wire               valid_final = valid_chain[8];
wire signed [30:0] temp_sum_comb = sum_final * 114;   // 1/9 xap xi = 114/1024, giong conv_multi.v

always @(posedge i_clk or posedge i_reset) begin
    if (i_reset) begin
        o_pixel <= 8'd0;
        data_valid_out <= 1'b0;
    end
    else if (valid_final) begin
        if (mode_final == 1'b0) begin
            // SHARPENING
            if (sum_final < 0)
                o_pixel <= 8'd0;
            else if (sum_final > 255)
                o_pixel <= 8'd255;
            else
                o_pixel <= sum_final[7:0];
        end
        else begin
            // BLUR
            if ((temp_sum_comb >>> 10) > 8'd255)
                o_pixel <= 8'd255;
            else
                o_pixel <= temp_sum_comb[17:10];
        end
        data_valid_out <= valid_final;
    end
    else begin
        data_valid_out <= 1'b0;
    end
end

endmodule
