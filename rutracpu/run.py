import argparse
import sys
from pathlib import Path

from rutracpu.assembler import assemble
from rutracpu.compiler import compile_to_rasm
from rutracpu.gpu_viewer import show_frames
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
    parser.add_argument("--gpu-window", action="store_true", help="Open GPU frames in a desktop window after run")
    parser.add_argument("--gpu-file", default="gpu_frames.txt", help="Path to GPU frame dump file")
    parser.add_argument("--gpu-fps", type=int, default=6, help="GPU viewer playback speed")
    parser.add_argument("--gpu-pixel-size", type=int, default=24, help="GPU viewer pixel size")
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
    gpu_frame_path = resolve_input_path(args.gpu_file)

    try:
        if source_path.suffix.lower() == ".rpl":
            compile_to_rasm(source_path, asm_path)
        assemble(asm_path, mem_path)
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    sim_rc = run_simulation(mem_path, gpu_frame_path=gpu_frame_path)
    if sim_rc != 0:
        return sim_rc

    if args.gpu_window:
        try:
            return show_frames(gpu_frame_path, pixel_size=args.gpu_pixel_size, fps=args.gpu_fps)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to open GPU window: {exc}", file=sys.stderr)
            return 1

    return 0
