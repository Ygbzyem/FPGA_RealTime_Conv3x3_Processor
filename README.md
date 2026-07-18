# FPGA_RealTime_Conv3x3_Processor

---

## 1. Project Description

This project focuses on the design and implementation of a real-time image processor on an FPGA. The system utilizes a 3x3 Convolution algorithm to perform common image filters such as Blur and Sharpening. The system is optimized using a Pipeline architecture and an Adder Tree to achieve high processing speed, ensuring each pixel is processed in every clock cycle.

**Version 2.0.0 update**: the convolution core has been refactored from two separate, hardcoded modules (`cnn_sharpening.v`, `cnn_blur.v`) into a single unified module, `conv_multi.v`, which selects the kernel coefficients internally via the existing `mode` signal. This removes duplicated adder-tree logic and establishes a foundation for adding more kernels (Sobel, Gaussian...) without duplicating hardware. See [Version History](#10-version-history) for details.

### 1.2 Objective

- Understand how 3x3 convolution works.
- How RTL in Modelsim works.
- How different kernels can create different images.
- Learn to refactor and verify RTL changes using regression/equivalence testbenches without a physical FPGA board.

## 2. System Overview

The system is designed to process images in a real-time pipeline. The data flow operates as follows:

- **Input:** A Grayscale image (64x64 pixels) is converted into raw data format (txt/hex) using a Python script. This data is then fed into the FPGA through the `input_interface`.

- **Processing:** The data passes through the `line_buffer` and `window_3x3` modules to create a 3x3 matrix. The 3x3 window is then sent to the `conv_multi.v` module, which internally selects the Sharpening or Blurring kernel coefficients based on the `mode` control signal and performs the convolution.

- **Output:** The processed pixel result is output from the `top_module` as raw data, which is then captured by another Python script and reconstructed into a viewable image file.

### Limitations

- Verified via RTL simulation only (ModelSim / Icarus Verilog); not yet deployed on physical FPGA hardware.
- Kernel coefficients are still hardcoded per mode (chosen via a `case`/mux inside `conv_multi.v`); not yet runtime-configurable through a register interface.
- Tested on 64x64 grayscale images only; RGB and larger resolutions not yet supported.
- The pipeline has no explicit "image boundary" handling: the first ~2 rows of pixels are computed while the internal line buffers are still filling with reset (zero) values, so edge pixels near the top of the image should be interpreted with this in mind.
- Regression testing (see Section 7.3) confirms `conv_multi.v` is bit-exact with the original `cnn_sharpening.v`; the blur path differs by one clock cycle from the original `cnn_blur.v` due to a timing bug found and fixed during the refactor (see Section 7.3 and Version History).

## 3. General Block Diagram

*(Diagram needs to be updated to reflect the new architecture: `cnn_sharpening.v` and `cnn_blur.v` are replaced by a single `conv_multi.v` block, selected internally by `mode` instead of an external output mux.)*

[![image](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/Block_Diagram.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/Block_Diagram.png?raw=true)

## 4. Module Index

| # | Module           | File               | Role                                                                                                        |
| --- | ---------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1 | `top_module`     | `top_module.v`     | The highest-level top module, connecting the entire system on the FPGA.                                     |
| 2 | `line_buffer`    | `line_buffer.v`    | Stores 2 lines of image data. This is a crucial module for converting serial data into a 3x3 matrix.        |
| 3 | `window_3x3`     | `window_3x3.v`     | Extracts a 3x3 pixel window (p11 to p33) from the Line Buffer to feed into the Convolution processing core. |
| 4 | `conv_multi`     | `conv_multi.v`     | Unified convolution core. Selects Sharpening or Blurring kernel coefficients internally based on `mode`, then performs the multiply-accumulate and clipping. Replaces the previous `cnn_sharpening.v` + `cnn_blur.v` pair. |
| 5 | `testbench_prj`  | `testbench_prj.v`  | Module used for simulation, loading images from Python, and verifying output data.                          |
| 6 | `tb_equivalence` | `tb_equivalence.v` | Regression testbench: verifies `conv_multi.v` produces bit-exact results against the original `cnn_sharpening.v` / `cnn_blur.v` pair under randomized stimulus. |
| 7 | `tb_lbw_equivalence` | `tb_lbw_equivalence.v` | Regression testbench: verifies the coding-style fix in `line_buffer.v` / `window_3x3.v` (blocking → non-blocking assignment in reset) does not change functional behavior. |

> Legacy modules `cnn_sharpening.v` and `cnn_blur.v` are kept under `src/v1_legacy/` for historical reference and as the baseline for regression testing; they are no longer instantiated by `top_module.v`.

## External Files & Scripts

| # | Filename                          | Role                  | Description                                                                                                                            |
| --- | --------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | `image_to_hex.py`                 | Preprocessing         | Converts a 64x64 image from common formats (png) to a .txt or .hex file containing pixel values for the testbench.                     |
| 2 | `hex_to_image.py`                 | Postprocessing        | Reads the output data file from ModelSim, converts it back into a pixel array, and exports it as an image file for quality comparison. |
| 3 | `input_data.hex`                  | Input Data            | File containing the result after Convolution written from the `top_module` during simulation.                                          |
| 4 | `output_data.hex (blur and sharp)` | Output Data           | File containing the result after Convolution written from the `top_module` during simulation.                                          |
| 5 | `image/`                          | Original Image Folder | Contains sample images (Input) and processed images (Output).                                                                          |

## 5. Interface Specifications

### 5.1 `top_module`

| # | Gate             | Type   | Bit-width | Description                             |
| --- | ---------------- | ------ | --------- | ---------------------------------------- |
| 1 | `i_clk`          | Input  | 1-bit     | System clock signal                     |
| 2 | `i_reset`        | Input  | 1-bit     | Resets the entire circuit (active-high) |
| 3 | `i_pixel`        | Input  | 8-bit     | Input pixel data (grayscale)            |
| 4 | `data_valid_in`  | Input  | 1-bit     | Signals valid input data                |
| 5 | `mode`           | Input  | 1-bit     | Selects mode: 0 (Sharpen), 1 (Blur)     |
| 6 | `o_pixel`        | Output | 8-bit     | Processed pixel result                  |
| 7 | `data_valid_out` | Output | 1-bit     | Signals valid output data                |

*(unchanged - `top_module`'s external interface is identical to v1.0.0)*

### 5.2 `line_buffer`

| # | Gate      | Type   | Bit-width | Description                                             |
| --- | --------- | ------ | --------- | -------------------------------------------------------- |
| 1 | `i_clk`   | Input  | 1-bit     | System clock signal                                     |
| 2 | `i_reset` | Input  | 1-bit     | Resets the entire circuit (active-high)                 |
| 3 | `i_pixel` | Input  | 8-bit     | Input pixel data (grayscale) received from `top_module` |
| 4 | `q1`      | Output | 8-bit     | Current data                                            |
| 5 | `q2`      | Output | 8-bit     | Previous line data (delayed by 1 line)                  |
| 6 | `q3`      | Output | 8-bit     | Data from 2 lines ago (delayed by 2 lines)              |

*(v2.0.0: internal reset logic fixed from blocking to non-blocking assignment; interface and functional behavior unchanged, confirmed via `tb_lbw_equivalence.v`.)*

### 5.3 `window_3x3`

| # | Gate             | Type  | Bit-width | Description                             |
| --- | ---------------- | ----- | --------- | ---------------------------------------- |
| 1 | `i_clk`          | Input | 1-bit     | System clock signal                     |
| 2 | `i_reset`        | Input | 1-bit     | Resets the entire circuit (active-high) |
| 3 | `q1`, `q2`, `q3` | Input | 8-bit     | Input data from 3 lines (Line Buffer)   |
| 4 | `data_valid_in`  | Input | 1-bit     | Signals valid input data                |
| 5 | `p11...p33`      | Input | 8-bit(x9) | 9 pixels forming the 3x3 window matrix  |

*(v2.0.0: internal reset logic fixed from blocking to non-blocking assignment; interface and functional behavior unchanged, confirmed via `tb_lbw_equivalence.v`.)*

### 5.4 `conv_multi`

*(replaces the previous separate `cnn_sharpening` and `cnn_blur` interface sections)*

| # | Gate             | Type   | Bit-width | Description                                      |
| --- | ---------------- | ------ | --------- | -------------------------------------------------- |
| 1 | `i_clk`          | Input  | 1-bit     | System clock signal                              |
| 2 | `i_reset`        | Input  | 1-bit     | Resets the entire circuit (active-high)          |
| 3 | `data_valid_in`  | Input  | 1-bit     | Signals valid input data                         |
| 4 | `mode`           | Input  | 1-bit     | Selects kernel: 0 (Sharpen), 1 (Blur)            |
| 5 | `p11...p33`      | Input  | 8-bit(x9) | Inputs the 3x3 pixel matrix into the convolution |
| 6 | `o_pixel`        | Output | 8-bit     | Outputs 1 pixel after convolution (mode-selected) |
| 7 | `data_valid_out` | Output | 1-bit     | Signals valid output data                        |

## 6. System Workflow

### 1. **Input Stage**

- **Preprocessing (Python)**: The original image (png) is passed through the `image_to_hex.py` script to be converted into an 8-bit pixel value matrix (0-255). The result is saved to the `input_data.hex` file.

[![image](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/workflow1.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow1.png?raw=true)

***The test image is placed in a folder containing 2 Python files used for image data conversion***

---

[![image](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/workflow2.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow2.png?raw=true)

- **Data Loading**: During simulation (`testbench_prj.v`), this `.hex` file is read and sequentially pushes each pixel through the `i_pixel` port of the `top_module` at every positive clock edge (`posedge i_clk`).

### 2. **Processing Stage**

- **Data Buffering**: The `line_buffer.v` module receives single pixels, stores, and shifts them through register stages to create 2 line buffers.
- **3x3 Window Generation**: The `window_3x3.v` module takes data from the line buffer and the current pixel to extract a 3x3 matrix window (consisting of 9 pixel values `p11` to `p33`).
- **Convolution Calculation**: This 3x3 window is sent to the `conv_multi.v` module. Based on the `mode` signal, the module internally selects the Sharpening or Blurring kernel coefficients, multiplies them with the corresponding pixels, and accumulates the result through an Adder Tree structure to generate the final resulting pixel.

### 3. **Output Stage**

- **Synchronization**: The calculated result passes through the `output_controller`, where the `data_valid_out` signal is activated to indicate that the data at `o_pixel` is ready.
- **Postprocessing (Python)**: The output pixel values are recorded in the `output_data.hex` file. The `hex_to_image.py` script then reads this file and reconstructs it into a digital image file so you can view and visually compare it.

[![image](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/workflow3.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/workflow3.png?raw=true)

## 7. Simulation & Verification

### 1. **Waveform Result**

[![Image 1](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/waveform1.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/waveform1.png?raw=true)

[![Image 2](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/raw/main/image/waveform2.png?raw=true)](https://github.com/LoVuongChiTon67/FPGA_RealTime_Conv3x3_Processor/blob/main/image/waveform2.png?raw=true)

- **`i_clk` / `i_reset`**: Source signals controlling the entire synchronous state of the integrated circuit.
- **`data_valid_in`**: Activated (*High*) to signal that the input pixel stream has started "flowing" into the `line_buffer` module.
- **`p11` to `p33`**: The values of 9 consecutive pixels successfully extracted to form a 3x3 sliding window at each clock cycle.
- **`o_pixel`**: The resulting output pixel after passing through the optimized **Adder Tree** structure.
- **`data_valid_out`**: This signal transitions to a high level (*High*) to indicate that the output pixel is stable and valid, ready to be recorded.

### 2. **Visual Results**

After the simulation is complete, the output data file is read by the Python script `hex_to_image.py` and reconstructed into a digital image structure for visual comparison:

- Original Input Image / Grayscale Input Image
- Sharpen Result / Blur Result

### 3. **Regression / Equivalence Verification (new in v2.0.0)**

When refactoring `cnn_sharpening.v` + `cnn_blur.v` into the unified `conv_multi.v`, two dedicated testbenches were added to make sure the refactor did not silently change functional behavior:

- **`tb_equivalence.v`**: instantiates the original `cnn_sharpening.v` + `cnn_blur.v` (with the original external mux, kept under `src/v1_legacy/`) side-by-side with the new `conv_multi.v`, drives both with the same randomized pixel stream (including edge cases: all-zero, all-max, and mixed patterns), and compares `o_pixel` / `data_valid_out` cycle-by-cycle.
  - **Sharpening path**: 100% bit-exact match against the original module.
  - **Blur path**: found and fixed a genuine timing bug in the original `cnn_blur.v` — a non-blocking assignment (`temp_sum <= sum_p * 114;`) was read back in the same `if` statement before the new value was committed, causing the final blur output to lag its own `data_valid_out` signal by one extra clock cycle. `conv_multi.v` computes this combinationally in the same cycle, so its blur output leads the original by exactly one cycle (verified: 99.98%+ match against the shifted comparison `new[n] == old[n+1]`).
- **`tb_lbw_equivalence.v`**: compares the original `line_buffer.v` / `window_3x3.v` (blocking assignment in reset) against the fixed version (non-blocking assignment), across normal operation, mid-stream resets, and interrupted `data_valid_in` streams. Result: 0 mismatches — the coding-style fix does not change functional behavior.

These testbenches are kept in the repository as a regression baseline for any future architectural change (e.g. the planned systolic-array pipeline, see Future Work).

## 8. Evaluation & Analysis

Based on the hardware simulation results obtained and the images reconstructed via the Python script, the 3x3 convolution image processing system on the FPGA achieves the following empirical results:

- **Preprocessing Function (Grayscale Conversion)**: The original color image in RGB space has been downsampled to 64x64 dimensions and successfully converted to 8-bit Grayscale space. The structural blocks and the outlines of the flower remain intact, ensuring a smooth data stream fed into the circuit via the `i_pixel` port.
- **Sharpening Filter Performance**: The borders, edges, spikes, and vein details on the flower petals are highly contrast-enhanced (resulting in distinct black/white boundary regions).

> *Technical Explanation*: This result proves that the `conv_multi` sharpening path has correctly executed the Kernel coefficient matrix (with high weight at the center and negative coefficients surrounding it). Areas with sudden changes in the pixel matrix have their amplitude amplified, proving that the Adder Tree structure does not overflow thanks to the clipping logic operating correctly.

- **Blurring Filter Performance**: All sharp noise details at the image borders are eliminated, and the overall image becomes noticeably smoother and blurrier compared to the original Grayscale image.

> *Technical Explanation*: The `conv_multi` blur path has correctly performed the essence of a Low-pass Filter, leveling the energy difference between adjacent pixels in the 3x3 sliding window. Note: pixel values from this path are now computed one clock cycle earlier than the original `cnn_blur.v`, due to the timing bug fix described in Section 7.3 — the reconstructed image content itself is unaffected.

- **System Accuracy and Synchronization**: The data flow control signals (`data_valid_in` and `data_valid_out`) operate correctly under the `i_clk` clock cycle. Regression testing against the original modules (Section 7.3) confirms the unified core is functionally equivalent (bit-exact for sharpening, and correctly ahead-by-one-cycle for the fixed blur timing bug), with no additional distortion introduced by the refactor.

## 9. Future Work

- Gaussian Filter and Sobel Edge Detection (extending `conv_multi.v`'s internal kernel selection)
- Runtime-configurable convolution kernel (coefficients loaded via a register interface, rather than a fixed `case`/mux)
- RGB Image Support
- Systolic-array pipeline architecture (replacing the combinational adder tree with a chain of single-MAC processing elements) to improve Fmax scalability for larger kernels
- Synthesis and deployment on physical FPGA hardware, with resource/timing/power measurement
- AXI4-Stream wrapper for integration into larger SoC / camera-pipeline systems

## 10. Version History

| Version | Date | Changes |
|---|---|---|
| v1.0.0 | 2026-06-29 | Initial release: separate `cnn_sharpening.v` / `cnn_blur.v` modules, selected via an external output mux in `top_module.v`. |
| v2.0.0 | *(pending)* | Unified `cnn_sharpening.v` + `cnn_blur.v` into a single `conv_multi.v` core (internal mode-based kernel selection). Fixed a timing bug in the blur path (stale `temp_sum` read). Fixed blocking/non-blocking assignment inconsistency in `line_buffer.v` and `window_3x3.v` reset logic. Added `tb_equivalence.v` and `tb_lbw_equivalence.v` regression testbenches. Legacy v1 modules kept under `src/v1_legacy/` for comparison. |

## About

Real-time 2D Image Convolution Processor implemented on FPGA using Verilog HDL. Supports Blur and Sharpening kernels through a unified, mode-selectable convolution core.
