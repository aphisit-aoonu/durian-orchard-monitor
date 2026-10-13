"""Side view, to scale: a tree topped at 6 m that a short pole reaches, next to an old 12 m tree that it does not.

Usage: python -m scripts.sim_catch [en|th]   -> out/sim_catch_<lang>.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from durian import plan_draw as pd
from durian import render
from durian.catch import Catch, load_moment_nm, pole_length
from durian.growth import REACH_M

W, H = 1920, 1080
MASS_KG = 3.0
LOW_TREE_M, LOW_FRUIT_M, LOW_OFFSET_M = 6.0, 4.0, 3.0     # the fruit drawn on the topped tree
FAR_FRUIT_M, FAR_OFFSET_M = 5.0, 5.0                      # longest reach the orchard plan asks for
TALL_TREE_M, TALL_FRUIT_M = 12.0, 10.0
RED, AMBER, GREEN = (214, 69, 65), (232, 137, 12), (46, 160, 67)

BAG = Catch("bag", 0.3, 0.1)
DROP_LOW = Catch("drop_low", LOW_FRUIT_M, 0.02)
DROP_TALL = Catch("drop_tall", TALL_FRUIT_M, 0.02)

TEXT = {
    "en": {"title": "Getting the fruit down", "badge": "SIMULATION",
           "sub": f"A {MASS_KG:.0f} kg durian. Drawn to scale. Speeds are plain physics, v = √(2gh).",
           "low": f"Tree topped at {LOW_TREE_M:.0f} m", "tall": f"Old tree, {TALL_TREE_M:.0f} m",
           "limit": f"{REACH_M:.0f} m: pole reach", "out": "out of reach", "bag": "bag",
           "cards": [
               ("Topped tree: bag on the cutter head",
                "Same idea as a fruit-picking pole with a basket, sized for a durian. The pole then lowers it.",
                [(f"{BAG.impact_speed():.1f}", "m/s into the bag"),
                 (f"{pole_length(LOW_FRUIT_M, LOW_OFFSET_M):.1f}", "m of pole, as drawn"),
                 (f"{pole_length(FAR_FRUIT_M, FAR_OFFSET_M):.1f}", "m of pole, longest in the plan")]),
               (f"Same fruit, just dropped from {LOW_FRUIT_M:.0f} m",
                "Why it is caught at the stem and not left to fall.",
                [(f"{DROP_LOW.impact_speed():.1f}", "m/s at the ground"),
                 (f"{DROP_LOW.energy_j(MASS_KG):.0f}", "J of energy")]),
               (f"Old tree: fruit at {TALL_FRUIT_M:.0f} m",
                "I found no machine that harvests durian at this height, so none is claimed here.",
                [(f"{DROP_TALL.impact_speed():.1f}", "m/s if dropped"),
                 (f"{pole_length(TALL_FRUIT_M, FAR_OFFSET_M):.1f}", "m of pole it would take")])],
           "chart": "Speed when it stops falling",
           "bars": ["Bag at the stem", f"Dropped {LOW_FRUIT_M:.0f} m", f"Dropped {TALL_FRUIT_M:.0f} m"],
           "pick": "Top trees at 6 m so a short pole reaches. Tall old trees stay with the climbing crew.",
           "foot": f"Holding {MASS_KG:.0f} kg {FAR_OFFSET_M:.0f} m to the side puts {load_moment_nm(MASS_KG, FAR_OFFSET_M):.0f} N·m on the cart; the cart is not designed yet. "
                   "Bruise limits were not measured.",
           "m": "m"},
    "th": {"title": "เอาลูกลงจากต้น", "badge": "ภาพจำลอง",
           "sub": f"ทุเรียน {MASS_KG:.0f} กก. · วาดตามสเกลจริง · ความเร็วคำนวณตามฟิสิกส์ v = √(2gh)",
           "low": f"ต้นที่ตัดยอดไว้ {LOW_TREE_M:.0f} ม.", "tall": f"ต้นเก่า สูง {TALL_TREE_M:.0f} ม.",
           "limit": f"{REACH_M:.0f} ม.: ระยะที่เสาเอื้อมถึง", "out": "เอื้อมไม่ถึง", "bag": "ถุงรับ",
           "cards": [
               ("ต้นตัดยอด: ถุงรับที่หัวตัด",
                "หลักเดียวกับตะกร้อสอยผลไม้ ขยายให้รับทุเรียนได้ แล้วเสาหย่อนลูกลงมา",
                [(f"{BAG.impact_speed():.1f}", "ม./วิ ตอนลงถุง"),
                 (f"{pole_length(LOW_FRUIT_M, LOW_OFFSET_M):.1f}", "ม. ความยาวเสาในรูป"),
                 (f"{pole_length(FAR_FRUIT_M, FAR_OFFSET_M):.1f}", "ม. เสายาวสุดในแปลนนี้")]),
               (f"ลูกเดียวกัน ถ้าปล่อยตกจาก {LOW_FRUIT_M:.0f} ม.",
                "เหตุผลที่ต้องรับตั้งแต่ขั้ว ไม่ปล่อยให้ตก",
                [(f"{DROP_LOW.impact_speed():.1f}", "ม./วิ ตอนถึงพื้น"),
                 (f"{DROP_LOW.energy_j(MASS_KG):.0f}", "จูล")]),
               (f"ต้นเก่า: ลูกอยู่ที่ {TALL_FRUIT_M:.0f} ม.",
                "ค้นแล้วยังไม่เจอเครื่องที่เก็บทุเรียนสูงระดับนี้ได้จริง จึงไม่อ้างว่าทำได้",
                [(f"{DROP_TALL.impact_speed():.1f}", "ม./วิ ถ้าปล่อยตก"),
                 (f"{pole_length(TALL_FRUIT_M, FAR_OFFSET_M):.1f}", "ม. เสาที่ต้องใช้")])],
           "chart": "ความเร็วตอนลูกหยุด",
           "bars": ["ถุงที่ขั้ว", f"ตก {LOW_FRUIT_M:.0f} ม.", f"ตก {TALL_FRUIT_M:.0f} ม."],
           "pick": "ตัดยอดคุมต้นไว้ 6 ม. ให้เสาสั้นเอื้อมถึง · ต้นเก่าที่สูงยังใช้ทีมมือตัดปีน",
           "foot": f"ถือลูก {MASS_KG:.0f} กก. ยื่นออกข้าง {FAR_OFFSET_M:.0f} ม. เกิดโมเมนต์ {load_moment_nm(MASS_KG, FAR_OFFSET_M):.0f} นิวตันเมตรที่รถ ยังไม่ได้ออกแบบตัวรถ · "
                   "ยังไม่ได้วัดว่าทุเรียนช้ำที่แรงเท่าไหร่",
           "m": "ม."},
}


def fruit(d, x, y, r=11):
    d.ellipse([x - r, y - r * 1.2, x + r, y + r * 1.2], fill=(150, 160, 60), outline=(90, 100, 30), width=2)


def side_view(d: ImageDraw.ImageDraw, box, t) -> None:
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=16, fill=render.CARD)
    gy = y1 - 60
    s = (gy - (y0 + 70)) / TALL_TREE_M                    # px per metre, same for both trees
    ym = lambda m: gy - m * s
    for m in range(0, int(TALL_TREE_M) + 1, 2):
        d.line([(x0 + 50, ym(m)), (x0 + 58, ym(m))], fill=render.MUTED, width=2)
        d.text((x0 + 16, ym(m) - 10), f"{m}", fill=render.MUTED, font=render.font(15))
    d.text((x0 + 14, y0 + 40), t["m"], fill=render.MUTED, font=render.font(15))
    d.line([(x0 + 60, gy), (x1 - 20, gy)], fill=(170, 160, 140), width=3)

    # old tall tree on the left
    tx = x0 + 250
    d.rectangle([tx - 13, ym(6), tx + 13, gy], fill=(110, 80, 50))
    d.ellipse([tx - 3.4 * s, ym(TALL_TREE_M), tx + 3.4 * s, ym(5)], fill=(104, 140, 110))
    fx, fy = tx + 1.6 * s, ym(TALL_FRUIT_M)
    fruit(d, fx, fy)
    render.pill(d, (fx + 18, fy - 16), t["out"], size=15, bg=RED + (235,), pad=7)
    d.text((tx - d.textlength(t["tall"], font=render.font(18, True)) / 2, gy + 14), t["tall"], fill=render.INK,
           font=render.font(18, True))

    # topped tree, cart on the rail beside it, pole to the fruit, bag under the cutter
    lx = x0 + 640
    d.rectangle([lx - 10, ym(2.5), lx + 10, gy], fill=(110, 80, 50))
    d.ellipse([lx - 2.8 * s, ym(LOW_TREE_M), lx + 2.8 * s, ym(1.8)], fill=pd.CANOPY)
    cart_x = lx + 4.5 * s
    px, py = cart_x - LOW_OFFSET_M * s, ym(LOW_FRUIT_M)
    d.line([(cart_x - 70, gy - 8), (cart_x + 80, gy - 8)], fill=pd.RAIL, width=5)
    d.rounded_rectangle([cart_x - 45, ym(1.0), cart_x + 45, gy - 10], radius=6, fill=(255, 196, 0), outline=render.INK, width=2)
    d.line([(cart_x, ym(1.0)), (px + 14, py - 16)], fill=render.INK, width=4)
    d.arc([px - 18, py - 6, px + 18, py + 40], 0, 180, fill=GREEN, width=5)
    fruit(d, px, py)
    bag_w = d.textlength(t["bag"], font=render.font(15, True)) + 14
    render.pill(d, (px - 24 - bag_w, py + 14), t["bag"], size=15, bg=(255, 255, 255, 235), fg=GREEN, pad=7)
    d.text((lx - d.textlength(t["low"], font=render.font(18, True)) / 2, gy + 14), t["low"], fill=render.INK,
           font=render.font(18, True))

    # reach limit across both trees
    for x in range(int(x0 + 64), int(x1 - 24), 18):
        d.line([(x, ym(REACH_M)), (x + 10, ym(REACH_M))], fill=AMBER, width=3)
    render.pill(d, (x1 - 30 - d.textlength(t["limit"], font=render.font(15, True)) - 14, ym(REACH_M) - 34), t["limit"],
                size=15, bg=AMBER + (240,), pad=7)


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    img = Image.new("RGB", (W, H), render.PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = d.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(d, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    d.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(22))

    side_view(d, (56, 170, 1090, 960), t)

    px, py, ch = 1120, 170, 172
    colors = [GREEN, AMBER, RED]
    for k, (name, note, stats) in enumerate(t["cards"]):
        y = py + k * (ch + 12)
        d.rounded_rectangle([px, y, W - 56, y + ch], radius=16, fill=render.CARD)
        d.rounded_rectangle([px, y, px + 10, y + ch], radius=5, fill=colors[k])
        d.text((px + 28, y + 14), name, fill=render.INK, font=render.font(24, True))
        d.text((px + 28, y + 50), note, fill=render.MUTED, font=render.font(15))
        for j, (num, label) in enumerate(stats):
            sx = px + 28 + j * 232
            d.text((sx, y + 82), num, fill=colors[k], font=render.font(40, True))
            d.text((sx, y + 134), label, fill=render.MUTED, font=render.font(15))

    y = py + 3 * (ch + 12) + 4
    d.text((px, y), t["chart"], fill=render.INK, font=render.font(20, True))
    speeds = [BAG.impact_speed(), DROP_LOW.impact_speed(), DROP_TALL.impact_speed()]
    for k, v in enumerate(speeds):
        by = y + 38 + k * 34
        bw = (W - 56 - px - 250) * v / max(speeds)
        d.rounded_rectangle([px + 180, by, px + 180 + bw, by + 22], radius=6, fill=colors[k])
        d.text((px, by - 1), t["bars"][k], fill=render.MUTED, font=render.font(16))
        d.text((px + 188 + bw, by - 1), f"{v:.1f}", fill=render.INK, font=render.font(16, True))
    render.pill(d, (px, y + 150), t["pick"], size=17, bg=(46, 160, 67, 235))
    d.text((56, H - 70), t["foot"], fill=render.MUTED, font=render.font(17))

    out = Path("out") / f"sim_catch_{lang}.png"
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
