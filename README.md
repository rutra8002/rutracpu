# Rutracpu 8-Bit Verilog CPU

- accumulator width: `8` bits
- program counter width: `8` bits
- program memory: `256` instructions
- instruction width: `12` bits (`opcode[11:8] + operand[7:0]`)
- data memory: `16` bytes of RAM
- instruction ROM is external to the CPU core

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

High-level language:

- `.rpl` source files compile into plain `.rasm`
- comments start with `#`
- variables live in the CPU's `16` RAM bytes, so a program can use at most `16` named variables total
- variables must be declared with `let` before you assign or read them
- `for` loop variables are created by the loop header itself
- variables store one byte; use `int` for numeric output and `char` for character output
- strings must be ASCII because `PRINT_STRING` lowers to ASCII character output
- string and char literals support escapes like `\n`, `\t`, `\\`, and `\"`

Supported `.rpl` statements:

- `let int x = 5`
- `let char ch = "a"`
- `let x = 5` defaults to `int`
- `x = x + 1`
- `x = x - 1`
- `print x`
- `print 42`
- `print "HELLO"`
- `print "HELLO\n"`
- `for i from 1 to 10 {` followed by statements and a closing `}`

Loop behavior:

- `for` ranges are inclusive, so `for i from 1 to 3` runs with `i = 1`, `2`, `3`
- descending ranges are currently rejected
- assigning to the active loop variable inside its own loop body is rejected to keep generated control flow correct
- `print` uses the declared variable type: `int` prints numbers, `char` prints ASCII characters
- `print "\n"` prints a newline

Example `.rpl` program:

```text
# Count from 1 to 10 and print each number.
let char ch = "a"
for i from 1 to 3 {
	print i
	print ch
	ch = ch - 1
}
```

Compile high-level code into `.rasm`:

```text
py .\compiler.py .\programs\count_for.rpl
```

This writes `.\programs\count_for.rasm`.

Typed print pseudo-instructions:

- `PRINT_INT n`: expands to `LOAD_IMMEDIATE n` + `OUTPUT_INT`
- `PRINT_STRING "text"`: expands to repeated `LOAD_IMMEDIATE ASCII` + `OUTPUT_CHAR`
- these pseudo-instructions are assembled by Python and let you print numbers or words directly

Example program in [programs/program.rasm](programs/program.rasm):

This program counts from `1` to `10` and prints each number.

If Icarus Verilog is installed, run:

py .\run_rutracpu.py .\programs\program.rasm

You can also run a high-level source file directly:

py .\run_rutracpu.py .\programs\count_for.rpl

What happens:

1. If the input is `.rpl`, the Python compiler first emits a matching `.rasm` file with the same base name.
2. The assembler turns the `.rasm` file into a matching `.mem` file with the same base name.
3. The testbench loads that generated `.mem` file into a separate ROM module with `$readmemb`.
4. `OUTPUT_INT` prints decimal lines and `OUTPUT_CHAR` prints ASCII text.
5. The simulation runs until `HALT` or timeout at 255 cycles.
6. The final CPU state is printed.

Synthesis note:

- The CPU core now takes `instruction` as an input instead of owning ROM internally.
- This keeps synthesis results representative of the programmable CPU instead of specializing the logic for one baked-in program.

Python toolchain layout:

- the main Python implementation now lives under `rutracpu/`
- `rutracpu/compiler/ast.py` defines the high-level language AST
- `rutracpu/compiler/parser.py` parses `.rpl` source
- `rutracpu/compiler/codegen.py` lowers the AST into `.rasm`
- root-level `compiler.py`, `assembler.py`, `simulator.py`, and `run_rutracpu.py` remain as thin compatibility entry points