import argparse
from pathlib import Path


def load_frames(frame_file: Path) -> list[list[str]]:
    if not frame_file.exists():
        raise FileNotFoundError(f"GPU frame file not found: {frame_file}")

    lines = frame_file.read_text(encoding="utf-8-sig").splitlines()
    frames: list[list[str]] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("[GPU FRAME"):
            frame_rows: list[str] = []
            i += 1
            while i < len(lines) and len(frame_rows) < 16:
                row = lines[i].rstrip("\r\n")
                if row:
                    frame_rows.append(row)
                i += 1

            if len(frame_rows) == 16:
                frames.append(frame_rows)
            continue

        i += 1

    return frames


def show_frames(frame_file: Path, pixel_size: int = 24, fps: int = 6) -> int:
    import tkinter as tk

    frames = load_frames(frame_file)
    if not frames:
        print(f"No GPU frames found in {frame_file}")
        return 1

    width = 16 * pixel_size
    height = 16 * pixel_size

    root = tk.Tk()
    root.title(f"RutraGPU Viewer - {frame_file.name}")
    canvas = tk.Canvas(root, width=width, height=height, bg="black", highlightthickness=0)
    canvas.pack()

    rects = []
    for y in range(16):
        for x in range(16):
            x0 = x * pixel_size
            y0 = y * pixel_size
            x1 = x0 + pixel_size
            y1 = y0 + pixel_size
            rect = canvas.create_rectangle(x0, y0, x1, y1, fill="#111111", outline="#222222")
            rects.append(rect)

    state = {"index": 0}
    frame_delay_ms = max(1, int(1000 / max(1, fps)))

    def draw_frame(frame_rows: list[str]) -> None:
        idx = 0
        for row in frame_rows:
            row_text = row[:16].ljust(16, ".")
            for ch in row_text:
                color = "#7CFF6B" if ch == "#" else "#111111"
                canvas.itemconfig(rects[idx], fill=color)
                idx += 1

    def tick() -> None:
        frame = frames[state["index"]]
        draw_frame(frame)
        state["index"] = (state["index"] + 1) % len(frames)
        root.after(frame_delay_ms, tick)

    tick()
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Display rutracpu GPU frames in a desktop window.")
    parser.add_argument("frame_file", nargs="?", default="gpu_frames.txt", help="Path to GPU frame dump file")
    parser.add_argument("--pixel-size", type=int, default=24, help="Pixel size for each GPU pixel")
    parser.add_argument("--fps", type=int, default=6, help="Playback frames per second")
    parser.add_argument("--info", action="store_true", help="Print frame count and exit")
    args = parser.parse_args()

    frame_file = Path(args.frame_file)
    frames = load_frames(frame_file)
    if args.info:
        print(f"frames={len(frames)} file={frame_file}")
        return 0

    if not frames:
        print(f"No GPU frames found in {frame_file}")
        return 1

    return show_frames(frame_file, pixel_size=args.pixel_size, fps=args.fps)


if __name__ == "__main__":
    raise SystemExit(main())
