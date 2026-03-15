from pathlib import Path


INSTRUCTION_SET = {
    "PASS": ("0000", "none"),
    "LOAD_IMMEDIATE": ("0001", "imm8"),
    "ADD_IMMEDIATE": ("0010", "imm8"),
    "SUBTRACT_IMMEDIATE": ("0011", "imm8"),
    "LOAD": ("0100", "mem4"),
    "STORE": ("0101", "mem4"),
    "JUMP": ("0110", "pc8"),
    "JUMP_IF_ZERO": ("0111", "pc8"),
    "OUTPUT_INT": ("1000", "none"),
    "OUTPUT_CHAR": ("1001", "none"),
    "HALT": ("1111", "none"),
}


def strip_comment(raw_line: str) -> str:
    in_string = False
    escaped = False
    result = []

    for ch in raw_line:
        if escaped:
            result.append(ch)
            escaped = False
            continue

        if ch == "\\":
            result.append(ch)
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue

        if ch == ";" and not in_string:
            break

        result.append(ch)

    return "".join(result)


def parse_int(raw_value: str, minimum: int, maximum: int, label: str) -> int:
    try:
        value = int(raw_value, 0)
    except ValueError as exc:
        raise ValueError(f"Invalid {label} '{raw_value}'.") from exc

    if value < minimum or value > maximum:
        raise ValueError(f"{label.capitalize()} out of range: {value}. Valid range is {minimum}..{maximum}.")

    return value


def encode_instruction(mnemonic: str, raw_operand: str | None) -> str:
    if mnemonic not in INSTRUCTION_SET:
        allowed = ", ".join(INSTRUCTION_SET)
        raise ValueError(f"Unknown instruction '{mnemonic}'. Allowed: {allowed}")

    opcode_bits, operand_type = INSTRUCTION_SET[mnemonic]

    if operand_type == "none":
        if raw_operand is not None:
            raise ValueError(f"Instruction '{mnemonic}' does not take an operand.")
        operand_bits = "00000000"
    elif operand_type == "imm8":
        if raw_operand is None:
            raise ValueError(f"Instruction '{mnemonic}' requires one operand (0..255).")
        imm_value = parse_int(raw_operand, 0, 255, "immediate")
        operand_bits = f"{imm_value:08b}"
    elif operand_type == "mem4":
        if raw_operand is None:
            raise ValueError(f"Instruction '{mnemonic}' requires one operand (0..15).")
        addr_value = parse_int(raw_operand, 0, 15, "address")
        operand_bits = "0000" + f"{addr_value:04b}"
    elif operand_type == "pc8":
        if raw_operand is None:
            raise ValueError(f"Instruction '{mnemonic}' requires one operand (0..255).")
        pc_value = parse_int(raw_operand, 0, 255, "address")
        operand_bits = f"{pc_value:08b}"
    else:
        raise ValueError(f"Unsupported operand type for instruction '{mnemonic}'.")

    return opcode_bits + operand_bits


def parse_string_literal(raw_value: str) -> str:
    if len(raw_value) < 2 or raw_value[0] != '"' or raw_value[-1] != '"':
        raise ValueError("PRINT_STRING requires a quoted string, for example: PRINT_STRING \"HELLO\".")

    inner = raw_value[1:-1]
    return bytes(inner, "ascii").decode("unicode_escape")


def assemble(asm_path: Path, mem_path: Path) -> None:
    if not asm_path.exists():
        raise FileNotFoundError(f"ASM file not found: {asm_path}")

    instructions = []
    for raw_line in asm_path.read_text(encoding="ascii").splitlines():
        clean_line = strip_comment(raw_line).strip()
        if not clean_line:
            continue

        upper_line = clean_line.upper()

        if upper_line.startswith("PRINT_STRING"):
            literal_start = clean_line.find('"')
            if literal_start == -1:
                raise ValueError("PRINT_STRING requires a quoted string literal.")
            literal = clean_line[literal_start:].strip()
            text = parse_string_literal(literal)

            for ch in text:
                instructions.append(encode_instruction("LOAD_IMMEDIATE", str(ord(ch))))
                instructions.append(encode_instruction("OUTPUT_CHAR", None))
            continue

        if upper_line.startswith("PRINT_INT"):
            parts = clean_line.split()
            if len(parts) != 2:
                raise ValueError("PRINT_INT requires one integer operand (0..255).")
            value = parse_int(parts[1], 0, 255, "integer")
            instructions.append(encode_instruction("LOAD_IMMEDIATE", str(value)))
            instructions.append(encode_instruction("OUTPUT_INT", None))
            continue

        parts = clean_line.split()
        mnemonic = parts[0].upper()
        raw_operand = parts[1] if len(parts) == 2 else None

        if len(parts) > 2:
            raise ValueError(f"Too many tokens in line: '{clean_line}'")

        instructions.append(encode_instruction(mnemonic, raw_operand))

    if len(instructions) > 256:
        raise ValueError(
            f"Program too long: {len(instructions)} instructions. rutracpu ROM holds 256 instructions."
        )

    instructions.extend(["000000000000"] * (256 - len(instructions)))
    mem_path.write_text("\n".join(instructions) + "\n", encoding="ascii")