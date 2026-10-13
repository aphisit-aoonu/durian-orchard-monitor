"""Shared drawing style for annotated photos and video frames."""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = r"C:\Windows\Fonts\LeelawUI.ttf"
FONT_BOLD = r"C:\Windows\Fonts\LeelaUIb.ttf"

ACCENT = (255, 196, 0)      # fruit boxes
INK = (20, 24, 28)
PAPER = (247, 248, 246)
CARD = (255, 255, 255)
MUTED = (110, 118, 125)
GREEN = (46, 160, 67)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_PATH, size)


def corner_box(d: ImageDraw.ImageDraw, box, color=ACCENT, width: int = 3, frac: float = 0.28) -> None:
    """Box drawn as four corner brackets plus a thin outline: reads well on busy foliage."""
    x1, y1, x2, y2 = box
    lx, ly = (x2 - x1) * frac, (y2 - y1) * frac
    d.rectangle(box, outline=color + (110,) if len(color) == 3 else color, width=1)
    for (ax, ay, bx, by) in [
        (x1, y1, x1 + lx, y1), (x1, y1, x1, y1 + ly),
        (x2, y1, x2 - lx, y1), (x2, y1, x2, y1 + ly),
        (x1, y2, x1 + lx, y2), (x1, y2, x1, y2 - ly),
        (x2, y2, x2 - lx, y2), (x2, y2, x2, y2 - ly),
    ]:
        d.line([(ax, ay), (bx, by)], fill=color, width=width)


def tag(d: ImageDraw.ImageDraw, xy, text: str, size: int = 16, bg=ACCENT, fg=INK, pad: int = 5) -> None:
    f = font(size, bold=True)
    x, y = xy
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y - size - pad * 2, x + w + pad * 2, y], radius=4, fill=bg)
    d.text((x + pad, y - size - pad * 1.6), text, fill=fg, font=f)


def pill(d: ImageDraw.ImageDraw, xy, text: str, size: int = 22, bg=(0, 0, 0, 170), fg=(255, 255, 255), pad: int = 10) -> int:
    """Rounded label; returns its width."""
    f = font(size, bold=True)
    x, y = xy
    w = d.textlength(text, font=f) + pad * 2
    d.rounded_rectangle([x, y, x + w, y + size + pad * 1.6], radius=(size + pad) // 2, fill=bg)
    d.text((x + pad, y + pad * 0.5), text, fill=fg, font=f)
    return int(w)


def annotate(img: Image.Image, dets, label_fn=None, scale: float = 1.0) -> Image.Image:
    """Draw detections on an RGB image. label_fn(i, box, score) -> str or None."""
    base = img.convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = max(2, int(3 * scale))
    for i, (box, score) in enumerate(dets):
        corner_box(d, [v * scale for v in box], ACCENT, width=w)
        text = label_fn(i, box, score) if label_fn else None
        if text:
            tag(d, (box[0] * scale, box[1] * scale - 2), text, size=max(12, int(15 * scale)))
    return Image.alpha_composite(base, layer).convert("RGB")
