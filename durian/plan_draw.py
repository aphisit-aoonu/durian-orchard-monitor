"""Draw the orchard plan (top-down). Shared by the still plan and the animated simulation."""
import math

from PIL import ImageDraw

from . import render
from .layout import Orchard

GROUND = (233, 239, 226)
ROAD = (214, 210, 200)
CANOPY = (58, 122, 70)
CANOPY_HI = (92, 158, 96)
NET = (150, 120, 70)
RAIL = (90, 96, 104)
SLEEPER = (150, 154, 160)
DEPOT = (66, 99, 160)
COLLECT = (196, 120, 40)


class View:
    """Maps orchard metres to canvas pixels."""

    def __init__(self, ox: float, oy: float, scale: float, x_min: float = -30.0, y_min: float = 0.0):
        self.ox, self.oy, self.s, self.x_min, self.y_min = ox, oy, scale, x_min, y_min

    def __call__(self, x: float, y: float) -> tuple[float, float]:
        return self.ox + (x - self.x_min) * self.s, self.oy + (y - self.y_min) * self.s


def dashed_circle(d, c, r, color, width=2, dash=10):
    n = max(12, int(2 * math.pi * r / dash))
    for k in range(0, n, 2):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        d.arc([c[0] - r, c[1] - r, c[0] + r, c[1] + r], math.degrees(a0), math.degrees(a1), fill=color, width=width)


def draw_ground(d: ImageDraw.ImageDraw, o: Orchard, v: View) -> None:
    x0, y0 = v(o.depot[0] - 12, -2)
    x1, y1 = v(o.width + 2, o.height + 2)
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=GROUND)
    rx0, _ = v(o.depot[0] - 11, 0)
    rx1, _ = v(o.depot[0] - 7, 0)
    d.rectangle([rx0, y0 + 8, rx1, y1 - 8], fill=ROAD)


def draw_rail(d: ImageDraw.ImageDraw, o: Orchard, v: View) -> None:
    pts = [v(*p) for p in o.route]
    for a, b in zip(o.route, o.route[1:]):
        seg = math.dist(a, b)
        for k in range(int(seg / 1.5) + 1):
            f = k * 1.5 / seg if seg else 0
            px, py = v(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            nx, ny = (b[1] - a[1]) / seg, -(b[0] - a[0]) / seg
            d.line([(px - nx * 7, py - ny * 7), (px + nx * 7, py + ny * 7)], fill=SLEEPER, width=2)
    d.line(pts, fill=RAIL, width=5, joint="curve")


def draw_trees(d: ImageDraw.ImageDraw, o: Orchard, v: View, highlight: dict | None = None, labels: bool = True) -> None:
    highlight = highlight or {}
    r = o.canopy * v.s
    for t in o.trees:
        c = v(t.x, t.y)
        dashed_circle(d, c, r + 0.9 * v.s, NET, width=2)
        col = highlight.get(t.id, CANOPY)
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=col)
        d.ellipse([c[0] - r * 0.55, c[1] - r * 0.75, c[0] + r * 0.25, c[1] - r * 0.05], fill=CANOPY_HI if col == CANOPY else col)
        if labels:
            f = render.font(max(10, int(v.s * 0.95)), bold=True)
            tw = d.textlength(t.id, font=f)
            d.text((c[0] - tw / 2, c[1] + r * 0.15), t.id, fill=(235, 245, 235), font=f)


def draw_buildings(d: ImageDraw.ImageDraw, o: Orchard, v: View, text: dict) -> None:
    for (x, y), color, label, above in [(o.collection, COLLECT, text["collection"], True),
                                        (o.depot, DEPOT, text["depot"], False)]:
        cx, cy = v(x, y)
        s = 2.4 * v.s
        d.rounded_rectangle([cx - s, cy - s * 0.7, cx + s, cy + s * 0.7], radius=6, fill=color)
        ly = cy - s * 0.7 - 34 if above else cy + s * 0.7 + 6
        render.pill(d, (cx - s, ly), label, size=14, bg=(255, 255, 255, 235), fg=render.INK, pad=7)


def draw_cart(d: ImageDraw.ImageDraw, pos: tuple[float, float], heading: float, v: View, busy: bool = False) -> None:
    cx, cy = v(*pos)
    s = 1.6 * v.s
    pts = []
    for dx, dy in [(-s, -s * 0.6), (s, -s * 0.6), (s, s * 0.6), (-s, s * 0.6)]:
        pts.append((cx + dx * math.cos(heading) - dy * math.sin(heading), cy + dx * math.sin(heading) + dy * math.cos(heading)))
    d.polygon(pts, fill=(255, 196, 0) if not busy else (46, 160, 67), outline=render.INK, width=2)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=render.INK)


def scale_bar(d: ImageDraw.ImageDraw, v: View, x: float, y: float, metres: int = 10) -> None:
    px = metres * v.s
    d.line([(x, y), (x + px, y)], fill=render.INK, width=3)
    for xx in (x, x + px):
        d.line([(xx, y - 6), (xx, y + 6)], fill=render.INK, width=3)
    d.text((x + px + 8, y - 10), f"{metres} m", fill=render.INK, font=render.font(15, bold=True))
