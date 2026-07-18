# FPGA_RealTime_Conv3x3_Processor

---

## 1. Project Description

This project implements a real-time image processor on an FPGA using a 3x3 Convolution algorithm to perform common image filters such as Blur and Sharpening. The convolution core — the part of the system responsible for accumulating the 9 multiply results of the 3x3 window — is implemented in **two alternative hardware architectures**:

1. **Adder Tree** (`conv_multi.v`): all 9 multiply-accumulate terms are summed combinationally in a single clock cycle using a tree of adders.
2. **Systolic Array** (`conv_systolic.v` + `systolic_pe.v` + `shift_delay.v`): the same 9-term accumulation is broken into a chain of 9 Processing Elements (PE), each performing exactly one multiply and one add per clock cycle.

Both architectures are functionally equivalent (produce the same convolution result) but differ in critical path length, pipeline latency, and hardware resource usage — this trade-off is the central comparison of this project (see Section 8 onward).

### 1.2 Objective

- Understand how 3x3 convolution works and how it is implemented in RTL.
- Understand how a combinational adder tree accumulator works, and its critical-path limitation as kernel size grows.
- Understand how a systolic-array (single-MAC-per-stage) accumulator works, and how it trades latency for a shorter, size-independent critical path.
- Compare both architectures quantitatively — hardware resource usage (LUT/FF/DSP) and maximum clock frequency (Fmax) — using Vivado synthesis and implementation reports.
- Verify both architectures produce numerically correct convolution results using an independent Python golden model.

---

## Table of Contents

1. [Project Description](#1-project-description)
2. [System Overview](#2-system-overview)
3. [General Block Diagram](#3-general-block-diagram)
4. [Repository Structure](#4-repository-structure)
5. [Module Index](#5-module-index)
6. [Interface Specifications](#6-interface-specifications)
7. [System Workflow](#7-system-workflow)
8. [Verification Methodology](#8-verification-methodology)
9. [Experimental Results](#9-experimental-results)
10. [Comparison & Trade-off Discussion](#10-comparison--trade-off-discussion)
11. [Limitations](#11-limitations)
12. [Future Work](#12-future-work)

---

## 2. System Overview

The system processes a 64x64 grayscale image through a real-time streaming pipeline:

- **Input:** A grayscale image is converted into raw pixel data (`.hex`/`.txt`) using a Python preprocessing script. This data is streamed into the FPGA one pixel per clock cycle through `i_pixel`, gated by `data_valid_in`.
- **Buffering & Windowing:** The `line_buffer` module stores 2 previous rows of the image, and `window_3x3` combines them with the current pixel to form a 3x3 sliding window (`p11` to `p33`) at every clock cycle.
- **Convolution:** The 3x3 window is passed to the convolution core, which multiplies each pixel by its corresponding kernel coefficient (selected by the `mode` signal — Sharpen or Blur) and accumulates the 9 products into a single result. **This is the stage where the Adder Tree and Systolic Array architectures differ** — everything before and after this stage (`line_buffer`, `window_3x3`, output handling) is identical between both versions.
- **Output:** The resulting pixel is output through `o_pixel`, synchronized with `data_valid_out`. A Python postprocessing script reconstructs the output pixel stream back into a viewable image.

---

## 3. General Block Diagram

<!-- Dan anh block diagram tong quat (line_buffer -> window_3x3 -> convolution core -> output) vao day.
     Chi can doi ten file duoi day thanh dung ten anh cua ban, vd: image/block_diagram.png -->
![System Block Diagram](image/TEN_ANH_BLOCK_DIAGRAM.png)

---

## 4. Repository Structure

```
FPGA_RealTime_Conv3x3_Processor/
├── src/
│   ├── common/                      # module dung chung cho ca 2 kien truc
│   │   ├── line_buffer.v
│   │   └── window_3x3.v
│   ├── adder_tree/                  # kien truc adder tree
│   │   ├── conv_multi.v
│   │   └── top_module.v             # ban goi conv_multi
│   └── systolic/                    # kien truc systolic
│       ├── shift_delay.v
│       ├── systolic_pe.v
│       ├── conv_systolic.v
│       └── top_module.v             # ban goi conv_systolic
├── constraints/
│   └── constraints.xdc              # dung chung cho ca 2 project Vivado
├── testbench/
│   └── testbench_prj.v              # dung chung, khong doi
├── golden_model/
│   └── golden_model.py
├── scripts/
│   ├── image_to_hex.py
│   └── hex_to_image.py
├── results/
│   ├── adder_tree/
│   │   ├── utilization_report.txt   # xuat tu Vivado (Report Utilization)
│   │   ├── timing_summary.txt       # xuat tu Vivado (Report Timing Summary)
│   │   └── output_sharp.hex, output_blur.hex
│   ├── systolic/
│   │   ├── utilization_report.txt
│   │   ├── timing_summary.txt
│   │   └── output_sharp.hex, output_blur.hex
│   └── comparison_table.md          # bang so sanh cuoi cung cho paper
├── image/
└── README.md
```

---

## 5. Module Index

| # | Module           | File               | Role                                                                                                        |
| --- | ---------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1 | `top_module`     | `top_module.v`     | The highest-level top module, connecting the entire system on the FPGA.                                     |
| 2 | `line_buffer`    | `line_buffer.v`    | Stores 2 lines of image data. Converts serial pixel data into a 3x3 matrix.                                  |
| 3 | `window_3x3`     | `window_3x3.v`     | Extracts a 3x3 pixel window (p11 to p33) from the Line Buffer to feed into the convolution core.             |
| 4 | `conv_multi`     | `conv_multi.v`     | Convolution core — **Adder Tree** architecture. Selects Sharpen/Blur kernel via `mode`, accumulates via a combinational adder tree. |
| 5 | `conv_systolic`  | `conv_systolic.v`  | Convolution core — **Systolic Array** architecture. Same interface as `conv_multi`, accumulates via a chain of 9 Processing Elements. |
| 6 | `systolic_pe`    | `systolic_pe.v`    | A single Processing Element used by `conv_systolic`: performs one multiply and one add per clock cycle.      |
| 7 | `shift_delay`    | `shift_delay.v`    | Generic N-cycle delay utility, used by `conv_systolic` to align pixel/mode/valid timing across the PE chain. |
| 8 | `testbench_prj`  | `testbench_prj.v`  | Simulation testbench: loads images from Python, drives the DUT, and writes output data for verification.     |

---

## 6. Interface Specifications

### 6.1 `top_module`

<!-- Dan anh cau truc/so do cua top_module vao day, doi ten file cho khop -->
![top_module structure](image/TEN_ANH_TOP_MODULE.png)

| # | Gate             | Type   | Bit-width | Description                             |
| --- | ---------------- | ------ | --------- | ---------------------------------------- |
| 1 | `i_clk`          | Input  | 1-bit     | System clock signal                     |
| 2 | `i_reset`        | Input  | 1-bit     | Resets the entire circuit (active-high) |
| 3 | `i_pixel`        | Input  | 8-bit     | Input pixel data (grayscale)            |
| 4 | `data_valid_in`  | Input  | 1-bit     | Signals valid input data                |
| 5 | `mode`           | Input  | 1-bit     | Selects mode: 0 (Sharpen), 1 (Blur)     |
| 6 | `o_pixel`        | Output | 8-bit     | Processed pixel result                  |
| 7 | `data_valid_out` | Output | 1-bit     | Signals valid output data                |

### 6.2 `line_buffer`

<!-- Dan anh cau truc/so do cua line_buffer vao day, doi ten file cho khop -->
![line_buffer structure](image/TEN_ANH_LINE_BUFFER.png)

| # | Gate      | Type   | Bit-width | Description                                             |
| --- | --------- | ------ | --------- | -------------------------------------------------------- |
| 1 | `i_clk`   | Input  | 1-bit     | System clock signal                                     |
| 2 | `i_reset` | Input  | 1-bit     | Resets the entire circuit (active-high)                 |
| 3 | `i_pixel` | Input  | 8-bit     | Input pixel data (grayscale) received from `top_module` |
| 4 | `q1`      | Output | 8-bit     | Current data                                            |
| 5 | `q2`      | Output | 8-bit     | Previous line data (delayed by 1 line)                  |
| 6 | `q3`      | Output | 8-bit     | Data from 2 lines ago (delayed by 2 lines)              |

### 6.3 `window_3x3`

<!-- Dan anh cau truc/so do cua window_3x3 vao day, doi ten file cho khop -->
![window_3x3 structure](image/TEN_ANH_WINDOW_3X3.png)

| # | Gate             | Type  | Bit-width | Description                             |
| --- | ---------------- | ----- | --------- | ---------------------------------------- |
| 1 | `i_clk`          | Input | 1-bit     | System clock signal                     |
| 2 | `i_reset`        | Input | 1-bit     | Resets the entire circuit (active-high) |
| 3 | `q1`, `q2`, `q3` | Input | 8-bit     | Input data from 3 lines (Line Buffer)   |
| 4 | `data_valid_in`  | Input | 1-bit     | Signals valid input data                |
| 5 | `p11...p33`      | Output | 8-bit(x9) | 9 pixels forming the 3x3 window matrix  |

### 6.4 Convolution Core

The convolution core is the only stage that differs between the two architectures compared in this project. Both versions share the exact same external interface (`i_clk`, `i_reset`, `data_valid_in`, `mode`, `p11...p33` → `o_pixel`, `data_valid_out`), so either can be instantiated in `top_module.v` without changing any other module.

#### 6.4.1 Adder Tree — `conv_multi.v`

<!-- Dan anh so do khoi cua conv_multi (adder tree) vao day, doi ten file cho khop -->
![conv_multi (Adder Tree) structure](image/TEN_ANH_CONV_MULTI.png)

| # | Gate             | Type   | Bit-width | Description                                      |
| --- | ---------------- | ------ | --------- | -------------------------------------------------- |
| 1 | `i_clk`          | Input  | 1-bit     | System clock signal                              |
| 2 | `i_reset`        | Input  | 1-bit     | Resets the entire circuit (active-high)          |
| 3 | `data_valid_in`  | Input  | 1-bit     | Signals valid input data                         |
| 4 | `mode`           | Input  | 1-bit     | Selects kernel: 0 (Sharpen), 1 (Blur)            |
| 5 | `p11...p33`      | Input  | 8-bit(x9) | Inputs the 3x3 pixel matrix into the convolution |
| 6 | `o_pixel`        | Output | 8-bit     | Outputs 1 pixel after convolution (mode-selected) |
| 7 | `data_valid_out` | Output | 1-bit     | Signals valid output data                        |

**How it works:** all 9 multiply results (`pixel × kernel coefficient`) are computed in parallel in one register stage, then summed together in a single combinational adder tree in the next stage, then clipped/scaled in a final stage. Total pipeline latency: **3 clock cycles**.

#### 6.4.2 Systolic Array

<!-- Dan anh so do tong quat cua kien truc systolic (chuoi 9 PE noi tiep) vao day, doi ten file cho khop -->
![Systolic Array overview](image/TEN_ANH_SYSTOLIC_OVERVIEW.png)

**How it works:** instead of summing all 9 terms in one cycle, the accumulation is broken into a chain of 9 Processing Elements (PE). Each PE performs exactly one multiply and one add per clock cycle, then registers the partial sum before passing it to the next PE. Because a new 3x3 window arrives every clock cycle (not every 9 cycles), each pixel/mode/valid signal must be delayed by an amount matching its position in the chain (handled by `shift_delay.v`) so that every PE always operates on data from the *same* window. Total pipeline latency: **10 clock cycles** (9 PE stages + 1 final output/clipping stage).

##### 6.4.2.1 `conv_systolic.v`

<!-- Dan anh so do chi tiet cua conv_systolic.v (bao gom cac khoi shift_delay va chuoi PE) vao day -->
![conv_systolic.v structure](image/TEN_ANH_CONV_SYSTOLIC.png)

| # | Gate             | Type   | Bit-width | Description                                      |
| --- | ---------------- | ------ | --------- | -------------------------------------------------- |
| 1 | `i_clk`          | Input  | 1-bit     | System clock signal                              |
| 2 | `i_reset`        | Input  | 1-bit     | Resets the entire circuit (active-high)          |
| 3 | `data_valid_in`  | Input  | 1-bit     | Signals valid input data                         |
| 4 | `mode`           | Input  | 1-bit     | Selects kernel: 0 (Sharpen), 1 (Blur)            |
| 5 | `p11...p33`      | Input  | 8-bit(x9) | Inputs the 3x3 pixel matrix into the convolution |
| 6 | `o_pixel`        | Output | 8-bit     | Outputs 1 pixel after convolution (mode-selected) |
| 7 | `data_valid_out` | Output | 1-bit     | Signals valid output data                        |

##### 6.4.2.2 `systolic_pe.v`

<!-- Dan anh so do 1 Processing Element vao day -->
![systolic_pe.v structure](image/TEN_ANH_SYSTOLIC_PE.png)

| # | Gate                 | Type   | Bit-width         | Description                                                        |
| --- | -------------------- | ------ | ----------------- | -------------------------------------------------------------------- |
| 1 | `i_clk`              | Input  | 1-bit             | System clock signal                                                |
| 2 | `i_reset`            | Input  | 1-bit             | Resets the entire circuit (active-high)                            |
| 3 | `i_pixel`            | Input  | 8-bit             | 1 pixel of the 3x3 window, pre-delayed to align with this PE's stage |
| 4 | `i_weight`           | Input  | 8-bit (signed)    | Kernel coefficient corresponding to this PE's position              |
| 5 | `i_valid`            | Input  | 1-bit             | Local valid signal, pre-delayed to align with this PE's stage       |
| 6 | `i_partial_sum_in`   | Input  | 20-bit (signed)   | Partial sum accumulated from the previous PE in the chain           |
| 7 | `o_partial_sum`      | Output | 20-bit (signed)   | Partial sum after adding this PE's multiply result (registered)      |

##### 6.4.2.3 `shift_delay.v`

<!-- Dan anh so do khoi cua shift_delay vao day -->
![shift_delay.v structure](image/TEN_ANH_SHIFT_DELAY.png)

| # | Gate       | Type   | Bit-width       | Description                                          |
| --- | ---------- | ------ | --------------- | ------------------------------------------------------ |
| 1 | `i_clk`    | Input  | 1-bit           | System clock signal                                  |
| 2 | `i_reset`  | Input  | 1-bit           | Resets the entire circuit (active-high)              |
| 3 | `i_data`   | Input  | `WIDTH`-bit      | Signal to be delayed                                 |
| 4 | `o_data`   | Output | `WIDTH`-bit      | `i_data` delayed by `DEPTH` clock cycles (parameter)  |

---

## 7. System Workflow

### 1. Input Stage

- **Preprocessing (Python):** The original image is converted into an 8-bit pixel value matrix (0–255) using `image_to_hex.py`, saved to `input_data.hex`.
- **Data Loading:** During simulation (`testbench_prj.v`), this `.hex` file is read and pushed pixel-by-pixel into `i_pixel` at every rising edge of `i_clk`.

### 2. Processing Stage

- **Data Buffering:** `line_buffer.v` receives single pixels and shifts them through register stages to form 2 line buffers.
- **3x3 Window Generation:** `window_3x3.v` combines line buffer data with the current pixel to extract the 3x3 window (`p11` to `p33`).
- **Convolution Calculation:** The 3x3 window is sent to the convolution core (either `conv_multi.v` or `conv_systolic.v`, depending on which architecture is instantiated in `top_module.v`), which selects the kernel coefficients based on `mode` and accumulates the result.

### 3. Output Stage

- **Synchronization:** `data_valid_out` is asserted to indicate `o_pixel` is ready.
- **Postprocessing (Python):** `output_data.hex` is read by `hex_to_image.py` and reconstructed into a viewable image.

---

## 8. Verification Methodology

Before comparing hardware resource usage and timing between the two architectures, both were verified against an independent software reference ("golden model") to confirm they compute the mathematically correct convolution result, not just that they compile and simulate without errors.

- **Golden Model (`golden_model.py`):** A Python/NumPy implementation of the same fixed-point convolution algorithm (kernel coefficients, accumulator width, clipping, and the blur approximation `sum × 114 >> 10`), used to generate a reference output for a given input image.
- **Test Vectors:** A set of patterns designed to expose specific classes of bugs — all-zero, all-max (saturation), checkerboard (window ordering), single-impulse (kernel coefficient correctness), corner cases (boundary/zero-padding behavior), and random images.
- **Procedure:** for each architecture, the RTL simulation output (`output_data.hex`) is compared pixel-by-pixel against the golden model's output using match rate, PSNR, and SSIM.

---

## 9. Experimental Results

### 9.1 Timing Methodology

Fmax is derived from Vivado's Timing Summary report after implementation, using:

```
Fmax = 1 / (Clock Period − WNS)
```

where **WNS (Worst Negative Slack)** is read directly from the Design Timing Summary. The clock period constraint was iteratively tightened until WNS approached zero, to obtain an accurate Fmax estimate rather than relying on a single loosely-constrained run.

### 9.2 Resource & Timing Comparison

<!-- Dien so lieu that tu Vivado Report Utilization / Report Timing Summary vao bang duoi day -->

| Metric | Adder Tree (`conv_multi.v`) | Systolic Array (`conv_systolic.v`) |
|---|---|---|
| LUT | *(điền số liệu)* | *(điền số liệu)* |
| FF (Flip-Flop) | *(điền số liệu)* | *(điền số liệu)* |
| DSP | *(điền số liệu)* | *(điền số liệu)* |
| Clock Period used for measurement | 5.500 ns | *(điền số liệu)* |
| WNS at that period | 0.150 ns | *(điền số liệu)* |
| **Fmax** | **≈ 186.9 MHz** | *(điền số liệu)* |
| Pipeline Latency | 3 clock cycles | 10 clock cycles |

### 9.3 Verification Results

<!-- Dien ket qua chay golden_model.py cho ca 2 kien truc vao bang duoi day -->

| Metric | Adder Tree | Systolic Array |
|---|---|---|
| Sharpen — Match Rate | *(điền số liệu)* | *(điền số liệu)* |
| Sharpen — PSNR | *(điền số liệu)* | *(điền số liệu)* |
| Blur — Match Rate | *(điền số liệu)* | *(điền số liệu)* |
| Blur — PSNR | *(điền số liệu)* | *(điền số liệu)* |

---

## 10. Comparison & Trade-off Discussion

<!-- Sau khi dien du so lieu o Muc 9, viet 2-3 nhan xet ghep cap uu/nhuoc diem o day.
     Vi du (dien lai theo so lieu that cua ban):
     - Systolic dat Fmax cao hon vi critical path chi con 1 phep nhan + 1 phep cong moi tang,
       thay vi cong don 9 so trong 1 chu ky nhu adder tree - doi lai latency tang tu 3 len 10 chu ky.
     - Adder tree dung it thanh ghi (FF) hon vi khong can 9 tang dang ky trung gian, nhung
       critical path se dai ra nhanh hon khi mo rong kernel (5x5, 7x7...).
-->

*(Viết nhận xét dựa trên số liệu thật ở Mục 9.2 và 9.3)*

---

## 11. Limitations

- Verified via RTL simulation and Vivado synthesis/implementation reports only; not yet deployed on physical FPGA hardware (no on-board Fmax/power measurement).
- Kernel coefficients are hardcoded per mode (chosen via a `case`/mux internally); not yet runtime-configurable through a register interface.
- Tested on 64x64 grayscale images only; RGB and larger resolutions not yet supported.
- The pipeline has no explicit "image boundary" handling: the first ~2 rows of pixels are computed while the internal line buffers are still filling with reset (zero) values.
- Fmax figures are derived from Vivado's static timing analysis (post-implementation), not measured on physical silicon; actual on-board Fmax may differ slightly due to temperature/voltage/process variation.

---

## 12. Future Work

- Gaussian Filter and Sobel Edge Detection support in both convolution core architectures.
- Runtime-configurable convolution kernel (coefficients loaded via a register interface).
- Extending the comparison to larger kernel sizes (5x5, 7x7) to observe how the Fmax gap between Adder Tree and Systolic Array grows with kernel size.
- RGB image support.
- Deployment on physical FPGA hardware with on-board Fmax and power measurement.
- AXI4-Stream wrapper for integration into larger SoC / camera-pipeline systems.
