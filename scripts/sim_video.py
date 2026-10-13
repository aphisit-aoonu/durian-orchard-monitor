"""Animated simulation of one inspection round: cart on the rail, cutting, net, basket, collection point.

Usage: python -m scripts.sim_video [en|th]   -> out/sim_round_<lang>.mp4
Everything here is simulated (which fruit is ready is random with a fixed seed). The video says so on every frame.
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from durian import plan_draw as pd
from durian import render
from durian.layout import Orchard

W, H, FPS = 1920, 1080, 30
TRAVEL_SECONDS = 26          # video seconds for one full loop of travel
CUT_SECONDS = (2.8, 2.8, 0.8)  # first cuts slow so the side view can be followed, the rest quick
UNLOAD_SECONDS = 3.0
SEED = 7

TEXT = {
    "en": {"title": "One inspection round", "badge": "SIMULATION",
           "sub": "Which fruit is ready is simulated. Distances come from the orchard plan.",
           "inspected": "trees passed", "cut": "fruit cut", "basket": "in basket", "delivered": "delivered",
           "steps": ["Camera confirms ready fruit", "Pole cutter cuts the stem", "Fruit drops into the net",
                     "Net funnels it to the basket", "Rail carries it to collection", "Weigh, count, notify truck"],
           "side": "Side view", "truck": "Truck notified: {n} fruit ready for pickup",
           "depot": "Depot", "collection": "Collection point", "at": "Tree {id}",
           "ready": "tree with fruit ready to cut", "done": "cut this round"},
    "th": {"title": "หนึ่งรอบการตรวจ", "badge": "ภาพจำลอง",
           "sub": "ลูกไหนถึงเวลาตัดเป็นข้อมูลจำลอง · ระยะทางมาจากแปลนสวน",
           "inspected": "ต้นที่ผ่าน", "cut": "ลูกที่ตัด", "basket": "ในตะกร้า", "delivered": "ส่งถึงจุดรับ",
           "steps": ["กล้องยืนยันลูกที่ถึงเวลา", "หัวตัดบนเสายืดตัดขั้ว", "ลูกตกลงตาข่าย",
                     "ตาข่ายเทลงตะกร้า", "รางพาไปจุดรับ", "ชั่ง นับ แจ้งรถมารับ"],
           "side": "ภาพด้านข้าง", "truck": "แจ้งรถแล้ว: มี {n} ลูกรอรับ",
           "depot": "โรงจอด", "collection": "จุดรับ", "at": "ต้น {id}",
           "ready": "ต้นที่มีลูกถึงเวลาตัด", "done": "ตัดแล้วรอบนี้"},
}


def plan_events(o: Orchard) -> list[tuple[float, str, int]]:
    """(rail position, tree id, fruit count) for trees with ready fruit, in the order the cart reaches them."""
    rng = random.Random(SEED)
    ready = {t.id: rng.choice([0, 0, 0, 0, 1, 1, 2]) for t in o.trees}
    stops = sorted((o.stop_for(t), t.id, ready[t.id]) for t in o.trees if ready[t.id])
    return stops


def timeline(o: Orchard, stops) -> list[dict]:
    """Per video frame: cart position, phase and counters."""
    speed = o.rail_length / (TRAVEL_SECONDS * FPS)  # metres per frame
    frames, s, basket, cut, delivered = [], 0.0, 0, 0, 0
    passed = 0
    stop_iter = iter(stops)
    nxt = next(stop_iter, None)
    tree_stops = sorted(o.stop_for(t) for t in o.trees)
    while s < o.rail_length:
        while nxt and s >= nxt[0]:
            for k in range(nxt[2]):
                n = int(CUT_SECONDS[min(cut, len(CUT_SECONDS) - 1)] * FPS)
                for f in range(n):
                    frames.append({"s": nxt[0], "phase": "cut", "p": f / n, "tree": nxt[1],
                                   "basket": basket, "cut": cut, "delivered": delivered, "passed": passed})
                basket += 1
                cut += 1
            nxt = next(stop_iter, None)
        passed = sum(1 for x in tree_stops if x <= s)
        frames.append({"s": s, "phase": "travel", "basket": basket, "cut": cut, "delivered": delivered, "passed": passed})
        s += speed
    for f in range(int(UNLOAD_SECONDS * FPS)):
        moved = min(basket, int(basket * f / (UNLOAD_SECONDS * FPS * 0.7)))
        frames.append({"s": o.rail_length - 0.01, "phase": "unload", "p": f / (UNLOAD_SECONDS * FPS),
                       "basket": basket - moved, "cut": cut, "delivered": moved, "passed": len(o.trees)})
    for _ in range(FPS * 3):
        frames.append({**frames[-1], "phase": "done"})
    return frames


def side_view(d: ImageDraw.ImageDraw, box, phase: str, p: float, t: dict) -> None:
    """Small side-view illustration of cut -> net -> basket, scaled to the box."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=16, fill=render.CARD)
    d.text((x0 + 18, y0 + 12), t["side"], fill=render.MUTED, font=render.font(16, bold=True))
    gy = y1 - 26
    d.line([(x0 + 16, gy), (x1 - 16, gy)], fill=(180, 170, 150), width=3)
    tx = x0 + 150
    can_top, can_bot = y0 + 46, y0 + 150
    d.rectangle([tx - 9, can_bot - 20, tx + 9, gy], fill=(110, 80, 50))
    d.ellipse([tx - 100, can_top, tx + 100, can_bot], fill=pd.CANOPY)
    rail_y, cart_x = gy - 34, x1 - 120
    d.line([(cart_x - 80, rail_y + 18), (x1 - 20, rail_y + 18)], fill=pd.RAIL, width=5)
    d.rounded_rectangle([cart_x - 45, rail_y - 18, cart_x + 45, rail_y + 14], radius=6, fill=(255, 196, 0),
                        outline=render.INK, width=2)
    # net: under the canopy, sloping down into the basket
    net = [(tx - 70, can_bot + 18), (tx + 80, can_bot + 30), (cart_x - 40, rail_y - 20)]
    d.line(net, fill=pd.NET, width=4)
    hang = (tx + 45, can_bot + 2)
    if phase != "cut":
        d.ellipse([hang[0] - 13, hang[1] - 16, hang[0] + 13, hang[1] + 16], fill=(150, 160, 60))
        return
    stem = (hang[0] + 2, hang[1] - 18)
    ext = min(1.0, p / 0.25)
    px = cart_x + (stem[0] + 14 - cart_x) * ext
    py = rail_y - 18 + (stem[1] - (rail_y - 18)) * ext
    d.line([(cart_x, rail_y - 18), (px, py)], fill=render.INK, width=4)
    if 0.25 <= p < 0.38:
        d.ellipse([stem[0] - 11, stem[1] - 11, stem[0] + 11, stem[1] + 11], outline=(214, 69, 65), width=3)
    if p < 0.35:
        fx, fy = hang
        d.line([(fx, fy - 16), stem], fill=(90, 70, 40), width=3)
    elif p < 0.55:
        f = (p - 0.35) / 0.2
        target = net[0][1] + (net[1][1] - net[0][1]) * ((hang[0] - net[0][0]) / (net[1][0] - net[0][0])) - 16
        fx, fy = hang[0], hang[1] + (target - hang[1]) * f * f
    else:
        f = min(1.0, (p - 0.55) / 0.4)
        sx = hang[0]
        sy = net[0][1] + (net[1][1] - net[0][1]) * ((hang[0] - net[0][0]) / (net[1][0] - net[0][0])) - 16
        ex, ey = net[2][0] + 22, net[2][1] - 4
        fx, fy = sx + (ex - sx) * f, sy + (ey - sy) * f
    d.ellipse([fx - 13, fy - 16, fx + 13, fy + 16], fill=(150, 160, 60), outline=(90, 100, 30), width=2)


def active_step(row) -> int:
    if row["phase"] == "cut":
        p = row["p"]
        return 0 if p < 0.12 else 1 if p < 0.35 else 2 if p < 0.55 else 3
    if row["phase"] in ("unload", "done"):
        return 5
    return 4 if row["basket"] else -1


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    o = Orchard()
    stops = plan_events(o)
    rows = timeline(o, stops)
    ready_trees = {tid for _, tid, _ in stops}

    v = pd.View(56, 190, 9.3)
    base = Image.new("RGB", (W, H), render.PAPER)
    bd = ImageDraw.Draw(base, "RGBA")
    bd.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = bd.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(bd, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    bd.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(22))
    pd.draw_ground(bd, o, v)
    pd.draw_rail(bd, o, v)
    pd.draw_buildings(bd, o, v, {"depot": t["depot"], "collection": t["collection"]})

    out_path = Path("out") / f"sim_round_{lang}.mp4"
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
                          stdin=subprocess.PIPE)
    done_cut: set[str] = set()
    px = 1150
    for i, row in enumerate(rows):
        img = base.copy()
        d = ImageDraw.Draw(img, "RGBA")
        if row["phase"] == "cut" and row["p"] > 0.9:
            done_cut.add(row["tree"])
        hl = {tid: (214, 160, 40) for tid in ready_trees - done_cut}
        hl.update({tid: (120, 140, 120) for tid in done_cut})
        pd.draw_trees(d, o, v, highlight=hl)
        s = row["s"]
        a, b = o.point_at(s), o.point_at(s + 0.5)
        heading = math.atan2(b[1] - a[1], b[0] - a[0])
        pd.draw_cart(d, a, heading, v, busy=row["phase"] == "cut")
        if row["phase"] == "cut":
            cx, cy = v(*a)
            render.pill(d, (cx + 18, cy - 46), t["at"].format(id=row["tree"]), size=16, bg=(20, 24, 28, 220))

        nums = [(row["passed"], t["inspected"]), (row["cut"], t["cut"]), (row["basket"], t["basket"]),
                (row["delivered"], t["delivered"])]
        cw = (W - px - 56 - 3 * 12) // 4
        for k, (n, label) in enumerate(nums):
            x = px + k * (cw + 12)
            d.rounded_rectangle([x, 170, x + cw, 262], radius=14, fill=render.CARD)
            d.text((x + 16, 180), str(n), fill=render.INK, font=render.font(34, bold=True))
            d.text((x + 16, 228), label, fill=render.MUTED, font=render.font(15))

        step = active_step(row)
        y = 292
        for k, text in enumerate(t["steps"]):
            on = k == step
            d.rounded_rectangle([px, y, W - 56, y + 44], radius=10, fill=(255, 244, 204) if on else render.CARD)
            d.ellipse([px + 10, y + 8, px + 38, y + 36], fill=render.ACCENT if on else (225, 225, 225))
            n = str(k + 1)
            d.text((px + 24 - d.textlength(n, font=render.font(16, bold=True)) / 2, y + 10), n, fill=render.INK,
                   font=render.font(16, bold=True))
            d.text((px + 50, y + 9), text, fill=render.INK if on else render.MUTED, font=render.font(18, bold=on))
            y += 52

        side_view(d, (px, 620, W - 56, 900), row["phase"], row.get("p", 0.0), t)
        lx, ly = 92, 840
        for label, col in [(t["ready"], (214, 160, 40)), (t["done"], (120, 140, 120))]:
            d.ellipse([lx, ly, lx + 20, ly + 20], fill=col)
            d.text((lx + 28, ly - 3), label, fill=render.INK, font=render.font(17))
            lx += 60 + d.textlength(label, font=render.font(17))
        if row["phase"] in ("unload", "done") and row["delivered"]:
            render.pill(d, (px, 920), t["truck"].format(n=row["delivered"]), size=20, bg=(46, 160, 67, 240))
        ff.stdin.write(np.asarray(img).tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"out/sim_round_{lang}.mp4: {len(rows) / FPS:.1f}s, {len(stops)} trees with ready fruit, {rows[-1]['delivered']} fruit delivered")


if __name__ == "__main__":
    main()
