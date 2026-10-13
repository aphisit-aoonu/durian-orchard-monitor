"""Still orchard plan with the numbers the layout implies. Clearly labelled as a simulation.

Usage: python -m scripts.sim_plan [en|th]   -> out/sim_plan_<lang>.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from durian import plan_draw as pd
from durian import render
from durian.layout import Orchard

CART_SPEED = 0.5      # m/s, typical for small orchard monorails
STOP_SECONDS = 30     # camera pass per tree (both sides from one stop)

TEXT = {
    "en": {
        "title": "Orchard plan", "badge": "SIMULATION",
        "sub": "One inspection cart on a rail serves every tree. Nets catch cut fruit; the rail brings it to one collection point.",
        "depot": "Depot · charge + clean lens", "collection": "Collection point · truck pickup",
        "k_trees": "trees", "k_area": "rai", "k_rail": "m of rail", "k_far": "m max tree to rail", "k_round": "min per full round",
        "legend": [("canopy", pd.CANOPY), ("catch net", pd.NET), ("rail", pd.RAIL), ("cart", (255, 196, 0))],
        "steps_title": "After a fruit is ready",
        "steps": ["Cart camera confirms the fruit (day count + photo)", "Cutter on a pole cuts the stem",
                  "Fruit drops into the net, never hits the ground", "Net funnels it into the cart basket",
                  "Rail brings it to the collection point", "Weigh, count, label · truck is notified"],
        "foot": "Layout and timings are calculated from the plan above, not measured in a real orchard.",
    },
    "th": {
        "title": "แปลนสวน", "badge": "ภาพจำลอง",
        "sub": "รถตรวจคันเดียววิ่งบนรางผ่านทุกต้น · ตาข่ายรับลูกที่ตัด · รางพาลูกไปจุดรับจุดเดียว",
        "depot": "โรงจอด · ชาร์จ + ล้างเลนส์", "collection": "จุดรับ · รถมารับ",
        "k_trees": "ต้น", "k_area": "ไร่", "k_rail": "ม. ราง", "k_far": "ม. ต้นไกลรางสุด", "k_round": "นาที ต่อรอบ",
        "legend": [("ทรงพุ่ม", pd.CANOPY), ("ตาข่ายรับ", pd.NET), ("ราง", pd.RAIL), ("รถตรวจ", (255, 196, 0))],
        "steps_title": "พอลูกถึงเวลาตัด",
        "steps": ["กล้องบนรถยืนยันลูก (นับวัน + ภาพ)", "หัวตัดบนเสายืดตัดขั้ว",
                  "ลูกตกลงตาข่าย ไม่ถึงพื้น", "ตาข่ายเทลงตะกร้าบนรถ",
                  "รางพาไปจุดรับ", "ชั่ง นับ ติดป้าย · แจ้งรถมารับ"],
        "foot": "ระยะและเวลาคำนวณจากแปลนนี้ ยังไม่ได้วัดในสวนจริง",
    },
}


def stats(o: Orchard) -> dict:
    import math
    far = max(min(math.dist((t.x, t.y), o.point_at(s / 4)) for s in range(int(o.rail_length * 4))) for t in o.trees)
    round_min = (o.rail_length / CART_SPEED + len(o.trees) * STOP_SECONDS) / 60
    return {"trees": len(o.trees), "rai": o.width * o.height / 1600, "rail": o.rail_length, "far": far, "round": round_min}


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    o = Orchard()
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), render.PAPER)
    d = ImageDraw.Draw(img, "RGBA")

    d.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = d.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(d, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    d.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(22))

    v = pd.View(56, 190, 9.3)
    pd.draw_ground(d, o, v)
    pd.draw_rail(d, o, v)
    pd.draw_trees(d, o, v)
    pd.draw_buildings(d, o, v, t)
    p = o.point_at(118)
    pd.draw_cart(d, p, 0.0, v)
    pd.scale_bar(d, v, 70, H - 60)

    px = 1150
    s = stats(o)
    cards = [(f"{s['trees']}", t["k_trees"]), (f"{s['rai']:.1f}", t["k_area"]), (f"{s['rail']:.0f}", t["k_rail"]),
             (f"{s['far']:.1f}", t["k_far"]), (f"{s['round']:.0f}", t["k_round"])]
    cw = (W - px - 56 - 2 * 14) // 3
    for k, (num, label) in enumerate(cards):
        x = px + (k % 3) * (cw + 14)
        y = 170 + (k // 3) * 116
        d.rounded_rectangle([x, y, x + cw, y + 102], radius=14, fill=render.CARD)
        d.text((x + 18, y + 12), num, fill=render.INK, font=render.font(36, bold=True))
        d.text((x + 18, y + 64), label, fill=render.MUTED, font=render.font(17))

    y = 420
    d.text((px, y), t["steps_title"], fill=render.INK, font=render.font(26, bold=True))
    y += 50
    for k, step in enumerate(t["steps"]):
        d.ellipse([px, y, px + 34, y + 34], fill=render.ACCENT)
        n = str(k + 1)
        d.text((px + 17 - d.textlength(n, font=render.font(18, bold=True)) / 2, y + 4), n, fill=render.INK,
               font=render.font(18, bold=True))
        d.text((px + 50, y + 3), step, fill=render.INK, font=render.font(20))
        if k < len(t["steps"]) - 1:
            d.line([(px + 17, y + 38), (px + 17, y + 56)], fill=(200, 200, 200), width=2)
        y += 60

    lx = px
    for name, col in t["legend"]:
        d.rounded_rectangle([lx, H - 120, lx + 22, H - 102], radius=4, fill=col)
        d.text((lx + 30, H - 124), name, fill=render.INK, font=render.font(17))
        lx += 40 + d.textlength(name, font=render.font(17)) + 18
    d.text((px, H - 80), t["foot"], fill=render.MUTED, font=render.font(16))

    out = Path("out") / f"sim_plan_{lang}.png"
    img.save(out)
    print(out, {k: round(val, 1) for k, val in s.items()})


if __name__ == "__main__":
    main()
