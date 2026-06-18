# FPGA_RealTime_Conv3x3_Processor

--- 

Dự án này tập trung vào việc thiết kế và hiện thực hóa bộ xử lý ảnh thời gian thực trên FPGA. Hệ thống sử dụng thuật toán 3x3 Convolution (Nhân chập) để thực hiện các bộ lọc ảnh phổ biến như Blur (Làm mờ) và Sharpening (Tăng độ sắc nét). Hệ thống được tối ưu hóa bằng kiến trúc Pipeline và Adder Tree để đạt tốc độ xử lý cao, đảm bảo mỗi pixel được xử lý trong mỗi chu kỳ clock.

## 1. Sơ đồ khối tổng quát

<img width="5096" height="3839" alt="image" src="https://github.com/AnhBaChaCuu/FPGA_RealTime_Conv3x3_Processor/blob/e1a4c9134abc59d65a1c13a32b5c7f85ea139965/Block_Diagram.png" />

## 2. Mục lục các module (Module Index)

| # | Module | File | Vai trò |
|---|--------|------|---------|
| 1 | `top_module` | `top_module.v` | Module top cấp cao nhất, kết nối toàn bộ hệ thống lên FPGA |
| 2 | `line_buffer` | `line_buffer.v` | Lưu trữ 2 dòng dữ liệu ảnh. Đây là module cực kỳ quan trọng để chuyển đổi dữ liệu dạng chuỗi (serial) thành ma trận 3x3. |
| 3 | `window_3x3` | `window_3x3.v` |Trích xuất cửa sổ 3x3 pixel (p11 đến p33) từ Line Buffer để đưa vào lõi xử lý Convolution. |
