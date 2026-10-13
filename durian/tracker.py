"""Give each fruit one id across frames, in camera-compensated ('world') coordinates."""
from dataclasses import dataclass, field

CONFIRM_HITS = 3          # detections before a fruit counts
FORGET_AFTER = 6          # detection rounds without a match before a track is dropped
LOWERED_SIZES = 1.2       # world-space drop, in fruit heights, that means the fruit is being lowered
LOWERED_WINDOW = 8        # detection rounds to look back over


def iou(a, b) -> float:
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _centre(b):
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def _near(a, b) -> float:
    """1.0 when centres coincide, falling to 0 at one fruit-width apart."""
    (ax, ay), (bx, by) = _centre(a), _centre(b)
    size = max(a[2] - a[0], a[3] - a[1], 1.0)
    d = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5 / size
    return max(0.0, 1.0 - d)


@dataclass
class Track:
    id: int
    box: list[float]                  # world coordinates
    score: float
    hits: int = 1
    missed: int = 0
    lowered: bool = False
    path: list[tuple[float, float]] = field(default_factory=list)  # world centres, one per hit
    path_box: list[float] = field(default_factory=list)            # latest raw detection, world coords

    @property
    def confirmed(self) -> bool:
        return self.hits >= CONFIRM_HITS


class Tracker:
    def __init__(self):
        self.tracks: list[Track] = []
        self.next_id = 1
        self.counted: set[int] = set()

    def update(self, world_dets: list[tuple[list[float], float]]) -> list[Track]:
        """Match this round's detections (already in world coords). Returns tracks that just got 'lowered'."""
        pairs = []
        for ti, tr in enumerate(self.tracks):
            for di, (box, _) in enumerate(world_dets):
                s = max(iou(tr.box, box), 0.8 * _near(tr.box, box))
                # a fruit being lowered moves straight down faster than IoU can follow
                cx, cy = _centre(tr.box)
                bx, by = _centre(box)
                h = tr.box[3] - tr.box[1]
                # once a fruit is known to be going down it can drop much further between rounds
                reach, side = (6.0, 1.0) if tr.lowered else (2.5, 0.6)
                if abs(bx - cx) < side * h and 0 < by - cy < reach * h:
                    s = max(s, 0.3)
                if s >= 0.25:
                    pairs.append((s, ti, di))
        used_t, used_d, newly_lowered = set(), set(), []
        for s, ti, di in sorted(pairs, reverse=True):
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            tr = self.tracks[ti]
            box, score = world_dets[di]
            tr.box = [0.5 * a + 0.5 * b for a, b in zip(tr.box, box)]
            tr.score, tr.hits, tr.missed = score, tr.hits + 1, 0
            tr.path.append(_centre(box))
            tr.path_box = list(box)
            if tr.confirmed:
                self.counted.add(tr.id)
            if not tr.lowered and len(tr.path) >= 4:
                recent = tr.path[-LOWERED_WINDOW:]
                drop = recent[-1][1] - recent[0][1]
                # a lowered fruit keeps going down; camera drift jitters up and down
                steady = all(b[1] >= a[1] for a, b in zip(recent, recent[1:]))
                if steady and drop > LOWERED_SIZES * (tr.box[3] - tr.box[1]):
                    tr.lowered = True
                    newly_lowered.append(tr)
        for ti, tr in enumerate(self.tracks):
            if ti not in used_t:
                tr.missed += 1
        for di, (box, score) in enumerate(world_dets):
            if di not in used_d:
                self.tracks.append(Track(self.next_id, list(box), score, path=[_centre(box)], path_box=list(box)))
                self.next_id += 1
        reported = [t for t in newly_lowered if not self._merge_into_earlier_lowered(t)]
        # a lowered fruit is kept longer so a late duplicate further down can still be merged
        self.tracks = [t for t in self.tracks if t.missed <= FORGET_AFTER * (2 if t.lowered else 1)]
        return reported

    def _merge_into_earlier_lowered(self, tr: Track) -> bool:
        """A fruit on a rope can outrun matching and come back as a new track below the old one.
        If so, give it the old id back so it is reported and counted once."""
        h = tr.box[3] - tr.box[1]
        cx, cy = _centre(tr.box)
        for old in self.tracks:
            if old is tr or not old.lowered:
                continue
            ox, oy = _centre(old.box)
            if abs(cx - ox) < h and 0 < cy - oy < 6 * h:
                self.counted.discard(tr.id)
                tr.id = old.id
                self.tracks.remove(old)
                return True
        return False

    @property
    def unique_count(self) -> int:
        return len(self.counted)
