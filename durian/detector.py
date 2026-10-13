"""Open-vocabulary durian detector (OWLv2, no training needed)."""
import cv2
import torch
from PIL import Image
from torchvision.ops import nms
from transformers import Owlv2ForObjectDetection, Owlv2Processor

MODEL = "google/owlv2-base-patch16-ensemble"
PROMPTS = ["a durian fruit"]


class Detector:
    def __init__(self, threshold: float = 0.2, min_area: float = 0.0004, max_area: float = 0.5):
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.proc = Owlv2Processor.from_pretrained(MODEL)
        self.model = Owlv2ForObjectDetection.from_pretrained(MODEL).to(self.dev).eval()
        if self.dev == "cuda":
            self.model.half()
        self.threshold, self.min_area, self.max_area = threshold, min_area, max_area

    @torch.no_grad()
    def __call__(self, frame_bgr) -> list[tuple[list[float], float]]:
        """Return [(x1, y1, x2, y2), score] in pixel coordinates of the input frame."""
        h, w = frame_bgr.shape[:2]
        img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        inp = self.proc(text=[PROMPTS], images=img, return_tensors="pt").to(self.dev)
        if self.dev == "cuda":
            inp["pixel_values"] = inp["pixel_values"].half()
        out = self.model(**inp)
        side = max(h, w)  # the processor pads to a square; boxes come back in that frame
        post = getattr(self.proc, "post_process_grounded_object_detection", None) or self.proc.post_process_object_detection
        res = post(out, threshold=self.threshold, target_sizes=torch.tensor([[side, side]]))[0]
        boxes, scores = res["boxes"].float().cpu(), res["scores"].float().cpu()
        if not len(boxes):
            return []
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clamp(0, w)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clamp(0, h)
        area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        ok = (area > self.min_area * w * h) & (area < self.max_area * w * h)
        boxes, scores = boxes[ok], scores[ok]
        keep = nms(boxes, scores, 0.4)
        return drop_nested([(boxes[i].tolist(), float(scores[i])) for i in keep])


def drop_nested(dets: list[tuple[list[float], float]], cover: float = 0.7) -> list[tuple[list[float], float]]:
    """Remove a box mostly inside another one. OWLv2 often adds a second box on part of a fruit,
    or one box spanning two touching fruits on top of the two correct ones."""
    def area(b):
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])

    def inter(a, b):
        return area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])

    boxes = [b for b, _ in dets]
    holds = [[j for j, b in enumerate(boxes) if j != i and area(b) < area(a) and inter(a, b) > cover * area(b)]
             for i, a in enumerate(boxes)]
    merged = {i for i, inside in enumerate(holds) if len(inside) >= 2}
    partial = {j for i, inside in enumerate(holds) if len(inside) == 1 for j in inside}
    return [d for k, d in enumerate(dets) if k not in merged | partial]
