# FPGA_RealTime_Conv3x3_Processor

--- 
## 1. Project Description

This project focuses on the design and implementation of a real-time image processor on an FPGA. The system utilizes a 3x3 Convolution algorithm to perform common image filters such as Blur and Sharpening. The system is optimized using a Pipeline architecture and an Adder Tree to achieve high processing speed, ensuring each pixel is processed in every clock cycle.

### 1.2 Objective
- Understand how 3x3 convolution work.
- How RTL in Modelsim work.
- How different kernels can create different images.

## 2. System Overview
The system is designed to process images in a real-time pipeline. The data flow operates as follows:

* **Input:** A Grayscale image (64x64 pixels) is converted into raw data format (txt/hex) using a Python script. This data is then fed into the FPGA through the `input_interface`.

* **Processing:** The data passes through the `line_buffer` and `window_3x3` modules to create a 3x3 matrix. Depending on the control signal, one of the two modules, `cnn_sharpening.v` or `cnn_blur.v`, will perform the Convolution calculation on these pixels.

* **Output:** The processed pixel result is output from the `top_module` as raw data, which is then captured by another Python script and reconstructed into a viewable image file.

### Limitations

* Verified via RTL simulation only (ModelSim); not yet deployed on physical FPGA hardware.
* Kernel coefficients are hardcoded (not runtime-configurable).
* Tested on 64x64 grayscale images only; RGB and larger resolutions not yet supported.

## 3. General Block Diagram

<img width="5096" height="3839" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/Block_Diagram.png?raw=true" />

## 4. Module Index

| # | Module | File | Role |
|---|--------|------|---------|
| 1 | `top_module` | `top_module.v` | The highest-level top module, connecting the entire system on the FPGA. |
| 2 | `line_buffer` | `line_buffer.v` | Stores 2 lines of image data. This is a crucial module for converting serial data into a 3x3 matrix. |
| 3 | `window_3x3` | `window_3x3.v` | Extracts a 3x3 pixel window (p11 to p33) from the Line Buffer to feed into the Convolution processing core. |
| 4 | `cnn_sharpening` | `cnn_sharpening.v` | Performs convolution with a Sharpening Kernel. |
| 5 | `cnn_blur` | `cnn_blur.v` | Performs convolution with a Blurring Kernel. |
| 6 | `testbench_prj` | `testbench_prj.v` | Module used for simulation, loading images from Python, and verifying output data. |

## External Files & Scripts
| # | Filename | Role | Description |
|---|--------|------|---------|
| 1 | `image_to_hex.py` | Preprocessing | Converts a 64x64 image from common formats (png) to a .txt or .hex file containing pixel values for the testbench. |
| 2 | `hex_to_image.py` | Postprocessing | Reads the output data file from ModelSim, converts it back into a pixel array, and exports it as an image file for quality comparison. |
| 3 | `input_data.hex`  | Input Data | File containing the result after Convolution written from the `top_module` during simulation. |
| 4 | `ouput_data.hex (blur and sharp)` | Output Data | File containing the result after Convolution written from the `top_module` during simulation. |
| 5 | `image/`  | Original Image Folder | Contains sample images (Input) and processed images (Output). |

## 5. Interface Specifications
### 5.1 `top_module`  

| # | Gate | Type | Bit-width | Description |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | System clock signal |
| 2 | `i_reset` | Input | 1-bit | Resets the entire circuit (active-high) |
| 3 | `i_pixel` | Input | 8-bit | Input pixel data (grayscale) |
| 4 | `data_valid_in` | Input | 1-bit | Signals valid input data |
| 5 | `mode` | Input | 1-bit | Selects mode: 0 (Sharpen), 1 (Blur) |
| 6 | `o_pixel` | Output | 8-bit | Processed pixel result |
| 7 | `data_valid_out` | Output | 1-bit | Signals valid output data |

### 5.2 `line_buffer`
| # | Gate | Type | Bit-width | Description |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | System clock signal |
| 2 | `i_reset` | Input | 1-bit | Resets the entire circuit (active-high) |
| 3 | `i_pixel` | Input | 8-bit | Input pixel data (grayscale) received from `top_module` |
| 4 | `q1` | Output | 8-bit | Current data |
| 5 | `q2` | Output | 8-bit | Previous line data (delayed by 1 line) |
| 6 | `q3` | Output | 8-bit | Data from 2 lines ago (delayed by 2 lines) |

### 5.3 `window_3x3`
| # | Gate | Type | Bit-width | Description |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | System clock signal |
| 2 | `i_reset` | Input | 1-bit | Resets the entire circuit (active-high) |
| 3 | `q1`, `q2`, `q3` | Input | 8-bit | Input data from 3 lines (Line Buffer) |
| 4 | `data_valid_in` | Input | 1-bit | Signals valid input data |
| 5 | `p11...p33` | Input | 8-bit(x9) | 9 pixels forming the 3x3 window matrix |

### 5.4 `cnn_sharpening`
| # | Gate | Type | Bit-width | Description |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | System clock signal |
| 2 | `i_reset` | Input | 1-bit | Resets the entire circuit (active-high) |
| 3 | `data_valid_in` | Input | 1-bit | Signals valid input data |
| 4 | `p11...p33` | Input | 8-bit(x9) | Inputs the 3x3 pixel matrix into the convolution |
| 5 | `o_pixel` | Output | 8-bit | Outputs 1 pixel after convolution (sharp) |
| 6 | `data_valid_out` | Output | 1-bit | Signals valid output data |

### 5.5 `cnn_blur`  

| # | Gate | Type | Bit-width | Description |
|---|--------|------|-----|----------|
| 1 | `i_clk` | Input | 1-bit | System clock signal |
| 2 | `i_reset` | Input | 1-bit | Resets the entire circuit (active-high) |
| 3 | `data_valid_in` | Input | 1-bit | Signals valid input data |
| 4 | `p11...p33` | Input | 8-bit(x9) | Inputs the 3x3 pixel matrix into the convolution |
| 5 | `o_pixel` | Output | 8-bit | Outputs 1 pixel after convolution (blur) |
| 6 | `data_valid_out` | Output | 1-bit | Signals valid output data |

## 6. System Workflow

### 1. **Input Stage**
* **Preprocessing (Python)**: The original image (png) is passed through the `image_to_hex.py` script to be converted into an 8-bit pixel value matrix (0-255). The result is saved to the `input_data.hex` file.

<img width="4700" height="3000" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow1.png?raw=true" /> 

***The test image is placed in a folder containing 2 Python files used for image data conversion***

----

<img width="4700" height="3000" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow2.png?raw=true" /> 


* **Data Loading**: During simulation (`testbench_prj.v`), this `.hex` file is read and sequentially pushes each pixel through the `i_pixel` port of the `top_module` at every positive clock edge (`posedge i_clk`). * _Line 46 in the `testbench_prj.v` file_

### 2. **Processing Stage**
* **Data Buffering**: The `line_buffer.v` module receives single pixels, stores, and shifts them through register stages to create 2 line buffers.
* **3x3 Window Generation**: The `window_3x3.v` module takes data from the linebuffer and the current pixel to extract a $3 \times 3$ matrix window (consisting of 9 pixel values `p11` to `p33`).
* **Convolution Calculation**: This $3 \times 3$ window is sent to either the `cnn_sharpening.v` or `cnn_blur.v` module (depending on the `mode`). Here, the pixels are multiplied by the corresponding Kernel coefficients and accumulated through an Adder Tree structure to generate the final resulting pixel.

### 3. **Output Stage**
* **Synchronization**: The calculated result passes through the `output_controller`, where the `data_valid_out` signal is activated to indicate that the data at `o_pixel` is ready.
* **Postprocessing (Python)**: The output pixel values are recorded in the `output_data.hex` file. The `hex_to_image.py` script then reads this file and reconstructs it into a digital image file so you can view and visually compare it.

<img width="4700" height="3000" alt="image" src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow3.png?raw=true" /> 

***These two Hex files will be processed by the hex_to_image script to output the image***

## 7. Simulation & Verification

### 1. **Waveform Result**
The figure below demonstrates the seamless coordination between control signals and data:

<img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/waveform1.png?raw=true" width="45%" align="left" alt="Image 1" />
<img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/waveform2.png?raw=true" width="45%" alt="Image 2" />
<div style="clear: both;"></div>

* **`i_clk` / `i_reset`**: Source signals controlling the entire synchronous state of the integrated circuit.
* **`data_valid_in`**: Activated (*High*) to signal that the input pixel stream has started "flowing" into the `linerbuffer` module.
* **`p11` to `p33`**: The values of 9 consecutive pixels successfully extracted to form a $3 \times 3$ sliding window at each clock cycle.
* **`o_pixel`**: The resulting output pixel after passing through the optimized **Adder Tree** structure.
* **`data_valid_out`**: This signal transitions to a high level (*High*) to indicate that the output pixel is stable and valid, ready to be recorded.

### 2. **Visual Results**
After the simulation is complete, the output data file is read by the Python script `hex_to_image.py` and reconstructed into a digital image structure for visual comparison:

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/input_original.png?raw=true" width="350" alt="Original Input Image"/>
      <br>
      <b>Original Image (Input - Original)</b>
    </td>
    <td align="center">
      <img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/input_grayscale.png?raw=true" width="350" alt="Grayscale Input Image"/>
      <br>
      <b>Original Image (Input - Grayscale 64x64)</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/output_sharpen.png?raw=true" width="350" alt="Sharpen Result"/>
      <br>
      <b>Result after <i>Sharpening</i> filter (FPGA)</b> 
    </td>
    <td align="center">
      <img src="https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/output_blur.png?raw=true" width="350" alt="Blur Result"/>
      <br>
      <b>Result after <i>Blurring</i> filter (FPGA)</b>
    </td>
  </tr>
</table>

----

## 8. Evaluation & Analysis
Based on the hardware simulation results obtained and the images reconstructed via the Python script, the $3 \times 3$ convolution image processing system on the FPGA achieves the following empirical results:
* **Preprocessing Function (Grayscale Conversion)**: The original color image in RGB space has been downsampled to $64 \times 64$ dimensions and successfully converted to 8-bit Grayscale space. The structural blocks and the outlines of the flower remain intact, ensuring a smooth data stream fed into the circuit via the `i_pixel` port.
* **Sharpening Filter Performance**: The borders, edges, spikes, and vein details on the flower petals are highly contrast-enhanced (resulting in distinct black/white boundary regions).
  > _Technical Explanation_: This result proves that the `cnn_sharpening` calculation core has correctly executed the Kernel coefficient matrix (with high weight at the center and negative coefficients surrounding it). Areas with sudden changes in the pixel matrix have their amplitude amplified, proving that the Adder Tree structure does not overflow thanks to the clipping logic operating correctly.
* **Blurring Filter Performance**: All sharp noise details at the image borders are eliminated, and the overall image becomes noticeably smoother and blurrier compared to the original Grayscale image.
  > _Technical Explanation_: The `cnn_blur` module has correctly performed the essence of a Low-pass Filter, leveling the energy difference between adjacent pixels in the $3 \times 3$ sliding window.
* **System Accuracy and Synchronization**: The data flow control signals (`data_valid_in` and `data_valid_out`) operate perfectly under the `i_clk` clock cycle. The image does not suffer from linear distortion or row/column misalignment, affirming that the pixel sliding address management of the `linerbuffer` and `window_3x3` modules is completely synchronized, with no data loss occurring at the boundary pixels.

## 9. Future Work

- Gaussian Filter
- Sobel Edge Detection
- Configurable Convolution Kernel
- RGB Image Support
- Better Verification
