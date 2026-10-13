"""Side view, to scale, of three ways to catch a durian cut 10 m up, with the impact numbers.

Usage: python -m scripts.sim_catch [en|th]   -> out/sim_catch_<lang>.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from durian import plan_draw as pd
from durian import render
from durian.catch import scenarios

W, H = 1920, 1080
TREE_M, FRUIT_M, NET_M, MASS_KG = 12.0, 10.0, 2.0, 3.0
COLORS = {"ground": (214, 69, 65), "net": (232, 137, 12), "bag": (46, 160, 67)}

TEXT = {
    "en": {"title": "Catching fruit from a 12 m tree", "badge": "SIMULATION",
           "sub": f"A {MASS_KG:.0f} kg durian cut {FRUIT_M:.0f} m up. Plain physics: speed at impact and how hard it is stopped.",
           "names": {"ground": "Let it drop", "net": "Net under the canopy", "bag": "Bag on the cutter + braked tube"},
           "notes": {"ground": "how most damage happens", "net": f"net {NET_M:.0f} m above ground, 0.5 m sag",
                     "bag": "fruit falls 0.3 m into the bag, slides down at 1 m/s"},
           "speed": "m/s at impact", "g": "average g while stopping", "energy": "J of energy",
           "chart": "Impact speed", "pick": "Plan: bag first, net as a backup for fruit that slips",
           "foot": "Durian bruise limits were not measured here. Numbers compare the options; they are not a bruise test.",
           "m": "m", "short": {"ground": "Drop", "net": "Net", "bag": "Bag + tube"}},
    "th": {"title": "รับลูกจากต้นสูง 12 เมตร", "badge": "ภาพจำลอง",
           "sub": f"ทุเรียน {MASS_KG:.0f} กก. ตัดที่ความสูง {FRUIT_M:.0f} ม. · คำนวณตามฟิสิกส์: ความเร็วตอนกระแทก และแรงที่ใช้หยุด",
           "names": {"ground": "ปล่อยตกพื้น", "net": "ตาข่ายใต้ทรงพุ่ม", "bag": "ถุงรับที่หัวตัด + ท่อหน่วง"},
           "notes": {"ground": "สาเหตุหลักที่ลูกเสียหาย", "net": f"ตาข่ายสูงจากพื้น {NET_M:.0f} ม. ยุบได้ 0.5 ม.",
                     "bag": "ลูกตกลงถุงแค่ 0.3 ม. แล้วไหลลงท่อ 1 ม./วิ"},
           "speed": "ม./วิ ตอนกระแทก", "g": "เท่าของแรงโน้มถ่วง (เฉลี่ย)", "energy": "จูล",
           "chart": "ความเร็วตอนกระแทก", "pick": "แผน: ใช้ถุงที่หัวตัดเป็นหลัก ตาข่ายสำรองไว้รับลูกที่หลุด",
           "foot": "ยังไม่ได้วัดว่าทุเรียนช้ำที่แรงเท่าไหร่ ตัวเลขนี้ใช้เทียบวิธี ไม่ใช่ผลทดสอบความช้ำ",
           "m": "ม.", "short": {"ground": "ตกพื้น", "net": "ตาข่าย", "bag": "ถุง + ท่อ"}},
}


def side_view(d: ImageDraw.ImageDraw, box, t) -> None:
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=16, fill=render.CARD)
    gy = y1 - 50
    s = (gy - (y0 + 40)) / TREE_M                       # px per metre
    ym = lambda m: gy - m * s
    # height axis
    for m in range(0, int(TREE_M) + 1, 2):
        d.line([(x0 + 50, ym(m)), (x0 + 58, ym(m))], fill=render.MUTED, width=2)
        d.text((x0 + 16, ym(m) - 10), f"{m}", fill=render.MUTED, font=render.font(15))
    d.text((x0 + 14, y0 + 8), t["m"], fill=render.MUTED, font=render.font(15))
    d.line([(x0 + 60, gy), (x1 - 20, gy)], fill=(170, 160, 140), width=3)
    tx = x0 + 230
    d.rectangle([tx - 12, ym(6), tx + 12, gy], fill=(110, 80, 50))
    d.ellipse([tx - 170, ym(TREE_M), tx + 170, ym(5.5)], fill=pd.CANOPY)
    fx, fy = tx + 110, ym(FRUIT_M)
    d.ellipse([fx - 12, fy - 14, fx + 12, fy + 14], fill=(150, 160, 60), outline=(90, 100, 30), width=2)
    # 1) drop straight down
    d.line([(fx - 30, fy + 16), (fx - 30, gy)], fill=COLORS["ground"], width=3)
    d.text((fx - 30 - 6, gy + 8), "1", fill=COLORS["ground"], font=render.font(18, True))
    # 2) net at NET_M
    nx0, nx1 = tx - 140, tx + 150
    d.line([(nx0, ym(NET_M)), ((nx0 + nx1) / 2, ym(NET_M) + 0.5 * s), (nx1, ym(NET_M))], fill=COLORS["net"], width=4)
    d.line([(fx, fy + 16), (fx, ym(NET_M) + 0.4 * s)], fill=COLORS["net"], width=3)
    d.text((nx1 + 8, ym(NET_M) - 10), "2", fill=COLORS["net"], font=render.font(18, True))
    # 3) cart on the rail, pole up to the stem, bag, tube back down
    cart_x = x1 - 170
    d.line([(cart_x - 80, gy - 8), (x1 - 30, gy - 8)], fill=pd.RAIL, width=5)
    d.rounded_rectangle([cart_x - 50, gy - 40, cart_x + 50, gy - 10], radius=6, fill=(255, 196, 0), outline=render.INK, width=2)
    top = (fx + 26, fy - 20)
    d.line([(cart_x, gy - 40), top], fill=render.INK, width=4)
    d.ellipse([top[0] - 4, fy - 2, top[0] + 36, fy + 34], outline=COLORS["bag"], width=4)
    tube_start = (top[0] + 16, fy + 34)
    d.line([tube_start, (cart_x - 30, gy - 44)], fill=COLORS["bag"], width=8)
    d.text((top[0] + 42, fy - 4), "3", fill=COLORS["bag"], font=render.font(18, True))


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    img = Image.new("RGB", (W, H), render.PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = d.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(d, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    d.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(22))

    side_view(d, (56, 170, 900, 980), t)

    px, py = 940, 170
    cases = scenarios(FRUIT_M, NET_M)
    ch = 170
    for k, c in enumerate(cases):
        y = py + k * (ch + 14)
        col = COLORS[c.name]
        d.rounded_rectangle([px, y, W - 56, y + ch], radius=16, fill=render.CARD)
        d.rounded_rectangle([px, y, px + 10, y + ch], radius=5, fill=col)
        d.text((px + 30, y + 16), f"{k + 1}. {t['names'][c.name]}", fill=render.INK, font=render.font(26, True))
        d.text((px + 30, y + 54), t["notes"][c.name], fill=render.MUTED, font=render.font(17))
        stats = [(f"{c.impact_speed():.1f}", t["speed"]), (f"{c.peak_g():.0f}", t["g"]),
                 (f"{c.energy_j(MASS_KG):.0f}", t["energy"])]
        for j, (num, label) in enumerate(stats):
            sx = px + 30 + j * 300
            d.text((sx, y + 88), num, fill=col, font=render.font(40, True))
            d.text((sx, y + 138), label, fill=render.MUTED, font=render.font(15))

    y = py + 3 * (ch + 14) + 6
    d.text((px, y), t["chart"], fill=render.INK, font=render.font(20, True))
    vmax = max(c.impact_speed() for c in cases)
    for k, c in enumerate(cases):
        by = y + 38 + k * 34
        bw = (W - 56 - px - 200) * c.impact_speed() / vmax
        d.rounded_rectangle([px + 150, by, px + 150 + bw, by + 22], radius=6, fill=COLORS[c.name])
        d.text((px, by - 1), t["short"][c.name], fill=render.MUTED, font=render.font(16))
        d.text((px + 158 + bw, by - 1), f"{c.impact_speed():.1f}", fill=render.INK, font=render.font(16, True))
    render.pill(d, (px, H - 136), t["pick"], size=19, bg=(46, 160, 67, 235))
    d.text((56, H - 70), t["foot"], fill=render.MUTED, font=render.font(17))

    out = Path("out") / f"sim_catch_{lang}.png"
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
