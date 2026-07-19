import cv2
import numpy as np

def generate_hex_file(image_path, output_hex_name, size=(128, 128)):
    img = cv2.imread(image_path)
    if img is None:
        print("Lỗi: Không tìm thấy ảnh. Kiểm tra lại đường dẫn!")
        return
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized_img = cv2.resize(gray_img, size)


    with open(output_hex_name, 'w') as f:
        for row in resized_img:
            for pixel in row:
                f.write(f"{pixel:02x}\n")
    

    cv2.imwrite("128_grayscale_preview.png", resized_img)
    print(f"Thành công! Đã tạo file: {output_hex_name}")
    print(f"Kích thước ảnh: {size[0]}x{size[1]} = {size[0]*size[1]} pixels.")


# Thay 'input.jpg' bằng tên file ảnh của bạn
generate_hex_file('test.png', 'input_data_128.hex', size=(128, 128))