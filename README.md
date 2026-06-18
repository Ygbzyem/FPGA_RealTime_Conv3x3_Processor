# FPGA_RealTime_Conv3x3_Processor

--- 

Dự án này tập trung vào việc thiết kế và hiện thực hóa bộ xử lý ảnh thời gian thực trên FPGA. Hệ thống sử dụng thuật toán 3x3 Convolution (Nhân chập) để thực hiện các bộ lọc ảnh phổ biến như Blur (Làm mờ) và Sharpening (Tăng độ sắc nét). Hệ thống được tối ưu hóa bằng kiến trúc Pipeline và Adder Tree để đạt tốc độ xử lý cao, đảm bảo mỗi pixel được xử lý trong mỗi chu kỳ clock.

## 1. Tổng quan hệ thống (System Workflow)
Hệ thống được thiết kế để xử lý ảnh theo quy trình thời gian thực. Luồng dữ liệu hoạt động như sau:

* Đầu vào (Input): Một ảnh Grayscale (64x64 pixel) được chuyển đổi sang định dạng dữ liệu thô (txt/hex) bằng script Python. Dữ liệu này sau đó được nạp vào FPGA thông qua input_interface.

* Xử lý (Processing): Dữ liệu được đưa qua các module line_buffer và window_3x3 để tạo ma trận 3x3. Tùy thuộc vào tín hiệu điều khiển, một trong hai module cnn_sharpening.v hoặc cnn_blur.v sẽ thực hiện tính toán Convolution trên các pixel này.

* Đầu ra (Output): Kết quả pixel sau xử lý được xuất ra từ top_module dưới dạng dữ liệu thô, sau đó được một script Python khác thu nhận và tái tạo lại thành file ảnh hiển thị được.

## 2. Sơ đồ khối tổng quát

<img width="5096" height="3839" alt="image" src="https://github.com/AnhBaChaCuu/FPGA_RealTime_Conv3x3_Processor/blob/e1a4c9134abc59d65a1c13a32b5c7f85ea139965/Block_Diagram.png" />

## 3. Mục lục các module (Module Index)

| # | Module | File | Vai trò |
|---|--------|------|---------|
| 1 | `top_module` | `top_module.v` | Module top cấp cao nhất, kết nối toàn bộ hệ thống lên FPGA. |
| 2 | `line_buffer` | `line_buffer.v` | Lưu trữ 2 dòng dữ liệu ảnh. Đây là module cực kỳ quan trọng để chuyển đổi dữ liệu dạng chuỗi (serial) thành ma trận 3x3. |
| 3 | `window_3x3` | `window_3x3.v` |Trích xuất cửa sổ 3x3 pixel (p11 đến p33) từ Line Buffer để đưa vào lõi xử lý Convolution. 
| 4 | `cnn_sharpening` | `cnn_sharpening.v` |Thực hiện phép nhân chập với Kernel làm sắc nét ảnh (Sharpening).
| 5 | `cnn_blur` | `cnn_blur.v` |Thực hiện phép nhân chập với Kernel làm mờ ảnh (Blur).
| 6 | `testbench_prj` | `testbench_prj.v` |Module dùng để mô phỏng, nạp ảnh từ Python và kiểm chứng dữ liệu đầu ra.

## Danh sách tệp tin bổ trợ (External Files & Scripts)
| # | Filename | Vai trò | Mô tả |
|---|--------|------|---------|
| 1 | `image_to_hex.py` | Tiền xử lý (Preprocessing) | Chuyển đổi ảnh 64x64 từ các định dạng thông thường (.jpg, .png) sang file .txt hoặc .hex chứa giá trị pixel để đưa vào testbench. |
| 2 | `hex_to_image.py` | Hậu xử lý (Postprocessing) |Đọc file dữ liệu kết quả từ ModelSim, chuyển đổi lại thành mảng pixel và xuất ra file ảnh để so sánh chất lượng. |
| 3 | `test_input.hex`  | Dữ liệu đầu vào | File chứa kết quả sau khi Convolution được ghi ra từ top_module trong quá trình mô phỏng. |
| 4 | `ouput_data.hex` | Dữ liệu đầu ra | File chứa kết quả sau khi Convolution được ghi ra từ top_module trong quá trình mô phỏng. |
| 5 | `image_source/`  | Thư mục ảnh gốc | Chứa các ảnh mẫu (Input) và ảnh sau khi xử lý (Output). |
