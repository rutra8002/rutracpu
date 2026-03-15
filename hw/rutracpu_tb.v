`timescale 1ns/1ps

module rutracpu_tb;
    reg clk;
    reg reset;
    reg [7:0] cycles;
    wire [1:0] pc;
    wire acc;
    wire halted;

    rutracpu dut (
        .clk(clk),
        .reset(reset),
        .pc(pc),
        .acc(acc),
        .halted(halted)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        reset = 1'b1;
        cycles = 8'd0;

        $readmemb("program.mem", dut.rom);

        #12;
        reset = 1'b0;

        while (!halted) begin
            @(posedge clk);
            cycles = cycles + 8'd1;
        end

        $display("HALTED: acc=%0d pc=%0d cycles=%0d", acc, pc, cycles);

        $finish;
    end
endmodule