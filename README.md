# FPGA_RealTime_Conv3x3_Processor

--- 

Dự án này tập trung vào việc thiết kế và hiện thực hóa bộ xử lý ảnh thời gian thực trên FPGA. Hệ thống sử dụng thuật toán 3x3 Convolution (Nhân chập) để thực hiện các bộ lọc ảnh phổ biến như Blur (Làm mờ) và Sharpening (Tăng độ sắc nét). Hệ thống được tối ưu hóa bằng kiến trúc Pipeline và Adder Tree để đạt tốc độ xử lý cao, đảm bảo mỗi pixel được xử lý trong mỗi chu kỳ clock.

## 1. Tổng quan hệ thống (System Overview)
Hệ thống được thiết kế để xử lý ảnh theo quy trình thời gian thực. Luồng dữ liệu hoạt động như sau:

* Đầu vào (Input): Một ảnh Grayscale (64x64 pixel) được chuyển đổi sang định dạng dữ liệu thô (txt/hex) bằng script Python. Dữ liệu này sau đó được nạp vào FPGA thông qua input_interface.

* Xử lý (Processing): Dữ liệu được đưa qua các module line_buffer và window_3x3 để tạo ma trận 3x3. Tùy thuộc vào tín hiệu điều khiển, một trong hai module cnn_sharpening.v hoặc cnn_blur.v sẽ thực hiện tính toán Convolution trên các pixel này.

* Đầu ra (Output): Kết quả pixel sau xử lý được xuất ra từ top_module dưới dạng dữ liệu thô, sau đó được một script Python khác thu nhận và tái tạo lại thành file ảnh hiển thị được.

## 2. Sơ đồ khối tổng quát

<img width="5096" height="3839" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/Block_Diagram.png?raw=true" />

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
| 1 | `image_to_hex.py` | Tiền xử lý (Preprocessing) | Chuyển đổi ảnh 64x64 từ các định dạng thông thường (png) sang file .txt hoặc .hex chứa giá trị pixel để đưa vào testbench. |
| 2 | `hex_to_image.py` | Hậu xử lý (Postprocessing) |Đọc file dữ liệu kết quả từ ModelSim, chuyển đổi lại thành mảng pixel và xuất ra file ảnh để so sánh chất lượng. |
| 3 | `test_input.hex`  | Dữ liệu đầu vào | File chứa kết quả sau khi Convolution được ghi ra từ top_module trong quá trình mô phỏng. |
| 4 | `ouput_data.hex` | Dữ liệu đầu ra | File chứa kết quả sau khi Convolution được ghi ra từ top_module trong quá trình mô phỏng. |
| 5 | `image_source/`  | Thư mục ảnh gốc | Chứa các ảnh mẫu (Input) và ảnh sau khi xử lý (Output). |

## 4. Chi tiết chân tín hiệu I/O từng module (Interface Specifications)
### 4.1 `top_module`  

| # | Gate | Type | Bit-width | Mô tả |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | Xung clock hệ thống |
| 2 | `i_reset` | Input | 1-bit | Có vai trò khởi động lại toàn bộ mạch (active-high) |
| 3 | `i_pixel` | Input | 8-bit | Dữ liệu pixel đầu vào (grayscale) |
| 4 | `data_valid_in` | Input | 1-bit | Báo hiệu dữ liệu đầu vào hợp lệ |
| 5 | `mode` | Input | 1-bit | Chọn chế độ: 0 (Sharpen), 1 (Blur) |
| 6 | `o_pixel` | Output | 8-bit | Kết quả pixel đã xử lý |
| 7 | `data_valid_out` | Output | 1-bit | Báo hiệu dữ liệu đầu ra hợp lệ |

### 4.2 `line_buffer`
| # | Gate | Type | Bit-width | Mô tả |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | Xung clock hệ thống |
| 2 | `i_reset` | Input | 1-bit | Có vai trò khởi động lại toàn bộ mạch (active-high) |
| 3 | `i_pixel` | Input | 8-bit | Dữ liệu pixel đầu vào (grayscale) nhận từ `top_module` |
| 4 | `q1` | Output | 8-bit | Dữ liệu hiện tại |
| 4 | `q2` | Output | 8-bit | Dữ liệu dòng trên (đã trễ 1 dòng) |
| 5 | `q3` | Output | 8-bit | Dữ liệu dòng dưới (đã trễ 2 dòng) |

### 4.3 `window_3x3`
| # | Gate | Type | Bit-width | Mô tả |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | Xung clock hệ thống |
| 2 | `i_reset` | Input | 1-bit | Có vai trò khởi động lại toàn bộ mạch (active-high) |
| 3 | `q1`, `q2`, `q3` | Input | 8-bit | Dữ liệu đầu vào từ 3 hàng (Line Buffer)|
| 4 | `data_valid_in` | Input | 1-bit | Báo hiệu dữ liệu đầu vào hợp lệ |
| 5 | `p11...p33` | Input | 8-bit(x9) | 9 pixel tạo thành ma trận cửa sổ 3x3 |

### 4.4 `cnn_sharpening`
| # | Gate | Type | Bit-width | Mô tả |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | Xung clock hệ thông |
| 2 | `i_reset` | Input | 1-bit | Có vai trò khởi đọng toàn bộ mạch (active-high) |
| 3 | `data_valid_in` | Input | 1-bit | Báo dữ liệu đầu vào hợp lệ |
| 4 | `p11...p33` | Input | 8-bit(x9) | đưa ma trận 3x3 pixel vào convolution |
| 5 | `o_pixel` | Output | 8-bit | đưa ra 1 pixel sau khi convolution (sharp) |
| 6 | `data_valid_out` | Output | 1-bit | Báo dữ liệu ra hợp lệ |

### 4.5 `cnn_blur` 

| # | Gate | Type | Bit-width | Mô tả |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | Xung clock hệ thông |
| 2 | `i_reset` | Input | 1-bit | Có vai trò khởi đọng toàn bộ mạch (active-high) |
| 3 | `data_valid_in` | Input | 1-bit | Báo dữ liệu đầu vào hợp lệ |
| 4 | `p11...p33` | Input | 8-bit(x9) | đưa ma trận 3x3 pixel vào convolution |
| 5 | `o_pixel` | Output | 8-bit | đưa ra 1 pixel sau khi convolution (blur) |
| 6 | `data_valid_out` | Output | 1-bit | Báo dữ liệu ra hợp lệ |

## 5. Luồng hoạt động hệ thống (System Workflow)

### 1. **Chuẩn bị và nạp dữ liệu (Input Stage)**
* **Tiền xử lý (Python)**: Ảnh gốc (png) được đưa qua script image_to_hex.py để chuyển đổi sang ma trận giá trị pixel 8-bit (0-255). Kết quả được lưu vào file input_data.hex.

<img width="4700" height="3000" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow1.png?raw=true" /> 

***Ảnh test được bỏ vào tệp có chứa 2 file python dùng để chuyển đổi dữ liệu ảnh***

----

<img width="4700" height="3000" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow2.png?raw=true" /> 


* **Nạp dữ liệu**: Trong quá trình mô phỏng (testbench_prj.v), file .hex này được đọc vào và đẩy tuần tự từng pixel qua cổng i_pixel của top_module tại mỗi sườn dương của xung clock (posedge i_clk). (_Dòng 46 trong file testbench_prj.v_)

### 2. **Xử lý Convolution (Processing Stage)**
* **Đệm dữ liệu**: Module linerbuffer.v nhận các pixel đơn lẻ, lưu trữ và dịch chuyển chúng qua các tầng ghi để tạo ra 2 dòng đệm (Line buffers).
* **Tạo cửa sổ 3x3**:  Module window_3x3.v lấy dữ liệu từ linerbuffer và pixel hiện tại để trích xuất ra một cửa sổ ma trận $3 \times 3$ (gồm 9 giá trị pixel p11 đến p33).
* **Tính toán nhân chập**: Cửa sổ $3 \times 3$ này được gửi tới một trong hai module cnn_sharpening.v hoặc cnn_blur.v (tùy vào chế độ mode). Tại đây, các pixel sẽ được nhân với hệ số Kernel tương ứng và cộng dồn qua cấu trúc cây cộng (Adder Tree) để tạo ra pixel kết quả cuối cùng.

### 3. **Xuất và Tái tạo ảnh (Output Stage)**
* **Đồng bộ hoá**: Kết quả sau khi tính toán được đưa qua output_controller, tại đây tín hiệu data_valid_out được kích hoạt để báo hiệu rằng dữ liệu tại o_pixel đã sẵn sàng.
* **Hậu xử lý (Python)**: Các giá trị pixel đầu ra được ghi lại vào file output_data.txt. Script hex_to_image.py sau đó sẽ đọc file này và tái tạo lại thành file ảnh kỹ thuật số để bạn có thể xem và so sánh trực quan.
