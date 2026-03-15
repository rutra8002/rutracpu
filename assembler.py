from pathlib import Path


INSTRUCTION_MAP = {
    "NOPE": "00",
    "SET": "01",
    "CLEAR": "10",
    "HALT": "11",
}


def assemble(asm_path: Path, mem_path: Path) -> None:
    if not asm_path.exists():
        raise FileNotFoundError(f"ASM file not found: {asm_path}")

    instructions = []
    for raw_line in asm_path.read_text(encoding="ascii").splitlines():
        clean_line = raw_line.split(";", 1)[0].strip().upper()
        if not clean_line:
            continue

        if clean_line not in INSTRUCTION_MAP:
            allowed = ", ".join(INSTRUCTION_MAP)
            raise ValueError(f"Unknown instruction '{clean_line}'. Allowed: {allowed}")

        instructions.append(INSTRUCTION_MAP[clean_line])

    if len(instructions) > 4:
        raise ValueError(
            f"Program too long: {len(instructions)} instructions. rutracpu ROM holds 4 instructions."
        )

    instructions.extend(["00"] * (4 - len(instructions)))
    mem_path.write_text("\n".join(instructions) + "\n", encoding="ascii")