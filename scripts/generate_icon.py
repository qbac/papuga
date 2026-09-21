"""Generuje ikonę aplikacji (icon.ico dla Windows, icon.png dla Linux/tray)."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "papuga" / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def draw_papuga(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = size * 0.06
    d.ellipse((margin, margin, size - margin, size - margin), fill=(46, 125, 50, 255))
    # fale dźwiękowe
    bbox1 = (size * 0.28, size * 0.22, size * 0.72, size * 0.78)
    bbox2 = (size * 0.16, size * 0.12, size * 0.84, size * 0.88)
    width = max(2, int(size * 0.055))
    d.arc(bbox1, start=300, end=60, fill="white", width=width)
    d.arc(bbox2, start=300, end=60, fill="white", width=width)
    r = size * 0.09
    cx, cy = size / 2, size / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white")
    return img


def main() -> None:
    base = draw_papuga(256)
    base.save(OUT_DIR / "icon.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [draw_papuga(s) for s in sizes]
    imgs[0].save(OUT_DIR / "icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Zapisano ikony w {OUT_DIR}")


if __name__ == "__main__":
    main()
