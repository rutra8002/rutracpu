import subprocess
from pathlib import Path


def run_command(command: list[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def run_simulation(mem_path: Path, gpu_frame_path: Path | None = None) -> int:
    compile_rc = run_command(["iverilog", "-o", "rutracpu_tb", "hw/rutracpu.v", "hw/rutragpu.v", "hw/rutracpu_tb.v"])
    if compile_rc != 0:
        return compile_rc

    command = ["vvp", ".\\rutracpu_tb", f"+memfile={mem_path.as_posix()}"]
    if gpu_frame_path is not None:
        command.append(f"+gpufile={gpu_frame_path.as_posix()}")
    return run_command(command)
