`default_nettype none

module Register
  #(parameter WORDWIDTH = 6)
  (input  logic [WORDWIDTH-1:0] D,
   output logic [WORDWIDTH-1:0] Q,
   input  logic clock, en, clear);
  always_ff @(posedge clock) begin
    if (en)
        Q <= D;
    else if (clear)
        Q <= 'd0;
    end
endmodule: Register

module my_chip (
    input logic [11:0] io_in, // Inputs to your chip
    output logic [11:0] io_out, // Outputs from your chip
    input logic clock,
    input logic reset // Important: Reset is ACTIVE-HIGH
);
    
    // Basic counter design as an example


    RangeFinder #(10) rf( .clock, .reset, .data_in(io_in[9:0]), .go(io_in[10]), .finish(io_in[11]), .range(io_out[9:0]), .debug_error(io_out[10]));
             

endmodule

module RangeFinder
    #(parameter WIDTH=16)
    (input logic [WIDTH-1:0] data_in,
     input logic clock, reset,
     input logic go, finish,
    output logic [WIDTH-1:0] range,
    output logic debug_error);

    logic smallest_enable, largest_enable;
    logic [WIDTH-1:0] smallest_out, largest_out;

    logic largest_init, smallest_init, is_go_initiated;

    logic clear, prefetch;

    assign prefetch = go & ~is_go_initiated & ~finish;

    Register #(WIDTH) smallest (.D(data_in), .Q(smallest_out), .clock(clock), .en(smallest_enable | prefetch), .clear(clear | ~is_go_initiated));

    Register #(WIDTH) largest (.D(data_in), .Q(largest_out), .clock(clock), .en(largest_enable | prefetch), .clear(clear | ~is_go_initiated));

    assign smallest_enable = ((data_in < smallest_out) && is_go_initiated) ? 1'b1 : 1'b0;

    assign largest_enable = ((data_in > largest_out) && is_go_initiated) ? 1'b1 : 1'b0;

    assign range = (largest_out - smallest_out);

    always_ff @(posedge clock, posedge reset) begin
        if (reset) begin
            debug_error <= 1'b0;
            clear <= 1'b1;
            is_go_initiated <= 1'b0;
        end
        else begin
            clear <= 1'b0;
            if (go & finish) begin
                debug_error <= 1'b1;
                is_go_initiated <= 1'b0;
            end
            else if (go & ~finish) begin
                debug_error <= 1'b0;
                is_go_initiated <= 1'b1;
            end
            else if (~go & finish & is_go_initiated) begin
                is_go_initiated <= 1'b0;
            end
            else if (~go & finish & ~is_go_initiated) begin
                debug_error <= 1'b1;
                is_go_initiated <= 1'b0;
            end
        end
    end

endmodule: RangeFinder
