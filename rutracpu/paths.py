from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent
