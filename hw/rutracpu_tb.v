`timescale 1ns/1ps

module rutracpu_tb;
    reg clk;
    reg reset;
    reg [7:0] cycles;
    reg [1023:0] memfile;
    wire [7:0] pc;
    wire [7:0] acc;
    wire [7:0] out_data;
    wire out_valid;
    wire out_is_char;
    wire halted;

    rutracpu dut (
        .clk(clk),
        .reset(reset),
        .pc(pc),
        .acc(acc),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_is_char(out_is_char),
        .halted(halted)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        reset = 1'b1;
        cycles = 8'd0;

        memfile = "program.mem";
        if (!$value$plusargs("memfile=%s", memfile))
            memfile = "program.mem";

        $readmemb(memfile, dut.rom);

        #12;
        reset = 1'b0;

        while (!halted && cycles < 8'd100) begin
            @(posedge clk);
            cycles = cycles + 8'd1;
            if (out_valid) begin
                if (out_is_char)
                    $write("%c", out_data);
                else
                    $display("%0d", out_data);
            end
        end

        $display("");

        if (!halted)
            $display("TIMEOUT: acc=%0d pc=%0d cycles=%0d", acc, pc, cycles);
        else
            $display("HALTED: acc=%0d pc=%0d cycles=%0d", acc, pc, cycles);

        $finish;
    end
endmodule