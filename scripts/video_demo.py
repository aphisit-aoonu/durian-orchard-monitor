"""Annotated demo clip: every durian gets one id even while the camera moves, plus a running count.

Usage:
  python -m scripts.video_demo analyse videos/tree.mp4     # slow: detection, cached in out/<name>.analysis.json
  python -m scripts.video_demo render videos/tree.mp4 en   # fast: draw the clip (en or th)
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from durian import render
from durian.motion import CameraMotion, apply
from durian.tracker import Tracker

DETECT_EVERY = 4
THRESHOLD = 0.25
OUT = Path("out")

TEXT = {
    "en": {"title": "Durian monitor", "sub": "camera-compensated tracking", "view": "In view", "count": "Tracked so far",
           "unique": "one id per fruit", "lowered": "#{id} lowered from the tree", "camera": "camera moving fast"},
    "th": {"title": "ตรวจลูกทุเรียน", "sub": "ชดเชยการขยับกล้อง", "view": "เห็นตอนนี้", "count": "ติดตามแล้ว",
           "unique": "ลูกละ 1 เลข", "lowered": "ลูก #{id} ถูกหย่อนลงจากต้น", "camera": "กล้องขยับเร็ว"},
}


def analyse(src: Path) -> None:
    from durian.detector import Detector  # heavy import only when needed

    det = Detector(THRESHOLD)
    motion = CameraMotion()
    cap = cv2.VideoCapture(str(src))
    fps, total = cap.get(cv2.CAP_PROP_FPS) or 30, int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        to_world = motion.update(frame)
        row = {"T": to_world.round(6).tolist(), "lost": motion.lost}
        if i % DETECT_EVERY == 0:
            row["dets"] = [[[round(v, 1) for v in b], round(s, 3)] for b, s in det(frame)]
        frames.append(row)
        if i % 100 == 0:
            print(f"{i}/{total}", flush=True)
        i += 1
    (OUT / f"{src.stem}.analysis.json").write_text(json.dumps({"fps": fps, "frames": frames}), encoding="utf-8")
    print(f"analysed {i} frames")


def hud(d: ImageDraw.ImageDraw, t: dict, in_view: int, counted: int, w: int) -> None:
    d.rounded_rectangle([20, 20, 330, 150], radius=16, fill=(12, 16, 20, 190))
    d.text((38, 30), t["title"], fill=(255, 255, 255), font=render.font(24, bold=True))
    d.text((38, 62), t["sub"], fill=(170, 178, 186), font=render.font(15))
    d.text((38, 88), str(in_view), fill=render.ACCENT, font=render.font(34, bold=True))
    d.text((38, 126), t["view"], fill=(200, 205, 210), font=render.font(14))
    d.text((170, 88), str(counted), fill=(255, 255, 255), font=render.font(34, bold=True))
    d.text((170, 126), f"{t['count']} · {t['unique']}", fill=(200, 205, 210), font=render.font(14))


def render_clip(src: Path, lang: str) -> None:
    t = TEXT[lang]
    data = json.loads((OUT / f"{src.stem}.analysis.json").read_text(encoding="utf-8"))
    fps, rows = data["fps"], data["frames"]
    cap = cv2.VideoCapture(str(src))
    w, h = int(cap.get(3)), int(cap.get(4))
    raw = OUT / f"{src.stem}_{lang}.raw.mp4"
    writer = cv2.VideoWriter(str(raw), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    tracker = Tracker()
    events: list[tuple[int, str]] = []
    lowered_ids: set[int] = set()
    seen_at: dict[int, tuple[int, list[float], np.ndarray]] = {}  # track id -> (frame, box in that frame, to_world)
    for i, row in enumerate(rows):
        ok, frame = cap.read()
        if not ok:
            break
        to_world = np.array(row["T"])
        if "dets" in row:
            world = [(apply(to_world, b), s) for b, s in row["dets"]]
            before = {tr.id: tr.hits for tr in tracker.tracks}
            for tr in tracker.update(world):
                lowered_ids.add(tr.id)
                events.append((i, t["lowered"].format(id=tr.id)))
            # remember where each matched fruit really was in this frame, for drawing
            inv = np.linalg.inv(to_world)
            for tr in tracker.tracks:
                if tr.missed == 0 and tr.hits != before.get(tr.id, 0):
                    seen_at[tr.id] = (i, apply(inv, tr.path_box), to_world)
        to_frame = np.linalg.inv(to_world)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        in_view = 0
        for tr in tracker.tracks:
            if not tr.confirmed or tr.id not in seen_at or i - seen_at[tr.id][0] > DETECT_EVERY:
                continue
            fi, fbox, fworld = seen_at[tr.id]
            # last real detection, shifted only by the camera motion since then (at most a few frames)
            box = apply(to_frame @ fworld, fbox)
            if box[2] < 0 or box[3] < 0 or box[0] > w or box[1] > h:
                continue
            in_view += 1
            color = render.GREEN if tr.id in lowered_ids else render.ACCENT
            render.corner_box(d, box, color, width=3)
            render.tag(d, (box[0], box[1] - 2), f"#{tr.id}", size=15, bg=color, fg=render.INK)
        hud(d, t, in_view, tracker.unique_count, w)
        recent = [text for (fi, text) in events if 0 <= i - fi < fps * 3][-2:]
        for k, text in enumerate(recent):
            render.pill(d, (20, h - 70 - k * 52), text, size=22, bg=(46, 160, 67, 230))
        if row.get("lost"):
            render.pill(d, (w - 230, 24), t["camera"], size=18, bg=(200, 60, 50, 220))
        out = Image.alpha_composite(img, layer).convert("RGB")
        writer.write(cv2.cvtColor(np.asarray(out), cv2.COLOR_RGB2BGR))
    writer.release()
    final = OUT / f"{src.stem}_demo_{lang}.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(raw), "-c:v", "libx264",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)], check=True)
    raw.unlink()
    print(f"{final}: counted {tracker.unique_count} fruits, {len(events)} lowered events")


if __name__ == "__main__":
    mode, src = sys.argv[1], Path(sys.argv[2])
    OUT.mkdir(exist_ok=True)
    if mode == "analyse":
        analyse(src)
    else:
        render_clip(src, sys.argv[3] if len(sys.argv) > 3 else "en")
