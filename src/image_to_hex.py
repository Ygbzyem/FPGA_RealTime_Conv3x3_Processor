import cv2
import numpy as np

def generate_hex_file(image_path, output_hex_name, size=(64, 64)):
    # 1. Đọc ảnh từ máy tính
    img = cv2.imread(image_path)
    if img is None:
        print("Lỗi: Không tìm thấy ảnh. Kiểm tra lại đường dẫn!")
        return

    # 2. Chuyển sang ảnh xám (Grayscale)
    # Mỗi pixel lúc này là 1 số từ 0 đến 255 (8-bit)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Thay đổi kích thước (Resize)
    # Quan trọng: FPGA mô phỏng rất chậm, nên để ảnh nhỏ (64x64 hoặc 128x128)
    resized_img = cv2.resize(gray_img, size)

    # 4. Ghi dữ liệu ra file .hex
    with open(output_hex_name, 'w') as f:
        for row in resized_img:
            for pixel in row:
                # Chuyển số nguyên sang mã Hex 2 ký tự (ví dụ 255 -> ff)
                # và viết mỗi pixel trên 1 dòng
                f.write(f"{pixel:02x}\n")
    
    # Lưu một ảnh xám thực tế để đối chiếu (Golden Model)
    cv2.imwrite("grayscale_preview.png", resized_img)
    print(f"Thành công! Đã tạo file: {output_hex_name}")
    print(f"Kích thước ảnh: {size[0]}x{size[1]} = {size[0]*size[1]} pixels.")

# --- CHẠY THỬ ---
# Thay 'input.jpg' bằng tên file ảnh của bạn
generate_hex_file('test.png', 'input_data.hex', size=(64, 64))