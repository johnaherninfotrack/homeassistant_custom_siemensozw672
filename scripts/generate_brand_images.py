"""Generate brand images for the siemens_ozw672 custom integration.

Outputs to brand/ following the HA 2026.3+ bundled-brand convention:
    icon.png       256x256
    icon@2x.png    512x512
    logo.png       shortest side 128-256
    logo@2x.png    shortest side 256-512
plus dark_ variants.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "custom_components", "siemens_ozw672", "brand")
os.makedirs(OUT, exist_ok=True)

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
NARROW = "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"

# Deliberately not Siemens' petrol brand colour - this is an original mark for a
# community integration, not an imitation of the manufacturer's identity.
TEAL_A = (13, 115, 119)
TEAL_B = (7, 74, 82)
WHITE = (255, 255, 255, 255)
DARK_BG_A = (22, 30, 36)
DARK_BG_B = (12, 18, 22)


def _fit(draw, text, font_path, target_w, start):
    """Largest font size whose rendered width fits target_w."""
    size = start
    while size > 8:
        f = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=f) <= target_w:
            return f
        size -= 2
    return ImageFont.truetype(font_path, 8)


def _vgrad(size, top, bottom):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def _rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def _flame_points(cx, cy, w, h):
    """Outline of a flame: rounded belly, drawn-out pointed tip."""
    import math

    pts = []
    steps = 96
    for i in range(steps + 1):
        t = i / steps
        ang = math.pi * 2 * t - math.pi / 2  # start at the tip
        # Radius shrinks sharply toward the top to form a point, and swells low down.
        v = (1 - math.cos(ang + math.pi / 2)) / 2  # 0 at tip -> 1 at base
        rx = (w / 2) * (v ** 0.62)
        ry = h / 2
        x = cx + math.sin(ang + math.pi / 2) * rx
        y = cy - math.cos(ang + math.pi / 2) * ry * (1 if v < 0.5 else 1)
        pts.append((x, y))
    return pts


def draw_flame(d, cx, cy, w, h, fill, inner=None):
    """Flame glyph - the OZW672 is a heating controller."""
    d.polygon(_flame_points(cx, cy, w, h), fill=fill)
    if inner is not None:
        # Inner flame, sitting low and small, reads as heat rather than as an eye.
        d.polygon(_flame_points(cx, cy + h * 0.16, w * 0.44, h * 0.50), fill=inner)


def make_icon(px, dark=False):
    """Square app icon: the model number alone, with a flame accent.

    The icon deliberately carries only "OZW672" and no manufacturer wordmark.
    A brand name on a logo tile is the case where implied endorsement is
    easiest to argue; a model number identifies the hardware without that.
    The wide logo still carries the full name for use in documentation.
    """
    S = px * 4  # supersample
    top, bottom = (DARK_BG_A, DARK_BG_B) if dark else (TEAL_A, TEAL_B)
    bg = _vgrad((S, S), top, bottom).convert("RGBA")
    bg.putalpha(_rounded_mask((S, S), int(S * 0.22)))

    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    draw_flame(d, S * 0.5, S * 0.34, S * 0.27, S * 0.34, (255, 255, 255, 235), inner=(top[0], top[1], top[2], 255))

    f_big = _fit(d, "OZW672", BOLD, S * 0.82, int(S * 0.34))
    d.text((S * 0.5, S * 0.70), "OZW672", font=f_big, fill=WHITE, anchor="mm")

    out = Image.alpha_composite(bg, layer).resize((px, px), Image.LANCZOS)
    name = f"{'dark_' if dark else ''}icon{'@2x' if px == 512 else ''}.png"
    out.save(os.path.join(OUT, name), "PNG", optimize=True)
    return name


def make_logo(h, dark=False):
    """Wide logo: flame mark + model number, transparent background.

    Carries no manufacturer wordmark, matching the icon. See make_icon for
    the reasoning.
    """
    S = h * 4
    W = int(S * 2.6)
    img = Image.new("RGBA", (W, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    fg = (255, 255, 255, 255) if dark else (17, 24, 28, 255)
    accent = (24, 160, 165, 255) if dark else TEAL_A + (255,)

    draw_flame(d, S * 0.30, S * 0.5, S * 0.44, S * 0.74, accent, inner=(255, 255, 255, 0))

    f_big = _fit(d, "OZW672", BOLD, W - S * 0.72, int(S * 0.60))
    d.text((S * 0.62, S * 0.52), "OZW672", font=f_big, fill=fg, anchor="lm")

    out = img.resize((W // 4, h), Image.LANCZOS)
    name = f"{'dark_' if dark else ''}logo{'@2x' if h == 256 else ''}.png"
    out.save(os.path.join(OUT, name), "PNG", optimize=True)
    return name


if __name__ == "__main__":
    made = []
    for dark in (False, True):
        made.append(make_icon(256, dark))
        made.append(make_icon(512, dark))
        made.append(make_logo(128, dark))
        made.append(make_logo(256, dark))
    for n in sorted(made):
        p = os.path.join(OUT, n)
        print(f"{n:24} {Image.open(p).size!s:12} {os.path.getsize(p)/1024:6.1f} KB")
