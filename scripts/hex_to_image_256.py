import numpy as np
from PIL import Image

WIDTH = 256  # Thay bằng chiều rộng thực tế của ảnh
HEIGHT = 256 # Thay bằng chiều cao thực tế của ảnh

def hex_to_image(hex_file, output_image):
    with open(hex_file, 'r') as f:
        hex_data = f.read().splitlines()
    pixel_values = [int(line, 16) for line in hex_data if line.strip()]
    if len(pixel_values) != WIDTH * HEIGHT:
        print(f"Cảnh báo: Số lượng pixel ({len(pixel_values)}) không khớp với kích thước ảnh ({WIDTH * HEIGHT})!")
    img_array = np.array(pixel_values, dtype=np.uint8).reshape((HEIGHT, WIDTH))
    img = Image.fromarray(img_array, mode='L')
    img.save(output_image)
    print(f"Đã convert thành công sang file: {output_image}")

# Chạy lệnh
hex_to_image('output_sharp_256.hex', 'ouput_sharp_256.png')
hex_to_image('output_blur_256.hex', 'ouput_blur_256.png')