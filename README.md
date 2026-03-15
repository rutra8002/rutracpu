# Rutracpu 1-Bit Verilog CPU

This version is reduced to a 1-bit accumulator CPU.

- accumulator width: `1` bit
- program counter width: `2` bits
- program memory: `4` instructions
- instruction width: `2` bits


Instruction set:

- `00`: `NOPE`
- `01`: `SET` -> `acc = 1`
- `10`: `CLEAR` -> `acc = 0`
- `11`: `HALT`

Instruction behavior:

- `NOPE`: does nothing, then `pc` increases by 1.
- `SET`: writes `1` into `acc`, then `pc` increases by 1.
- `CLEAR`: writes `0` into `acc`, then `pc` increases by 1.
- `HALT`: sets `halted = 1` and stops execution. `pc` does not advance after this instruction.

Quick examples:

- If `acc` is `0` and the instruction is `NOPE`, `acc` stays `0`.
- If `acc` is `0` and the instruction is `SET`, `acc` becomes `1`.
- If `acc` is `1` and the instruction is `CLEAR`, `acc` becomes `0`.
- If the instruction is `HALT`, the CPU stops on that instruction address.

You can now run a custom `.rasm` file through the CPU.

Assembly format:

- one instruction per line
- allowed instructions: `NOPE`, `SET`, `CLEAR`, `HALT`
- blank lines are ignored
- `;` starts a comment
- maximum program size: `4` instructions

Example program in [program.rasm](program.rasm):

1. `SET`
2. `CLEAR`
3. `SET`
4. `HALT`

After execution, the accumulator should be `1`.

If Icarus Verilog is installed, run:

py .\run_rutracpu.py .\program.rasm

What happens:

1. The Python script assembles the `.rasm` file into `program.mem`.
2. The testbench loads `program.mem` into the CPU ROM with `$readmemb`.
3. The simulation runs until `HALT` or a small timeout.
4. The final CPU state is printed.