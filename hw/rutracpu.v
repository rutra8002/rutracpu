module rutracpu (
    input wire clk,
    input wire reset,
    input wire [11:0] instruction,
    output reg [7:0] pc,
    output reg [7:0] acc,
    output reg [7:0] out_data,
    output reg out_valid,
    output reg out_is_char,
    output reg halted
);
    reg [7:0] ram [0:15];

    wire [3:0] opcode = instruction[11:8];
    wire [7:0] operand_imm = instruction[7:0];
    wire [3:0] operand_addr = instruction[3:0];

    initial begin
        pc = 8'd0;
        acc = 8'd0;
        out_data = 8'd0;
        out_valid = 1'b0;
        out_is_char = 1'b0;
        halted = 1'b0;
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pc <= 8'd0;
            acc <= 8'd0;
            out_data <= 8'd0;
            out_valid <= 1'b0;
            out_is_char <= 1'b0;
            halted <= 1'b0;
        end else if (!halted) begin
            out_valid <= 1'b0;
            case (opcode)
                4'h0: pc <= pc + 8'd1;                     // PASS
                4'h1: begin                                // LOAD_IMMEDIATE imm8
                    acc <= operand_imm;
                    pc <= pc + 8'd1;
                end
                4'h2: begin                                // ADD_IMMEDIATE imm8
                    acc <= acc + operand_imm;
                    pc <= pc + 8'd1;
                end
                4'h3: begin                                // SUBTRACT_IMMEDIATE imm8
                    acc <= acc - operand_imm;
                    pc <= pc + 8'd1;
                end
                4'h4: begin                                // LOAD address
                    acc <= ram[operand_addr];
                    pc <= pc + 8'd1;
                end
                4'h5: begin                                // STORE address
                    ram[operand_addr] <= acc;
                    pc <= pc + 8'd1;
                end
                4'h6: pc <= operand_imm;                   // JUMP address
                4'h7: begin                                // JUMP_IF_ZERO address
                    if (acc == 8'd0)
                        pc <= operand_imm;
                    else
                        pc <= pc + 8'd1;
                end
                4'h8: begin                                // OUTPUT_INT
                    out_data <= acc;
                    out_is_char <= 1'b0;
                    out_valid <= 1'b1;
                    pc <= pc + 8'd1;
                end
                4'h9: begin                                // OUTPUT_CHAR
                    out_data <= acc;
                    out_is_char <= 1'b1;
                    out_valid <= 1'b1;
                    pc <= pc + 8'd1;
                end
                4'hF: halted <= 1'b1;                      // HALT
                default: pc <= pc + 8'd1;
            endcase
        end
    end
endmodule

module rutracpu_rom (
    input wire [7:0] address,
    output wire [11:0] instruction
);
    reg [11:0] rom [0:255];

    assign instruction = rom[address];
endmodule