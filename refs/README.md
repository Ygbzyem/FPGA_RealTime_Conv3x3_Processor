# References

This project was developed based on fundamental concepts in digital image processing, FPGA architecture, and convolution-based hardware acceleration. The following references were used throughout the design and implementation process.

---

## Image Processing & Convolution

- **Types of Convolution Kernels**
  https://www.geeksforgeeks.org/deep-learning/types-of-convolution-kernels/

- **Convolutional Layers in AI Model Training: A Deep Dive into 3×3 Filters**
  https://marjavamitjava.com/convolutional-layers-in-ai-model-training-a-deep-dive-into-3x3-filters/

- **Advanced Image Processing – 3×3 Convolution Algorithms (University of Cambridge)**
  https://www.cl.cam.ac.uk/teaching/1617/AdvGraph/04_Advanced_image_proc.pdf

---

## FPGA Image Processing

- **FPGA-Based Brain Tumor Detection from MRI Using 3×3 Convolution Soft IP Core (Stride = 1)**
  https://www.youtube.com/watch?v=5VMVOeyQqiU

- **FPGA Implementation of Image Line Buffer to Split and Reconstruct a 3×3 Image Window**
  https://www.youtube.com/watch?v=E1i-o8glsgg

- **Veling, R. et al., "A Fast FPGA-Based Implementation of Linear and Non-Linear Image Filters," IJECE, Vol. 12, No. 5, 2025.**
  Closely related work: implements sharpening and blurring filters over a 3×3 window in Verilog HDL on a Basys-3 FPGA, synthesized in Xilinx Vivado. Used as a benchmark reference for resource utilization and timing once this project reaches the synthesis stage.
  https://www.internationaljournalssrg.org/IJECE/2025/Volume12-Issue5/IJECE-V12I5P109.pdf

- **"Design space exploration for image processing architectures on FPGA targets," arXiv:1404.3877.**
  Provides the theoretical basis for the line-buffer sizing used in `line_buffer.v` (a kernel of height *H* requires *H−1* line buffers).
  https://arxiv.org/pdf/1404.3877

- **"A Multiwindow Partial Buffering Scheme for FPGA-Based 2-D Convolvers," IEEE Transactions on Circuits and Systems II.**
  Discusses the trade-off between full buffering and partial buffering strategies, relevant to the buffering approach used in `line_buffer.v` and `window_3x3.v`.
  https://ieeexplore.ieee.org/document/4100887/

- **Bourennane, A. et al., "An FPGA Sliding-Window-Based Architecture Harris Corner Detector," IEEE Conference Publication.**
  Sliding-window streaming architecture similar to this project's `window_3x3` design; reports throughput results on Spartan-6 as a reference point for evaluating real-time performance.
  https://ieeexplore.ieee.org/document/6927402/

---

## Filter Design (Blur / Sharpening / Gaussian)

- **"FPGA Implementation of Filtered Image Using 2D Gaussian Filter," IJACSA, Vol. 7, No. 7, 2016.**
  Compares PSNR between software (MATLAB) and hardware (VHDL) filter outputs — a useful model for quantitatively evaluating output image quality beyond visual inspection.
  https://thesai.org/Downloads/Volume7No7/Paper_71-FPGA_implementation_of_filtered_image_using%202D.pdf

- **"Review on Image Enhancement Techniques: FPGA Implementation Perspective."**
  Survey of point-processing and spatial-filtering techniques (including sharpening and smoothing) implemented on FPGA; used as background for the related-work context of `cnn_sharpening.v` and `cnn_blur.v`.
  https://www.academia.edu/2441330/

---

## Pipeline & Adder Tree Architecture

- **"Design of FPGA Hardware Accelerator Based on Convolutional Neural Network," Springer, 2024.**
  Describes a pipelined multiplier and pipelined tree-adder design in Verilog for accelerating convolution — the architectural basis for the Adder Tree structure used in this project's convolution cores.
  https://link.springer.com/chapter/10.1007/978-981-96-0096-0_31

---

## Educational Resources

- **What is Convolution?**
  https://www.youtube.com/watch?v=KuXjwB4LzSA

---

## Standards

- **IEEE Std 1364™ — Verilog Hardware Description Language**
- **IEEE Std 1800™ — SystemVerilog**