# FPGA_RealTime_Conv3x3_Processor

# 1. Giới thiệu hệ thống

Dự án này tập trung vào việc thiết kế và hiện thực hóa bộ xử lý ảnh thời gian thực trên FPGA. Hệ thống sử dụng thuật toán 3x3 Convolution (Nhân chập) để thực hiện các bộ lọc ảnh phổ biến như Blur (Làm mờ) và Sharpening (Tăng độ sắc nét). Hệ thống được tối ưu hóa bằng kiến trúc Pipeline và Adder Tree để đạt tốc độ xử lý cao, đảm bảo mỗi pixel được xử lý trong mỗi chu kỳ clock.
