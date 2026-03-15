module rutragpu (
    input wire clk,
    input wire reset,
    input wire in_valid,
    input wire in_is_char,
    input wire [7:0] in_data,
    output wire consumed,
    output reg present_pulse
);
    localparam [7:0] CMD_SET_X = 8'hF0;
    localparam [7:0] CMD_SET_Y = 8'hF1;
    localparam [7:0] CMD_PLOT = 8'hF2;
    localparam [7:0] CMD_CLEAR = 8'hF3;
    localparam [7:0] CMD_PRESENT = 8'hF4;

    localparam [1:0] WAIT_COMMAND = 2'd0;
    localparam [1:0] WAIT_X = 2'd1;
    localparam [1:0] WAIT_Y = 2'd2;
    localparam [1:0] WAIT_PLOT = 2'd3;

    reg [1:0] state;
    reg [3:0] cursor_x;
    reg [3:0] cursor_y;
    reg framebuffer [0:255];
    wire is_command;

    assign is_command = (in_data == CMD_SET_X) ||
                        (in_data == CMD_SET_Y) ||
                        (in_data == CMD_PLOT) ||
                        (in_data == CMD_CLEAR) ||
                        (in_data == CMD_PRESENT);

    assign consumed = in_valid && in_is_char && (
        ((state == WAIT_COMMAND) && is_command) ||
        (state == WAIT_X) ||
        (state == WAIT_Y) ||
        (state == WAIT_PLOT)
    );

    integer i;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= WAIT_COMMAND;
            cursor_x <= 4'd0;
            cursor_y <= 4'd0;
            present_pulse <= 1'b0;
            for (i = 0; i < 256; i = i + 1)
                framebuffer[i] <= 1'b0;
        end else begin
            present_pulse <= 1'b0;

            if (in_valid && in_is_char) begin
                case (state)
                    WAIT_COMMAND: begin
                        case (in_data)
                            CMD_SET_X: begin
                                state <= WAIT_X;
                            end
                            CMD_SET_Y: begin
                                state <= WAIT_Y;
                            end
                            CMD_PLOT: begin
                                state <= WAIT_PLOT;
                            end
                            CMD_CLEAR: begin
                                for (i = 0; i < 256; i = i + 1)
                                    framebuffer[i] <= 1'b0;
                            end
                            CMD_PRESENT: begin
                                present_pulse <= 1'b1;
                            end
                            default: begin
                                // Not a GPU command; let normal output path handle it.
                            end
                        endcase
                    end

                    WAIT_X: begin
                        cursor_x <= in_data[3:0];
                        state <= WAIT_COMMAND;
                    end

                    WAIT_Y: begin
                        cursor_y <= in_data[3:0];
                        state <= WAIT_COMMAND;
                    end

                    WAIT_PLOT: begin
                        framebuffer[{cursor_y, cursor_x}] <= (in_data != 8'd0);
                        state <= WAIT_COMMAND;
                    end
                endcase
            end
        end
    end
endmodule
