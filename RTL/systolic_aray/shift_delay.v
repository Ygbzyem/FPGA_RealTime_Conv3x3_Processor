module shift_delay #(
    parameter WIDTH = 16,
    parameter DEPTH = 1     // so chu ky can tre; DEPTH=0 nghia la khong tre (pass-through)
)(
    input i_clk,
    input i_reset,
    input  [WIDTH-1:0] i_data,
    output [WIDTH-1:0] o_data
);

generate
    if (DEPTH == 0) begin : no_delay
        assign o_data = i_data;
    end
    else begin : delayed
        reg [WIDTH-1:0] pipe [0:DEPTH-1];
        integer i;

        always @(posedge i_clk or posedge i_reset) begin
            if (i_reset) begin
                for (i = 0; i < DEPTH; i = i + 1)
                    pipe[i] <= {WIDTH{1'b0}};
            end
            else begin
                pipe[0] <= i_data;
                for (i = 1; i < DEPTH; i = i + 1)
                    pipe[i] <= pipe[i-1];
            end
        end

        assign o_data = pipe[DEPTH-1];
    end
endgenerate

endmodule
