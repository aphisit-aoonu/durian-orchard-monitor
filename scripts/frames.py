"""Dump frames of a video as JPEGs for a quick look: python -m scripts.frames video.mp4 prefix t1 t2 ..."""
import sys
from pathlib import Path

import cv2

src, prefix = sys.argv[1], sys.argv[2]
out = Path("out") / "frames"
out.mkdir(parents=True, exist_ok=True)
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
print("fps", fps, "frames", int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), "size", int(cap.get(3)), int(cap.get(4)))
for t in sys.argv[3:]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(float(t) * fps))
    ok, frame = cap.read()
    if ok:
        h, w = frame.shape[:2]
        s = 640 / max(h, w)
        cv2.imwrite(str(out / f"{prefix}_{t}.jpg"), cv2.resize(frame, (int(w * s), int(h * s))))
