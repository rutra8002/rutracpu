import subprocess


def run_command(command: list[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def run_simulation() -> int:
    compile_rc = run_command(["iverilog", "-o", "rutracpu_tb", "hw/rutracpu.v", "hw/rutracpu_tb.v"])
    if compile_rc != 0:
        return compile_rc

    return run_command(["vvp", ".\\rutracpu_tb"])