"""Run the detector on CC-licensed durian tree photos and build one shareable gallery image.

Usage: python -m scripts.photo_gallery
Needs commons/ from scripts.fetch_commons. Writes out/gallery.jpg (1920x1080) and out/gallery_credits.txt.
"""
import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

from durian import render
from durian.detector import Detector

W, H = 1920, 1080
COLS, ROWS = 3, 2
MARGIN, GAP, TOP, BOTTOM = 48, 20, 150, 70
THRESHOLD = 0.3
PICKS = ["File:Durian in tree.jpg", "File:Durians on a tree.jpg", "File:Durian Tree.jpg",
         "File:Tender fruit's Durian tree.JPG", "File:Ripe Durian Tree in Samosir Island 05.JPG",
         "File:Durio zibeth 071230-2985 sntn.jpg"]


def cover(img: Image.Image, w: int, h: int) -> tuple[Image.Image, float, int, int]:
    """Scale to fill w x h, centre-crop. Returns image, scale, crop offsets."""
    s = max(w / img.width, h / img.height)
    big = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    ox, oy = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((ox, oy, ox + w, oy + h)), s, ox, oy


def main() -> None:
    photos = {p["title"]: p for p in json.loads(Path("commons/selected.json").read_text(encoding="utf-8"))}
    det = Detector(THRESHOLD)

    canvas = Image.new("RGB", (W, H), render.PAPER)
    d = ImageDraw.Draw(canvas)
    d.text((MARGIN, 40), "Finding durians on the tree", fill=render.INK, font=render.font(46, bold=True))
    d.text((MARGIN, 100), "Open-vocabulary detector, no durian-specific training · 6 trees, different light and distance",
           fill=render.MUTED, font=render.font(24))

    tw = (W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    th = (H - TOP - BOTTOM - (ROWS - 1) * GAP) // ROWS
    credits, total = [], 0
    for n, title in enumerate(PICKS[: COLS * ROWS]):
        p = photos[title]
        bgr = cv2.imread(p["file"])
        dets = det(bgr)
        img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        tile, s, ox, oy = cover(img, tw, th)
        shifted = [([b[0] * s - ox, b[1] * s - oy, b[2] * s - ox, b[3] * s - oy], sc) for b, sc in dets]
        visible = [(b, sc) for b, sc in shifted if b[2] > 0 and b[3] > 0 and b[0] < tw and b[1] < th]
        total += len(visible)
        tile = render.annotate(tile, visible)
        td = ImageDraw.Draw(tile, "RGBA")
        render.pill(td, (14, 14), f"{len(visible)} found", size=22)
        x = MARGIN + (n % COLS) * (tw + GAP)
        y = TOP + (n // COLS) * (th + GAP)
        mask = Image.new("L", tile.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=14, fill=255)
        canvas.paste(tile, (x, y), mask)
        credits.append(f"{n + 1}. {p['title'][5:]} by {p['artist'] or 'unknown'} ({p['license']}) {p['page']}")

    d.text((MARGIN, H - BOTTOM + 22),
           "Photos: Wikimedia Commons, CC licences (full credits in gallery_credits.txt) · boxes drawn by the model, threshold 0.3",
           fill=render.MUTED, font=render.font(18))
    out = Path("out")
    canvas.save(out / "gallery.jpg", quality=92)
    (out / "gallery_credits.txt").write_text("\n".join(credits) + "\n", encoding="utf-8")
    print(f"out/gallery.jpg, {total} boxes")


if __name__ == "__main__":
    main()
