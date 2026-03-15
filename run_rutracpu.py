import argparse
import sys
from pathlib import Path

from assembler import assemble
from simulator import run_simulation

def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble and run rutracpu programs.")
    parser.add_argument("rasm_file", nargs="?", default="programs/program.rasm", help="Path to the .rasm file")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent
    asm_path = (workspace / args.rasm_file).resolve() if not Path(args.rasm_file).is_absolute() else Path(args.rasm_file)
    mem_path = workspace / "program.mem"

    try:
        assemble(asm_path, mem_path)
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    return run_simulation()


if __name__ == "__main__":
    raise SystemExit(main())