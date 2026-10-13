"""Tree heights against the 6 m reach, and which trees come due for cutting in the next weeks.

Usage: python -m scripts.sim_height [en|th]   -> out/sim_height_<lang>.png
Heights, growth rates and bloom dates are simulated with a fixed seed. The picture says so.
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw

from durian import plan_draw as pd
from durian import render
from durian.growth import DAYS_TO_HARVEST, REACH_M, TreeState, due_in_week
from durian.layout import Orchard

W, H = 1920, 1080
SEED = 11
TODAY = date(2026, 5, 4)
WEEKS = 6
COLORS = {"ok": pd.CANOPY, "soon": (232, 137, 12), "over": (214, 69, 65)}

TEXT = {
    "en": {"title": "Tree height and cutting calendar", "badge": "SIMULATION",
           "sub": f"Heights and bloom dates are simulated. Rule: fruit is due {DAYS_TO_HARVEST} days after full bloom (Monthong).",
           "k": {"ok": "within reach", "soon": "top after this harvest", "over": f"over {REACH_M:.0f} m"},
           "trim": "Top these first", "trim_row": "{id}  {h:.1f} m", "none": "none",
           "cal": "Trees due for cutting, by week", "week": "{d} {m}", "now": "this week",
           "list": "This week's list for the cutters", "row": "{id}  ·  day {n} of {total}  ·  due {d} {m}",
           "more": "and {n} more trees later this week",
           "legend": "Number on each tree: height in metres",
           "foot": "With real data, heights come from a drone survey and bloom dates from the grower's log.",
           "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
    "th": {"title": "ความสูงต้น และปฏิทินตัด", "badge": "ภาพจำลอง",
           "sub": f"ความสูงและวันดอกบานเป็นข้อมูลจำลอง · เกณฑ์: ลูกถึงกำหนด {DAYS_TO_HARVEST} วันหลังดอกบาน (หมอนทอง)",
           "k": {"ok": "เอื้อมถึง", "soon": "ตัดยอดหลังเก็บรอบนี้", "over": f"สูงเกิน {REACH_M:.0f} ม."},
           "trim": "ต้นที่ต้องตัดยอดก่อน", "trim_row": "{id}  {h:.1f} ม.", "none": "ไม่มี",
           "cal": "จำนวนต้นที่ถึงกำหนดตัด รายสัปดาห์", "week": "{d} {m}", "now": "สัปดาห์นี้",
           "list": "รายการสัปดาห์นี้สำหรับมือตัด", "row": "{id}  ·  วันที่ {n} จาก {total}  ·  ครบกำหนด {d} {m}",
           "more": "และอีก {n} ต้นในสัปดาห์นี้",
           "legend": "ตัวเลขบนต้น: ความสูงเป็นเมตร",
           "foot": "ถ้าใช้ข้อมูลจริง ความสูงมาจากโดรนสำรวจ วันดอกบานมาจากบันทึกของเจ้าของสวน",
           "months": ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]},
}


def simulate(o: Orchard) -> list[TreeState]:
    rng = random.Random(SEED)
    trees = []
    for t in o.trees:
        bloom = None
        if rng.random() < 0.75:
            bloom = TODAY - timedelta(days=DAYS_TO_HARVEST) + timedelta(days=rng.randint(-2, WEEKS * 7 - 1))
        trees.append(TreeState(t.id, round(rng.triangular(4.2, 6.6, 5.2), 1), round(rng.uniform(0.5, 0.9), 2), bloom))
    return trees


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    o = Orchard()
    states = simulate(o)
    by_id = {s.id: s for s in states}
    fmt_day = lambda dt: t["week"].format(d=dt.day, m=t["months"][dt.month - 1])

    img = Image.new("RGB", (W, H), render.PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = d.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(d, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    d.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(22))

    v = pd.View(56, 190, 9.3)
    pd.draw_ground(d, o, v)
    pd.draw_rail(d, o, v)
    r = o.canopy * v.s
    for tree in o.trees:
        s = by_id[tree.id]
        cx, cy = v(tree.x, tree.y)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLORS[s.status()])
        num = f"{s.height_m:.1f}"
        f = render.font(17, True)
        d.text((cx - d.textlength(num, font=f) / 2, cy - 20), num, fill=(255, 255, 255), font=f)
        f = render.font(12, True)
        d.text((cx - d.textlength(tree.id, font=f) / 2, cy + 4), tree.id, fill=(235, 245, 235), font=f)
    d.text((70, H - 124), t["legend"], fill=render.INK, font=render.font(17))

    px = 1150
    cw = (W - px - 56 - 2 * 14) // 3
    for k, key in enumerate(("ok", "soon", "over")):
        x = px + k * (cw + 14)
        n = sum(1 for s in states if s.status() == key)
        d.rounded_rectangle([x, 170, x + cw, 272], radius=14, fill=render.CARD)
        d.rounded_rectangle([x, 170, x + 8, 272], radius=4, fill=COLORS[key])
        d.text((x + 22, 180), str(n), fill=render.INK, font=render.font(38, True))
        d.text((x + 22, 234), t["k"][key], fill=render.MUTED, font=render.font(16))

    y = 300
    d.text((px, y), t["trim"], fill=render.INK, font=render.font(22, True))
    over = sorted((s for s in states if s.status() == "over"), key=lambda s: -s.height_m)
    x = px
    for s in over[:6]:
        x += render.pill(d, (x, y + 40), t["trim_row"].format(id=s.id, h=s.height_m), size=17, bg=COLORS["over"] + (235,), pad=9) + 10
    if not over:
        d.text((px, y + 42), t["none"], fill=render.MUTED, font=render.font(18))

    y = 420
    d.text((px, y), t["cal"], fill=render.INK, font=render.font(22, True))
    weeks = [TODAY + timedelta(days=7 * k) for k in range(WEEKS)]
    counts = [len(due_in_week(states, w)) for w in weeks]
    bw = (W - px - 56 - (WEEKS - 1) * 12) // WEEKS
    base, top = y + 250, y + 70
    for k, (w, n) in enumerate(zip(weeks, counts)):
        x = px + k * (bw + 12)
        h = (base - top) * n / max(max(counts), 1)
        d.rounded_rectangle([x, base - max(h, 4), x + bw, base], radius=8, fill=render.GREEN if k == 0 else (170, 200, 175))
        f = render.font(22, True)
        d.text((x + (bw - d.textlength(str(n), font=f)) / 2, base - max(h, 4) - 32), str(n), fill=render.INK, font=f)
        label = t["now"] if k == 0 else fmt_day(w)
        f = render.font(15, k == 0)
        d.text((x + (bw - d.textlength(label, font=f)) / 2, base + 8), label, fill=render.INK if k == 0 else render.MUTED, font=f)

    y = base + 56
    d.text((px, y), t["list"], fill=render.INK, font=render.font(22, True))
    y += 42
    due_now = due_in_week(states, TODAY)
    for s in due_now[:5]:
        d.rounded_rectangle([px, y, W - 56, y + 38], radius=9, fill=render.CARD)
        due = s.harvest_date()
        row = t["row"].format(id=s.id, n=DAYS_TO_HARVEST - s.days_to_harvest(TODAY), total=DAYS_TO_HARVEST,
                              d=due.day, m=t["months"][due.month - 1])
        d.text((px + 16, y + 7), row, fill=render.INK, font=render.font(18))
        y += 44
    if len(due_now) > 5:
        d.text((px + 16, y + 4), t["more"].format(n=len(due_now) - 5), fill=render.MUTED, font=render.font(17))
    d.text((56, H - 70), t["foot"], fill=render.MUTED, font=render.font(17))

    out = Path("out") / f"sim_height_{lang}.png"
    img.save(out)
    print(out, {"over": len(over), "due_by_week": counts})


if __name__ == "__main__":
    main()
