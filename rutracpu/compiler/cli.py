import argparse
import sys
from pathlib import Path

from rutracpu.compiler.codegen import compile_to_rasm
from rutracpu.paths import workspace_root


def resolve_input_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (workspace_root() / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile rutracpu high-level source into .rasm.")
    parser.add_argument("source_file", help="Path to the .rpl source file")
    parser.add_argument("output_file", nargs="?", help="Optional output .rasm path")
    args = parser.parse_args()

    source_path = resolve_input_path(args.source_file)
    output_path = resolve_input_path(args.output_file) if args.output_file else None

    try:
        generated_path = compile_to_rasm(source_path, output_path)
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print(generated_path)
    return 0
