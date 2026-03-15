`timescale 1ns/1ps

module rutracpu_tb;
    reg clk;
    reg reset;
    reg [7:0] cycles;
    reg [1023:0] memfile;
    reg [1023:0] gpufile;
    wire [7:0] pc;
    wire [11:0] instruction;
    wire [7:0] acc;
    wire [7:0] out_data;
    wire out_valid;
    wire out_is_char;
    wire halted;
    wire gpu_consumed;
    wire gpu_present;
    integer gx;
    integer gy;
    integer gpu_fd;
    integer gpu_frame_index;

    rutracpu_rom rom (
        .address(pc),
        .instruction(instruction)
    );

    rutracpu dut (
        .clk(clk),
        .reset(reset),
        .instruction(instruction),
        .pc(pc),
        .acc(acc),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_is_char(out_is_char),
        .halted(halted)
    );

    rutragpu gpu (
        .clk(clk),
        .reset(reset),
        .in_valid(out_valid),
        .in_is_char(out_is_char),
        .in_data(out_data),
        .consumed(gpu_consumed),
        .present_pulse(gpu_present)
    );

    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (gpu_present) begin
            if (gpu_fd != 0) begin
                $fwrite(gpu_fd, "[GPU FRAME %0d]\n", gpu_frame_index);
                gpu_frame_index = gpu_frame_index + 1;
            end
            for (gy = 0; gy < 16; gy = gy + 1) begin
                for (gx = 0; gx < 16; gx = gx + 1) begin
                    if (gpu.framebuffer[(gy * 16) + gx]) begin
                        if (gpu_fd != 0)
                            $fwrite(gpu_fd, "#");
                    end else begin
                        if (gpu_fd != 0)
                            $fwrite(gpu_fd, ".");
                    end
                end
                if (gpu_fd != 0)
                    $fwrite(gpu_fd, "\n");
            end
            if (gpu_fd != 0)
                $fwrite(gpu_fd, "\n");
        end
    end

    initial begin
        clk = 1'b0;
        reset = 1'b1;
        cycles = 8'd0;
        gpu_frame_index = 0;

        memfile = "program.mem";
        if (!$value$plusargs("memfile=%s", memfile))
            memfile = "program.mem";

        gpufile = "gpu_frames.txt";
        if (!$value$plusargs("gpufile=%s", gpufile))
            gpufile = "gpu_frames.txt";

        gpu_fd = $fopen(gpufile, "w");
        if (gpu_fd == 0)
            $display("WARNING: could not open GPU output file '%0s'. GPU frames will be discarded.", gpufile);

        $readmemb(memfile, rom.rom);

        #12;
        reset = 1'b0;

        while (!halted && cycles < 8'd255) begin
            @(posedge clk);
            cycles = cycles + 8'd1;
            if (out_valid) begin
                if (out_is_char && gpu_consumed)
                    ;
                else if (out_is_char)
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

        if (gpu_fd != 0)
            $fclose(gpu_fd);

        $finish;
    end
endmodule