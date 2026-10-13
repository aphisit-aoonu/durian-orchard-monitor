"""Short shareable clip (about 45 s): detection on CC photos, how it works, the simulation, what it is built with.

Usage: python -m scripts.post_video   -> out/post_video.mp4
Uses only CC-licensed photos (credited on screen) and the simulation; no third-party video.
"""
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from durian import render
from durian.detector import Detector
from scripts.photo_gallery import PICKS, THRESHOLD, cover

W, H, FPS = 1920, 1080, 30
PHOTO_SECONDS = 3.2
# the far-away tree is left out: boxes there are too small to check by eye
SIM_FROM, SIM_TO = 6.0, 19.0
DARK = (14, 18, 22)


def text_center(d, y, text, size, fill, bold=False):
    f = render.font(size, bold)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, fill=fill, font=f)


def card(lines: list[tuple[str, int, tuple, bool]], badge: str | None = None) -> Image.Image:
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img, "RGBA")
    total = sum(size * 1.6 for _, size, _, _ in lines)
    y = (H - total) / 2
    if badge:
        f = render.font(22, True)
        bw = d.textlength(badge, font=f) + 28
        render.pill(d, ((W - bw) / 2, y - 70), badge, size=22, bg=(255, 196, 0, 255), fg=render.INK, pad=14)
    for text, size, fill, bold in lines:
        text_center(d, y, text, size, fill, bold)
        y += size * 1.6
    return img


def photo_frames(photo, dets, writer) -> None:
    bgr = cv2.imread(photo["file"])
    img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    n = int(PHOTO_SECONDS * FPS)
    for f in range(n):
        zoom = 1.0 + 0.06 * f / n                      # slow push-in
        tile, s, ox, oy = cover(img, round(W * zoom), round(H * zoom))
        cx, cy = (tile.width - W) // 2, (tile.height - H) // 2
        frame = tile.crop((cx, cy, cx + W, cy + H))
        boxes = [([b[0] * s - ox - cx, b[1] * s - oy - cy, b[2] * s - ox - cx, b[3] * s - oy - cy], sc) for b, sc in dets]
        boxes = [x for x in boxes if x[0][2] > 0 and x[0][3] > 0 and x[0][0] < W and x[0][1] < H]
        shown = boxes[: int(len(boxes) * min(1.0, f / (n * 0.5))) + (1 if f > 2 else 0)]
        frame = render.annotate(frame, shown, scale=1.0)
        d = ImageDraw.Draw(frame, "RGBA")
        render.pill(d, (40, 40), f"{len(shown)} found", size=30, bg=(0, 0, 0, 170))
        credit = f"Photo: {photo['artist'][:40] or 'unknown'} · {photo['license']} · Wikimedia Commons"
        render.pill(d, (40, H - 70), credit, size=16, bg=(0, 0, 0, 150), pad=8)
        writer(frame)


def pipeline_card() -> Image.Image:
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img, "RGBA")
    text_center(d, 150, "How it works", 52, (255, 255, 255), True)
    steps = ["Video frame", "Open-vocabulary detector\n(OWLv2, no training)", "Remove duplicate boxes",
             "Camera-motion compensation\n(ORB + RANSAC)", "One id per fruit"]
    bw, bh, gap = 300, 150, 40
    x = (W - (len(steps) * bw + (len(steps) - 1) * gap)) / 2
    y = 360
    for k, s in enumerate(steps):
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=18, fill=(32, 38, 46), outline=(255, 196, 0), width=2)
        lines = s.split("\n")
        ty = y + bh / 2 - len(lines) * 18
        for line in lines:
            f = render.font(24 if line == lines[0] else 18, line == lines[0])
            d.text((x + (bw - d.textlength(line, font=f)) / 2, ty), line, fill=(255, 255, 255), font=f)
            ty += 36
        if k < len(steps) - 1:
            ax = x + bw + 6
            d.line([(ax, y + bh / 2), (ax + gap - 12, y + bh / 2)], fill=(255, 196, 0), width=4)
            d.polygon([(ax + gap - 12, y + bh / 2 - 9), (ax + gap - 2, y + bh / 2), (ax + gap - 12, y + bh / 2 + 9)],
                      fill=(255, 196, 0))
        x += bw + gap
    text_center(d, 640, "Honest numbers: about 2.7 s per frame on a GTX 1650, so it runs on recorded video for now.",
                26, (200, 205, 210))
    text_center(d, 690, "Next: a small durian-only model, fast enough for a live camera on a rail cart.", 26,
                (200, 205, 210))
    return img


def main() -> None:
    out = Path("out") / "post_video.mp4"
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    write = lambda im: ff.stdin.write(np.asarray(im.convert("RGB")).tobytes())
    hold = lambda im, sec: [write(im) for _ in range(int(sec * FPS))]

    hold(card([("Finding durians on the tree", 72, (255, 255, 255), True),
               ("A side project in computer vision for orchards", 32, (200, 205, 210), False)], badge="EARLY DEMO"), 3)

    photos = {p["title"]: p for p in json.loads(Path("commons/selected.json").read_text(encoding="utf-8"))}
    det = Detector(THRESHOLD)
    for title in PICKS[:5]:
        p = photos[title]
        photo_frames(p, det(cv2.imread(p["file"])), write)

    hold(pipeline_card(), 6)

    hold(card([("Then: how would one machine harvest a whole orchard?", 48, (255, 255, 255), True),
               ("Simulated round: rail cart, pole cutter, catch net, collection point", 28, (200, 205, 210), False)],
              badge="SIMULATION"), 3)
    cap = cv2.VideoCapture("out/sim_round_en.mp4")
    sim_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(SIM_FROM * sim_fps))
    for _ in range(int((SIM_TO - SIM_FROM) * sim_fps)):
        ok, frame = cap.read()
        if not ok:
            break
        write(Image.fromarray(cv2.cvtColor(cv2.resize(frame, (W, H)), cv2.COLOR_BGR2RGB)))

    hold(card([("Built with", 30, (200, 205, 210), False),
               ("Python · PyTorch · OWLv2 · OpenCV · pytest", 46, (255, 255, 255), True),
               ("github.com/aphisit-aoonu/durian-orchard-monitor", 30, (255, 196, 0), False)]), 4)
    ff.stdin.close()
    ff.wait()
    print(out)


if __name__ == "__main__":
    main()
