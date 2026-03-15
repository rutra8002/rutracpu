from rutracpu.compiler import compile_to_rasm
from rutracpu.compiler.cli import main

__all__ = ["compile_to_rasm", "main"]


if __name__ == "__main__":
    raise SystemExit(main())