`timescale 1ns/1ps

module tb_top_module;

    reg i_clk;
    reg i_reset;
    reg data_valid_in;
    reg [7:0] i_pixel;
    reg mode;

    wire [7:0] o_pixel;
    wire data_valid_out;

    reg [7:0] image_memory [0:4095];
    integer i;
    integer file_blur, file_sharp;

    top_module uut (
        .i_clk(i_clk),
        .i_reset(i_reset),
        .mode(mode),
        .data_valid_in(data_valid_in),
        .i_pixel(i_pixel),
        .o_pixel(o_pixel),
        .data_valid_out(data_valid_out)
    );

    always #10 i_clk = ~i_clk;

    initial begin
        file_blur  = $fopen("C:/Users/tungd/OneDrive/Desktop/Project_FPGA/output_blur.hex", "w");
        file_sharp = $fopen("C:/Users/tungd/OneDrive/Desktop/Project_FPGA/output_sharp.hex", "w");
        
        forever begin
            @(negedge i_clk); 
            if (data_valid_out) begin
                if (mode == 1) 
                    $fwrite(file_blur, "%02X\n", o_pixel);
                else          
                    $fwrite(file_sharp, "%02X\n", o_pixel);
            end
        end
    end

    initial begin
        $readmemh("C:/Users/tungd/OneDrive/Desktop/Project_FPGA/input_data.hex", image_memory);
        i_clk = 0; i_reset = 1; data_valid_in = 0; i_pixel = 8'd0;
        
        #40; i_reset = 0; #20;

        // --- TEST BLUR ---
        $display("[LOG] Starting BLUR mode...");
        mode = 1; 
        for (i = 0; i < 4096; i = i + 1) begin
            @(posedge i_clk);
            data_valid_in = 1;
            i_pixel = image_memory[i];
        end
        @(posedge i_clk); data_valid_in = 0;
        #4000; 

        // --- TEST SHARPENING ---
        $display("[LOG] Starting SHARPENING mode...");
        mode = 0;
        i_reset = 1; #40; i_reset = 0; #40;
        
        for (i = 0; i < 4096; i = i + 1) begin
            @(posedge i_clk);
            data_valid_in = 1;
            i_pixel = image_memory[i];
        end
        @(posedge i_clk); data_valid_in = 0;
        #4000;

        $fclose(file_blur);
        $fclose(file_sharp);
        $display("[LOG] Simulation Done!");
        $stop;
    end
endmodule