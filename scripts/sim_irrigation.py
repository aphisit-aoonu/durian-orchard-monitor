"""Animated 14 days of soil moisture per zone, valves opening only where needed, vs. a fixed schedule.

Usage: python -m scripts.sim_irrigation [en|th]   -> out/sim_irrigation_<lang>.mp4 + .png (last day)
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from durian import irrigation as ir
from durian import plan_draw as pd
from durian import render
from durian.layout import Orchard

W, H, FPS = 1920, 1080, 30
DAYS, SECONDS_PER_DAY = 14, 1.4
ZCOLS, ZROWS = 4, 3

TEXT = {
    "en": {"title": "Soil moisture, zone by zone", "badge": "SIMULATION",
           "sub": "12 zones, one sensor and one valve each. Water goes only where the soil is dry. Weather and sensor data are simulated.",
           "day": "Day", "rain": "rain", "sunny": "sunny", "cloudy": "cloudy",
           "chart": "Moisture per zone (%)", "dry": "open valve below", "wet": "too wet above",
           "smart": "Water only dry zones", "fixed": "Every zone, every 2 days",
           "litres": "litres so far", "wetdays": "zone-days too wet",
           "legend": [("dry", (176, 120, 60)), ("good", (78, 160, 90)), ("wet", (60, 120, 210))],
           "valve": "valve open"},
    "th": {"title": "ความชื้นดินรายโซน", "badge": "ภาพจำลอง",
           "sub": "12 โซน มีเซนเซอร์และวาล์วโซนละ 1 ชุด · รดเฉพาะโซนที่ดินแห้ง · สภาพอากาศและค่าเซนเซอร์เป็นข้อมูลจำลอง",
           "day": "วันที่", "rain": "ฝน", "sunny": "แดดจัด", "cloudy": "ครึ้ม",
           "chart": "ความชื้นแต่ละโซน (%)", "dry": "ต่ำกว่านี้เปิดวาล์ว", "wet": "สูงกว่านี้แฉะเกิน",
           "smart": "รดเฉพาะโซนที่แห้ง", "fixed": "รดทุกโซนทุก 2 วัน",
           "litres": "ลิตร (สะสม)", "wetdays": "โซน-วัน ที่แฉะเกิน",
           "legend": [("แห้ง", (176, 120, 60)), ("พอดี", (78, 160, 90)), ("แฉะ", (60, 120, 210))],
           "valve": "วาล์วเปิด"},
}


def moisture_color(m: float) -> tuple[int, int, int]:
    """Brown when dry, green in range, blue when wet."""
    stops = [(16, (176, 120, 60)), (24, (200, 170, 80)), (29, (78, 160, 90)), (35, (78, 160, 140)), (40, (60, 120, 210))]
    if m <= stops[0][0]:
        return stops[0][1]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if m <= b:
            f = (m - a) / (b - a)
            return tuple(round(x + (y - x) * f) for x, y in zip(ca, cb))
    return stops[-1][1]


def zone_box(o: Orchard, v: pd.View, zr: int, zc: int):
    pad = o.canopy + 1.2
    xs = [o.margin + c * o.tree_gap for c in (2 * zc, 2 * zc + 1)]
    ys = [o.margin + r * o.row_gap for r in (2 * zr, 2 * zr + 1)]
    return (*v(min(xs) - pad, min(ys) - pad), *v(max(xs) + pad, max(ys) + pad))


def main() -> None:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    t = TEXT[lang]
    o = Orchard()
    smart_zones, weather, _ = ir.run(DAYS, smart=True, cols=ZCOLS, rows=ZROWS)
    fixed_zones, _, _ = ir.run(DAYS, smart=False, cols=ZCOLS, rows=ZROWS)
    # litres per day, recomputed from history so the counters can grow over time
    def litres_by_day(smart):
        zones, weather_, _ = ir.make_zones(ZCOLS, ZROWS), ir.make_weather(DAYS), None
        out, total = [], 0.0
        for d, day in enumerate(weather_):
            for z in zones:
                total += ir.step(z, day, smart, scheduled_today=(d % 2 == 0))
            out.append(total)
        return out
    smart_l, fixed_l = litres_by_day(True), litres_by_day(False)

    v = pd.View(56, 190, 9.3)
    base = Image.new("RGB", (W, H), render.PAPER)
    bd = ImageDraw.Draw(base, "RGBA")
    bd.text((56, 40), t["title"], fill=render.INK, font=render.font(46, bold=True))
    tw = bd.textlength(t["title"], font=render.font(46, bold=True))
    render.pill(bd, (56 + tw + 20, 52), t["badge"], size=20, bg=(214, 69, 65, 255))
    bd.text((56, 104), t["sub"], fill=render.MUTED, font=render.font(21))
    pd.draw_ground(bd, o, v)

    out = Path("out") / f"sim_irrigation_{lang}.mp4"
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    per_day = int(SECONDS_PER_DAY * FPS)
    px, cx0, cy0, cw, chh = 1150, 1150, 330, W - 56 - 1150, 330
    last = None
    for d in range(DAYS):
        day = weather[d]
        for f in range(per_day):
            img = base.copy()
            dd = ImageDraw.Draw(img, "RGBA")
            boxes = [zone_box(o, v, *divmod(k, ZCOLS)) for k in range(len(smart_zones))]
            for box, z in zip(boxes, smart_zones):
                dd.rounded_rectangle(box, radius=10, fill=moisture_color(z.history[d]) + (150,), outline=(255, 255, 255), width=2)
            pd.draw_trees(dd, o, v, labels=False)
            # labels on top of the trees so they stay readable
            for box, z in zip(boxes, smart_zones):
                cxm = (box[0] + box[2]) / 2
                render.pill(dd, (cxm - 34, (box[1] + box[3]) / 2 - 16), f"{z.history[d]:.0f}%", size=18,
                            bg=moisture_color(z.history[d]) + (235,), pad=8)
                if z.watered[d]:
                    render.pill(dd, (box[0] + 6, box[1] + 6), t["valve"], size=13, bg=(40, 110, 220, 235), pad=6)
            if day.rain_mm and f % 6 < 4:
                rng = np.random.default_rng(d * 100 + f)
                for x, y in rng.uniform([90, 190], [1080, 820], size=(160, 2)):
                    dd.line([(x, y), (x - 4, y + 14)], fill=(90, 140, 220, 160), width=2)
            # header: day + weather
            label = f"{t['rain']} {day.rain_mm:.0f} mm" if day.rain_mm else (t["sunny"] if day.sun > 0.8 else t["cloudy"])
            dd.text((px, 172), f"{t['day']} {d + 1} / {DAYS}", fill=render.INK, font=render.font(40, True))
            render.pill(dd, (px + 260, 182), label, size=20,
                        bg=(60, 120, 210, 240) if day.rain_mm else (232, 160, 30, 240))
            dd.text((px, 250), t["chart"], fill=render.INK, font=render.font(20, True))
            # chart
            dd.rounded_rectangle([cx0, cy0 - 20, cx0 + cw, cy0 + chh + 20], radius=12, fill=render.CARD)
            ylo, yhi = 14, 42
            yof = lambda m: cy0 + chh - (m - ylo) / (yhi - ylo) * chh
            xof = lambda i: cx0 + 50 + i * (cw - 80) / (DAYS - 1)
            for lvl, col, txt in [(ir.DRY_BELOW, (176, 120, 60), t["dry"]), (ir.TOO_WET, (60, 120, 210), t["wet"])]:
                dd.line([(cx0 + 50, yof(lvl)), (cx0 + cw - 30, yof(lvl))], fill=col + (200,), width=2)
                dd.text((cx0 + cw - 30 - dd.textlength(txt, font=render.font(13)), yof(lvl) - 18), txt, fill=col,
                        font=render.font(13))
            for m in (20, 30, 40):
                dd.text((cx0 + 12, yof(m) - 9), str(m), fill=render.MUTED, font=render.font(13))
            for z in smart_zones:
                pts = [(xof(i), yof(m)) for i, m in enumerate(z.history[: d + 1])]
                if len(pts) > 1:
                    dd.line(pts, fill=moisture_color(z.history[d]) + (220,), width=2)
            # comparison cards
            for k, (name, litres, zones) in enumerate([(t["smart"], smart_l[d], smart_zones),
                                                      (t["fixed"], fixed_l[d], fixed_zones)]):
                x = px + k * ((cw - 14) // 2 + 14)
                y = 720
                col = (46, 160, 67) if k == 0 else (110, 118, 125)
                dd.rounded_rectangle([x, y, x + (cw - 14) // 2, y + 190], radius=14, fill=render.CARD)
                dd.rounded_rectangle([x, y, x + 8, y + 190], radius=4, fill=col)
                dd.text((x + 22, y + 14), name, fill=render.INK, font=render.font(19, True))
                dd.text((x + 22, y + 52), f"{litres:,.0f}", fill=col, font=render.font(36, True))
                dd.text((x + 22, y + 98), t["litres"], fill=render.MUTED, font=render.font(15))
                wet = sum(1 for z in zones for m in z.history[: d + 1] if m > ir.TOO_WET)
                dd.text((x + 22, y + 124), str(wet), fill=col, font=render.font(28, True))
                dd.text((x + 22, y + 162), t["wetdays"], fill=render.MUTED, font=render.font(15))
            lx = 92
            for name, col in t["legend"]:
                dd.rounded_rectangle([lx, 850, lx + 22, 868], radius=4, fill=col)
                dd.text((lx + 30, 846), name, fill=render.INK, font=render.font(17))
                lx += 60 + dd.textlength(name, font=render.font(17))
            ff.stdin.write(np.asarray(img).tobytes())
            last = img
    for _ in range(FPS * 2):
        ff.stdin.write(np.asarray(last).tobytes())
    ff.stdin.close()
    ff.wait()
    last.save(out.with_suffix(".png"))
    saved = 1 - smart_l[-1] / fixed_l[-1]
    print(f"{out}: smart {smart_l[-1]:,.0f} L vs fixed {fixed_l[-1]:,.0f} L ({saved:.0%} less)")


if __name__ == "__main__":
    main()
