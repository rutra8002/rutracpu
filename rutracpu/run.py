import argparse
import sys
from pathlib import Path

from rutracpu.assembler import assemble
from rutracpu.compiler import compile_to_rasm
from rutracpu.paths import workspace_root
from rutracpu.simulator import run_simulation


def resolve_input_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (workspace_root() / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile, assemble, and run rutracpu programs.")
    parser.add_argument(
        "source_file",
        nargs="?",
        default="programs/program.rasm",
        help="Path to the .rasm or .rpl file",
    )
    args = parser.parse_args()

    source_path = resolve_input_path(args.source_file)

    if source_path.suffix.lower() == ".rpl":
        asm_path = source_path.with_suffix(".rasm")
    elif source_path.suffix.lower() == ".rasm":
        asm_path = source_path
    else:
        print(f"Unsupported input file type: {source_path.suffix}", file=sys.stderr)
        return 1

    mem_path = asm_path.with_suffix(".mem")

    try:
        if source_path.suffix.lower() == ".rpl":
            compile_to_rasm(source_path, asm_path)
        assemble(asm_path, mem_path)
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    return run_simulation(mem_path)
