#!/usr/bin/env python3
"""
Generador de imagenes placeholder elegantes para Pedro Gomez Peluqueros.
No usa fotografia real: dibuja ilustraciones de linea minimalistas (tijeras,
peines, ondas de cabello, sillon de peluqueria...) sobre fondos degradados
en la paleta de marca (crema / antracita / dorado). Pensado para sustituirse
por fotografia real del salon cuando este disponible.

Uso: python3 generate-placeholders.py
Salida: ../assets/img/*.webp
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)

# Paleta de marca
CREAM      = (250, 246, 238)
CREAM_2    = (241, 232, 214)
PAPER      = (255, 253, 248)
INK        = (26, 25, 23)
INK_2      = (38, 36, 33)
GOLD       = (176, 141, 87)
GOLD_SOFT  = (196, 168, 122)

SS = 3  # supersample factor for smooth anti-aliased lines


def new_canvas(w, h, bg):
    return Image.new("RGB", (w * SS, h * SS), bg)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(im, top, bottom):
    w, h = im.size
    draw = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        draw.line([(0, y), (w, y)], fill=lerp(top, bottom, t))


def radial_glow(im, cx, cy, radius, color, max_alpha=90):
    w, h = im.size
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    steps = 60
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(max_alpha * (1 - i / steps) ** 1.6)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius / 6))
    im.paste(Image.alpha_composite(im.convert("RGBA"), glow).convert("RGB"), (0, 0))


def add_grain(im, amount=6):
    w, h = im.size
    noise = Image.effect_noise((w, h), amount).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(im, noise_rgb, 0.035)


def add_vignette(im, strength=70):
    w, h = im.size
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-w * 0.25, -h * 0.25, w * 1.25, h * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(w * 0.08))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(im, dark, vig.point(lambda p: 255 - int(strength * (255 - p) / 255)))


def fine_line(draw, pts, color, width, close=False):
    if close:
        pts = pts + [pts[0]]
    draw.line(pts, fill=color, width=width, joint="curve")


def motif_scissors(draw, cx, cy, s, color, width):
    # Two blades crossing, minimalist
    a = math.radians(28)
    L = s * 0.9
    for sign in (-1, 1):
        x2 = cx + sign * L * math.cos(a)
        y2 = cy - L * math.sin(a)
        fine_line(draw, [(cx, cy + s * 0.35), (x2, y2)], color, width)
        draw.ellipse([cx + sign * s * 0.18 - s * 0.16, cy + s * 0.35 - s * 0.16,
                      cx + sign * s * 0.18 + s * 0.16, cy + s * 0.35 + s * 0.16], outline=color, width=width)
    draw.ellipse([cx - s * 0.05, cy + s * 0.28, cx + s * 0.05, cy + s * 0.38], fill=color)


def motif_comb(draw, cx, cy, s, color, width):
    top = cy - s * 0.5
    bottom = cy - s * 0.15
    fine_line(draw, [(cx - s * 0.55, top), (cx + s * 0.55, top)], color, width)
    fine_line(draw, [(cx - s * 0.55, top), (cx - s * 0.55, bottom + s*0.25)], color, width)
    fine_line(draw, [(cx + s * 0.55, top), (cx + s * 0.55, bottom + s*0.25)], color, width)
    fine_line(draw, [(cx - s * 0.55, bottom + s*0.25), (cx + s * 0.55, bottom + s*0.25)], color, width)
    teeth = 12
    for i in range(teeth):
        x = cx - s * 0.5 + i * (s / (teeth - 1))
        fine_line(draw, [(x, bottom + s*0.25), (x, cy + s * 0.55)], color, max(1, width - 1))


def motif_wave_hair(draw, cx, cy, s, color, width, strands=5):
    for i in range(strands):
        off = (i - strands / 2) * s * 0.22
        pts = []
        for t in range(0, 21):
            tt = t / 20
            x = cx + off + math.sin(tt * math.pi * 1.6 + i) * s * 0.16
            y = cy - s * 0.7 + tt * s * 1.4
            pts.append((x, y))
        fine_line(draw, pts, color, width)


def motif_chair(draw, cx, cy, s, color, width):
    # minimalist salon chair silhouette (side profile)
    fine_line(draw, [(cx - s*0.5, cy + s*0.5), (cx + s*0.5, cy + s*0.5)], color, width)  # base
    fine_line(draw, [(cx - s*0.15, cy + s*0.5), (cx - s*0.15, cy + s*0.15)], color, width)  # stem
    fine_line(draw, [(cx - s*0.45, cy + s*0.15), (cx + s*0.2, cy + s*0.15)], color, width)  # seat
    fine_line(draw, [(cx - s*0.45, cy + s*0.15), (cx - s*0.45, cy - s*0.55)], color, width)  # backrest side
    fine_line(draw, [(cx - s*0.45, cy - s*0.55), (cx - s*0.02, cy - s*0.6)], color, width)  # backrest top
    fine_line(draw, [(cx - s*0.02, cy - s*0.6), (cx - s*0.02, cy + s*0.15)], color, width)
    draw.ellipse([cx + s*0.1, cy - s*0.15, cx + s*0.42, cy + s*0.15], outline=color, width=width)  # mirror-ish circle


def motif_brush_strokes(draw, cx, cy, s, color, width, n=4):
    for i in range(n):
        off = (i - n / 2) * s * 0.3
        pts = []
        for t in range(0, 14):
            tt = t / 13
            x = cx - s * 0.6 + tt * s * 1.2
            y = cy + off + math.sin(tt * math.pi + i * 0.7) * s * 0.06
            pts.append((x, y))
        fine_line(draw, pts, color, width)


def motif_dryer(draw, cx, cy, s, color, width):
    fine_line(draw, [(cx - s*0.5, cy - s*0.12), (cx + s*0.05, cy - s*0.12)], color, width)
    fine_line(draw, [(cx - s*0.5, cy + s*0.12), (cx + s*0.05, cy + s*0.12)], color, width)
    fine_line(draw, [(cx - s*0.5, cy - s*0.12), (cx - s*0.5, cy + s*0.12)], color, width)
    fine_line(draw, [(cx + s*0.05, cy - s*0.12), (cx + s*0.3, cy - s*0.45)], color, width)
    fine_line(draw, [(cx + s*0.05, cy + s*0.12), (cx + s*0.3, cy - s*0.45)], color, width)
    fine_line(draw, [(cx + s*0.05, cy - s*0.12), (cx + s*0.35, cy + s*0.35)], color, width)
    fine_line(draw, [(cx + s*0.05, cy + s*0.12), (cx + s*0.55, cy + s*0.42)], color, width)


def motif_updo(draw, cx, cy, s, color, width):
    # simple elegant updo silhouette
    pts = []
    for t in range(0, 40):
        tt = t / 39
        ang = tt * math.pi * 1.85 - math.pi * 0.15
        r = s * 0.45 * (0.4 + 0.6 * tt)
        x = cx + math.cos(ang) * r
        y = cy - s * 0.1 + math.sin(ang) * r * 0.9
        pts.append((x, y))
    fine_line(draw, pts, color, width)
    fine_line(draw, [(cx - s*0.02, cy + s*0.1), (cx - s*0.02, cy + s*0.62)], color, width)
    fine_line(draw, [(cx - s*0.3, cy + s*0.62), (cx + s*0.26, cy + s*0.62)], color, width)


def draw_frame(draw, w, h, color, inset, width):
    draw.rectangle([inset, inset, w - inset, h - inset], outline=color, width=width)


def render(name, w, h, bg_top, bg_bottom, glow_color, line_color, motif_fn, dark=False, motifs=1, size_mul=1.0):
    im = new_canvas(w, h, bg_top)
    vertical_gradient(im, bg_top, bg_bottom)
    im = im.convert("RGB")
    cx, cy = w * SS * 0.5, h * SS * 0.46
    radial_glow(im, cx, cy, min(w, h) * SS * 0.55, glow_color, max_alpha=70 if dark else 55)
    draw = ImageDraw.Draw(im)
    base_s = min(w, h) * SS * 0.16 * size_mul
    lw = max(2, int(SS * 1.6))
    if motifs == 1:
        motif_fn(draw, cx, cy, base_s, line_color, lw)
    else:
        random.seed(hash(name) % 1000)
        spread = min(w, h) * SS * 0.62
        for i in range(motifs):
            ang = (i / motifs) * math.pi * 2 + 0.4
            mx = cx + math.cos(ang) * spread * 0.42
            my = cy + math.sin(ang) * spread * 0.30
            motif_fn(draw, mx, my, base_s * 0.62, line_color, max(2, lw - 1))
    draw_frame(draw, w * SS, h * SS, line_color, int(w * SS * 0.035), max(1, int(SS * 0.9)))
    im = im.resize((w, h), Image.LANCZOS)
    im = add_vignette(im, strength=60 if dark else 28)
    im = add_grain(im, amount=7)
    im.save(OUT / f"{name}.webp", "WEBP", quality=80, method=6)
    print(f"  wrote {name}.webp  {w}x{h}")


def main():
    print("Generando placeholders elegantes...\n")
    print("AVISO: 'about-interior' y las fotos de peinados ya usan fotografia")
    print("real del salon (ver assets/photos/source/). Este script ya NO las")
    print("regenera para no pisarlas — solo repone las categorias que siguen")
    print("en placeholder (corte, coloracion, balayage, herramientas).\n")

    # HERO — amplio, tono oscuro/anthracite para que el overlay del hero funcione
    render("hero", 2000, 1250, (24, 22, 20), (14, 13, 12), GOLD, GOLD_SOFT,
           motif_wave_hair, dark=True, motifs=1, size_mul=3.6)

    # GALERIA — categorias que aun no tienen fotografia real
    render("gallery-corte-1", 1200, 1500, CREAM, CREAM_2, GOLD, INK_2, motif_scissors, size_mul=1.4)
    render("gallery-coloracion-1", 1200, 1500, (250, 244, 233), (238, 226, 202), GOLD, INK_2, motif_brush_strokes, size_mul=1.5)
    render("gallery-balayage-1", 1200, 1200, CREAM_2, (233, 219, 191), GOLD, INK_2, motif_wave_hair, size_mul=1.6)
    render("gallery-herramientas-1", 1200, 1200, (247, 241, 230), CREAM_2, GOLD, INK_2, motif_dryer, size_mul=1.4)

    print("\nListo. Categorias sin foto real repuestas en assets/img/*.webp")


if __name__ == "__main__":
    main()
