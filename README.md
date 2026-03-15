# Rutracpu 8-Bit Verilog CPU

- accumulator width: `8` bits
- program counter width: `8` bits
- program memory: `256` instructions
- instruction width: `12` bits (`opcode[11:8] + operand[7:0]`)
- data memory: `16` bytes of RAM

Instruction set:

- `0000 xxxxxxxx`: `PASS`
- `0001 iiiiiiii`: `LOAD_IMMEDIATE i`
- `0010 iiiiiiii`: `ADD_IMMEDIATE i`
- `0011 iiiiiiii`: `SUBTRACT_IMMEDIATE i`
- `0100 0000aaaa`: `LOAD a`
- `0101 0000aaaa`: `STORE a`
- `0110 aaaaaaaa`: `JUMP a`
- `0111 aaaaaaaa`: `JUMP_IF_ZERO a`
- `1000 xxxxxxxx`: `OUTPUT_INT`
- `1001 xxxxxxxx`: `OUTPUT_CHAR`
- `1111 xxxxxxxx`: `HALT`

Instruction behavior:

- `PASS`: no register or memory change; `pc = pc + 1`.
- `LOAD_IMMEDIATE i`: writes immediate value `i` into accumulator (`acc = i`); `pc = pc + 1`.
- `ADD_IMMEDIATE i`: adds immediate value to accumulator (`acc = acc + i` with 8-bit wraparound); `pc = pc + 1`.
- `SUBTRACT_IMMEDIATE i`: subtracts immediate value from accumulator (`acc = acc - i` with 8-bit wraparound); `pc = pc + 1`.
- `LOAD a`: reads RAM at address `a` into accumulator (`acc = ram[a]`); `pc = pc + 1`.
- `STORE a`: writes accumulator into RAM at address `a` (`ram[a] = acc`); `pc = pc + 1`.
- `JUMP a`: unconditional branch to address `a` (`pc = a`).
- `JUMP_IF_ZERO a`: if `acc == 0`, branches to `a`; otherwise continues (`pc = pc + 1`).
- `OUTPUT_INT`: emits accumulator as an integer line in the testbench output; `pc = pc + 1`.
- `OUTPUT_CHAR`: emits accumulator as an ASCII character in the testbench output; `pc = pc + 1`.
- `HALT`: sets halted state and stops instruction execution until reset.

Assembly format:

- one instruction per line
- mnemonics are case-insensitive
- full readable mnemonics are supported (for example: `JUMP`)
- blank lines are ignored
- `;` starts a comment
- programs can contain up to `256` instructions
- immediate operands for `LOAD_IMMEDIATE`, `ADD_IMMEDIATE`, `SUBTRACT_IMMEDIATE`: `0..255`
- address operands for `LOAD`, `STORE`: `0..15`
- address operands for `JUMP`, `JUMP_IF_ZERO`: `0..255`

Typed print pseudo-instructions:

- `PRINT_INT n`: expands to `LOAD_IMMEDIATE n` + `OUTPUT_INT`
- `PRINT_STRING "text"`: expands to repeated `LOAD_IMMEDIATE ASCII` + `OUTPUT_CHAR`
- these pseudo-instructions are assembled by Python and let you print numbers or words directly

Example program in [programs/program.rasm](programs/program.rasm):

This program counts from `1` to `10` and prints each number.

If Icarus Verilog is installed, run:

py .\run_rutracpu.py .\programs\program.rasm

What happens:

1. The Python script assembles the `.rasm` file into a matching `.mem` file with the same base name.
2. The testbench loads that generated `.mem` file into the CPU ROM with `$readmemb`.
3. `OUTPUT_INT` prints decimal lines and `OUTPUT_CHAR` prints ASCII text.
4. The simulation runs until `HALT` or timeout at 100 cycles.
5. The final CPU state is printed.