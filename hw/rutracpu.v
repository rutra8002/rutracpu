module rutracpu (
    input wire clk,
    input wire reset,
    output reg [1:0] pc,
    output reg acc,
    output reg halted
);
    reg [1:0] rom [0:3];

    initial begin
        pc = 2'd0;
        acc = 1'b0;
        halted = 1'b0;
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pc <= 2'd0;
            acc <= 1'b0;
            halted <= 1'b0;
        end else if (!halted) begin
            case (rom[pc])
                2'b00: pc <= pc + 2'd1;
                2'b01: begin
                    acc <= 1'b1;
                    pc <= pc + 2'd1;
                end
                2'b10: begin
                    acc <= 1'b0;
                    pc <= pc + 2'd1;
                end
                2'b11: halted <= 1'b1;
            endcase
        end
    end
endmodule