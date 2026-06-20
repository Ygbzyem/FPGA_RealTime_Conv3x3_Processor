import numpy as np
from PIL import Image

# 1. Cấu hình thông số ảnh của bạn (Phải khớp với file input gốc)
WIDTH = 64  # Thay bằng chiều rộng thực tế của ảnh
HEIGHT = 64 # Thay bằng chiều cao thực tế của ảnh

def hex_to_image(hex_file, output_image):
    # Đọc dữ liệu từ file hex
    with open(hex_file, 'r') as f:
        hex_data = f.read().splitlines()
    
    # Chuyển đổi từ Hex sang số nguyên (0-255)
    pixel_values = [int(line, 16) for line in hex_data if line.strip()]
    
    # Kiểm tra xem dữ liệu có đủ không
    if len(pixel_values) != WIDTH * HEIGHT:
        print(f"Cảnh báo: Số lượng pixel ({len(pixel_values)}) không khớp với kích thước ảnh ({WIDTH * HEIGHT})!")
    
    # Tạo mảng ảnh từ dữ liệu
    img_array = np.array(pixel_values, dtype=np.uint8).reshape((HEIGHT, WIDTH))
    
    # Lưu ảnh
    img = Image.fromarray(img_array, mode='L')
    img.save(output_image)
    print(f"Đã convert thành công sang file: {output_image}")

# Chạy lệnh
hex_to_image('output_sharp.hex', 'ouput_sharpen.png')