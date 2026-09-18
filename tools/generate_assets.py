#!/usr/bin/env python3
"""Cereal Pager - asset generator.

Draws every PNG the skin needs, from scratch, at 4x supersample.  Nothing in
assets/ is hand-edited: change this file, re-run it, rebuild the .vlt.

    python tools/generate_assets.py [--out assets]

Requires Pillow (pip install pillow).
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import rgb, rgba  # noqa: E402

S = 4                      # supersample factor
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(HERE, "fonts")

OUT = "assets"


# ---------------------------------------------------------------- canvas ---

def canvas(w, h):
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


WRITTEN = set()


def _record(path):
    WRITTEN.add(os.path.basename(path))
    return path


def save(img, w, h, name):
    out = img.resize((w, h), Image.LANCZOS)
    path = os.path.join(OUT, name + ".png")
    out.save(path, optimize=True)
    return _record(path)


def font(fname, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, fname), size)


STM = "ShareTechMono-Regular.ttf"
JBM = "JetBrainsMono-Medium.ttf"
JBB = "JetBrainsMono-Bold.ttf"


def text_at(d, xy, s, f, fill, anchor="la", spacing=0):
    """Draw text, optionally letter-spaced (Pillow has no tracking)."""
    if not spacing:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += d.textlength(ch, font=f) + spacing


def rr(d, box, r, fill):
    d.rounded_rectangle([c * S for c in box], radius=r * S, fill=fill)


# ---------------------------------------------------------------- glyphs ---
# Every glyph draws centred on (cx, cy) in *unscaled* pixels.

def g_play(d, cx, cy, s, c):
    h = s
    w = s * 0.88
    d.polygon([((cx - w / 2) * S, (cy - h / 2) * S),
               ((cx - w / 2) * S, (cy + h / 2) * S),
               ((cx + w / 2) * S, cy * S)], fill=c)


def g_pause(d, cx, cy, s, c):
    bw = s * 0.30
    gap = s * 0.26
    for sgn in (-1, 1):
        x = cx + sgn * (gap / 2 + bw / 2)
        d.rectangle([(x - bw / 2) * S, (cy - s / 2) * S,
                     (x + bw / 2) * S, (cy + s / 2) * S], fill=c)


def g_stop(d, cx, cy, s, c):
    a = s * 0.82
    rr(d, [cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2], a * 0.10, c)


def g_prev(d, cx, cy, s, c):
    w = s * 0.34
    bar = s * 0.16
    x0 = cx - s * 0.46
    d.rectangle([x0 * S, (cy - s / 2) * S, (x0 + bar) * S, (cy + s / 2) * S], fill=c)
    for i in (0, 1):
        xr = x0 + bar + s * 0.06 + i * (w + s * 0.05)
        d.polygon([((xr + w) * S, (cy - s / 2) * S),
                   ((xr + w) * S, (cy + s / 2) * S),
                   (xr * S, cy * S)], fill=c)


def g_next(d, cx, cy, s, c):
    w = s * 0.34
    bar = s * 0.16
    x1 = cx + s * 0.46
    d.rectangle([(x1 - bar) * S, (cy - s / 2) * S, x1 * S, (cy + s / 2) * S], fill=c)
    for i in (0, 1):
        xl = x1 - bar - s * 0.06 - (i + 1) * w - i * s * 0.05
        d.polygon([(xl * S, (cy - s / 2) * S),
                   (xl * S, (cy + s / 2) * S),
                   ((xl + w) * S, cy * S)], fill=c)


def g_eject(d, cx, cy, s, c):
    d.polygon([((cx - s * 0.46) * S, (cy + s * 0.02) * S),
               ((cx + s * 0.46) * S, (cy + s * 0.02) * S),
               (cx * S, (cy - s * 0.46) * S)], fill=c)
    d.rectangle([(cx - s * 0.46) * S, (cy + s * 0.20) * S,
                 (cx + s * 0.46) * S, (cy + s * 0.42) * S], fill=c)


def g_list(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    for i, dy in enumerate((-s * 0.32, 0, s * 0.32)):
        d.rectangle([(cx - s * 0.46) * S, (cy + dy - t / 2) * S,
                     (cx - s * 0.24) * S, (cy + dy + t / 2) * S], fill=c)
        d.rectangle([(cx - s * 0.14) * S, (cy + dy - t / 2) * S,
                     (cx + s * 0.46) * S, (cy + dy + t / 2) * S], fill=c)


def g_fullscreen(d, cx, cy, s, c):
    t = max(1.0, s * 0.12)
    a = s * 0.44
    arm = s * 0.30
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = cx + sx * a
            y = cy + sy * a
            d.rectangle([min(x, x - sx * arm) * S, (y - t / 2) * S,
                         max(x, x - sx * arm) * S, (y + t / 2) * S], fill=c)
            d.rectangle([(x - t / 2) * S, min(y, y - sy * arm) * S,
                         (x + t / 2) * S, max(y, y - sy * arm) * S], fill=c)


def _speaker(d, cx, cy, s, c):
    bx = cx - s * 0.40
    d.rectangle([bx * S, (cy - s * 0.16) * S, (bx + s * 0.22) * S, (cy + s * 0.16) * S], fill=c)
    d.polygon([((bx + s * 0.16) * S, (cy - s * 0.16) * S),
               ((bx + s * 0.16) * S, (cy + s * 0.16) * S),
               ((bx + s * 0.52) * S, (cy + s * 0.44) * S),
               ((bx + s * 0.52) * S, (cy - s * 0.44) * S)], fill=c)


def g_sound_on(d, cx, cy, s, c):
    _speaker(d, cx, cy, s, c)
    t = max(1.0, s * 0.10)
    for i, r in enumerate((s * 0.20, s * 0.36)):
        x = cx + s * 0.20
        d.arc([(x - r) * S, (cy - r) * S, (x + r) * S, (cy + r) * S],
              -58, 58, fill=c, width=int(t * S))


def g_sound_off(d, cx, cy, s, c):
    _speaker(d, cx, cy, s, c)
    t = max(1.0, s * 0.11)
    x = cx + s * 0.30
    r = s * 0.18
    d.line([(x - r) * S, (cy - r) * S, (x + r) * S, (cy + r) * S], fill=c, width=int(t * S))
    d.line([(x - r) * S, (cy + r) * S, (x + r) * S, (cy - r) * S], fill=c, width=int(t * S))


def g_loop(d, cx, cy, s, c, one=False):
    """Two rails and two arrowheads - reads cleanly at 14 px."""
    t = max(1.0, s * 0.11)
    w, h = s * 0.90, s * 0.52
    ah = s * 0.17
    xl, xr = cx - w / 2, cx + w / 2
    yt, yb = cy - h / 2, cy + h / 2
    # top rail, arrowhead on the right, stub turning down on the left
    d.rectangle([xl * S, (yt - t / 2) * S, (xr - ah * 0.9) * S, (yt + t / 2) * S], fill=c)
    d.polygon([((xr - ah) * S, (yt - ah * 0.85) * S),
               ((xr - ah) * S, (yt + ah * 0.85) * S),
               (xr * S, yt * S)], fill=c)
    d.rectangle([xl * S, (yt - t / 2) * S, (xl + t) * S, (yt + h * 0.55) * S], fill=c)
    # bottom rail, arrowhead on the left, stub turning up on the right
    d.rectangle([(xl + ah * 0.9) * S, (yb - t / 2) * S, xr * S, (yb + t / 2) * S], fill=c)
    d.polygon([((xl + ah) * S, (yb - ah * 0.85) * S),
               ((xl + ah) * S, (yb + ah * 0.85) * S),
               (xl * S, yb * S)], fill=c)
    d.rectangle([(xr - t) * S, (yb - h * 0.55) * S, xr * S, (yb + t / 2) * S], fill=c)
    if one:
        d.rectangle([(cx - t / 2) * S, (cy - s * 0.13) * S,
                     (cx + t / 2) * S, (cy + s * 0.13) * S], fill=c)


def g_shuffle(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    for sy in (-1, 1):
        y0 = cy + sy * s * 0.26
        y1 = cy - sy * s * 0.26
        d.line([(cx - s * 0.44) * S, y0 * S, (cx + s * 0.26) * S, y1 * S],
               fill=c, width=int(t * S))
        d.polygon([((cx + s * 0.44) * S, y1 * S),
                   ((cx + s * 0.20) * S, (y1 - s * 0.14) * S),
                   ((cx + s * 0.20) * S, (y1 + s * 0.14) * S)], fill=c)


def g_close(d, cx, cy, s, c):
    t = max(1.0, s * 0.13)
    a = s * 0.36
    d.line([(cx - a) * S, (cy - a) * S, (cx + a) * S, (cy + a) * S], fill=c, width=int(t * S))
    d.line([(cx - a) * S, (cy + a) * S, (cx + a) * S, (cy - a) * S], fill=c, width=int(t * S))


def g_min(d, cx, cy, s, c):
    t = max(1.0, s * 0.13)
    d.rectangle([(cx - s * 0.36) * S, (cy + s * 0.22) * S,
                 (cx + s * 0.36) * S, (cy + s * 0.22 + t) * S], fill=c)


def g_max(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    a = s * 0.34
    d.rectangle([(cx - a) * S, (cy - a) * S, (cx + a) * S, (cy + a) * S],
                outline=c, width=int(t * S))


def g_unmax(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    a = s * 0.28
    o = s * 0.12
    d.rectangle([(cx - a - o) * S, (cy - a + o) * S,
                 (cx + a - o) * S, (cy + a + o) * S], outline=c, width=int(t * S))
    d.rectangle([(cx - a + o) * S, (cy - a - o) * S,
                 (cx + a + o) * S, (cy + a - o) * S], outline=c, width=int(t * S))


def g_chev(d, cx, cy, s, c, up=True):
    t = max(1.0, s * 0.13)
    a = s * 0.34
    k = s * 0.18
    sgn = -1 if up else 1
    d.line([(cx - a) * S, (cy - sgn * k) * S, cx * S, (cy + sgn * k) * S],
           fill=c, width=int(t * S), joint="curve")
    d.line([cx * S, (cy + sgn * k) * S, (cx + a) * S, (cy - sgn * k) * S],
           fill=c, width=int(t * S), joint="curve")


def g_plus(d, cx, cy, s, c):
    t = max(1.0, s * 0.13)
    a = s * 0.34
    d.rectangle([(cx - a) * S, (cy - t / 2) * S, (cx + a) * S, (cy + t / 2) * S], fill=c)
    d.rectangle([(cx - t / 2) * S, (cy - a) * S, (cx + t / 2) * S, (cy + a) * S], fill=c)


def g_minus(d, cx, cy, s, c):
    t = max(1.0, s * 0.13)
    a = s * 0.34
    d.rectangle([(cx - a) * S, (cy - t / 2) * S, (cx + a) * S, (cy + t / 2) * S], fill=c)


def g_sort(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    for i, w in enumerate((0.86, 0.60, 0.34)):
        y = cy + (i - 1) * s * 0.30
        d.rectangle([(cx - s * 0.43) * S, (y - t / 2) * S,
                     (cx - s * 0.43 + s * w) * S, (y + t / 2) * S], fill=c)


def g_eq(d, cx, cy, s, c):
    t = max(1.0, s * 0.11)
    for i, (h, ky) in enumerate(((0.80, -0.10), (0.52, 0.16), (0.68, 0.02))):
        x = cx + (i - 1) * s * 0.30
        d.rectangle([(x - t / 2) * S, (cy - s * h / 2) * S,
                     (x + t / 2) * S, (cy + s * h / 2) * S], fill=c)
        d.rectangle([(x - s * 0.11) * S, (cy + s * ky - t) * S,
                     (x + s * 0.11) * S, (cy + s * ky + t) * S], fill=c)


def g_snapshot(d, cx, cy, s, c):
    t = max(1.0, s * 0.10)
    d.rounded_rectangle([(cx - s * 0.46) * S, (cy - s * 0.30) * S,
                         (cx + s * 0.46) * S, (cy + s * 0.38) * S],
                        radius=s * 0.10 * S, outline=c, width=int(t * S))
    d.rectangle([(cx - s * 0.16) * S, (cy - s * 0.42) * S,
                 (cx + s * 0.16) * S, (cy - s * 0.26) * S], fill=c)
    r = s * 0.17
    d.ellipse([(cx - r) * S, (cy + s * 0.04 - r) * S,
               (cx + r) * S, (cy + s * 0.04 + r) * S], outline=c, width=int(t * S))


# ------------------------------------------------------------- geometry ---
# These numbers are the contract between the artwork and theme.xml.
# Change one, change both. docs/DESIGN.md explains the grid.

W0, H0 = 800, 520          # default main-window size
HEADER_H = 36
DECK_H = 128
SEEK_W = 764               # full-bleed seek bar at the default width
VOL_W = 84

PILL_W, PILL_H = 46, 44    # transport end caps (prev / next)
BAR_W, BAR_H = 76, 21      # transport centre rocker halves
PAD = 32                   # dark pad buttons (open / playlist)
ICON = 26                  # bare icon buttons on the chassis
LED = 14

STATES = ("up", "over", "down")


# ---------------------------------------------------------------- tiles ---

def tile(name, w, h, rows):
    """A 1:1 tile.  `rows` is a list of (y0, y1, colour) bands."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y0, y1, col in rows:
        d.rectangle([0, y0, w - 1, y1], fill=col)
    _record(os.path.join(OUT, name + ".png"))
    img.save(os.path.join(OUT, name + ".png"), optimize=True)


def gradient_tile(name, w, h, top, bottom, caps=()):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        d.rectangle([0, y, w - 1, y], fill=col)
    for y0, y1, col in caps:
        d.rectangle([0, y0, w - 1, y1], fill=col)
    _record(os.path.join(OUT, name + ".png"))
    img.save(os.path.join(OUT, name + ".png"), optimize=True)


def backgrounds():
    ch, hi, lo, ink = rgba("CHASSIS"), rgba("CHASSIS_HI"), rgba("CHASSIS_LO"), rgba("INK")
    deep = rgba("CHASSIS_DEEP")

    tile("bg_header", 6, HEADER_H, [
        (0, 0, hi), (1, HEADER_H - 2, ch), (HEADER_H - 1, HEADER_H - 1, ink)])

    tile("bg_deck", 6, DECK_H, [
        (0, 0, ink), (1, 49, ch), (50, 50, lo), (51, DECK_H - 1, ch)])

    gradient_tile("bg_lcd", 6, 44, rgb("LCD_BG"), rgb("LCD_BG2"),
                  caps=[(0, 0, deep), (1, 1, (160, 156, 0, 255)), (43, 43, hi)])

    tile("bg_stage", 8, 8, [(0, 7, rgba("STAGE"))])
    tile("bg_panel", 6, 6, [(0, 5, ch)])
    tile("bg_panel_top", 6, HEADER_H, [
        (0, 0, hi), (1, HEADER_H - 2, ch), (HEADER_H - 1, HEADER_H - 1, ink)])
    tile("bg_lcdflat", 6, 6, [(0, 5, rgba("LCD_BG2"))])
    tile("bg_fsc", 6, 64, [
        (0, 0, ink), (1, 1, hi), (2, 62, ch), (63, 63, ink)])
    tile("bg_seam", 6, 1, [(0, 0, lo)])
    # near-invisible strip that still answers hit tests: the window edges use
    # it for resizeE / resizeS without putting a visible line on the chassis.
    tile("bg_hit", 4, 4, [(0, 3, (0, 0, 0, 6))])


# -------------------------------------------------------------- buttons ---

def _pad_housing(d, w, h, col, radius=7):
    rr(d, [0, 0, w, h], radius, col)


def icon_button(name, glyph, size=ICON, gs=None, tone="chassis"):
    """A bare glyph button sitting directly on the chassis."""
    gs = gs or size * 0.56
    for st in STATES:
        img, d = canvas(size, size)
        if tone == "chassis":
            if st == "over":
                rr(d, [0, 0, size, size], 6, rgba("CHASSIS_LO"))
                col = rgba("INK")
            elif st == "down":
                rr(d, [0, 0, size, size], 6, rgba("INK"))
                col = rgba("CHASSIS")
            else:
                col = rgba("INK")
        else:                                   # on a dark field
            if st == "over":
                rr(d, [0, 0, size, size], 6, (255, 255, 255, 26))
                col = rgba("CHASSIS")
            elif st == "down":
                rr(d, [0, 0, size, size], 6, rgba("CHASSIS"))
                col = rgba("INK")
            else:
                col = rgba("CHASSIS_LO")
        glyph(d, size / 2, size / 2, gs, col)
        save(img, size, size, "%s_%s" % (name, st))


def dim_icon(name, glyph, size=ICON, gs=None):
    """Checkbox 'off' face: same geometry, muted ink."""
    gs = gs or size * 0.56
    for st in STATES:
        img, d = canvas(size, size)
        if st == "over":
            rr(d, [0, 0, size, size], 6, rgba("CHASSIS_LO"))
            col = rgba("INK")
        elif st == "down":
            rr(d, [0, 0, size, size], 6, rgba("INK"))
            col = rgba("CHASSIS")
        else:
            col = rgba("INK_SOFT")
        glyph(d, size / 2, size / 2, gs, col)
        save(img, size, size, "%s_%s" % (name, st))


def active_icon(name, glyph, size=ICON, gs=None):
    """Checkbox 'on' face: full ink plus an underline tick."""
    gs = gs or size * 0.56
    for st in STATES:
        img, d = canvas(size, size)
        if st == "over":
            rr(d, [0, 0, size, size], 6, rgba("CHASSIS_LO"))
            col = rgba("INK")
        elif st == "down":
            rr(d, [0, 0, size, size], 6, rgba("INK"))
            col = rgba("CHASSIS")
        else:
            col = rgba("INK")
        glyph(d, size / 2, size / 2 - 1.5, gs, col)
        bw = size * 0.42
        d.rectangle([(size / 2 - bw / 2) * S, (size - 5) * S,
                     (size / 2 + bw / 2) * S, (size - 3.5) * S], fill=col)
        save(img, size, size, "%s_%s" % (name, st))


def pad_button(name, glyph, w=PAD, h=PAD, gs=None):
    """A dark pad, like the pager's rubber keys."""
    gs = gs or w * 0.50
    for st in STATES:
        img, d = canvas(w, h)
        if st == "down":
            _pad_housing(d, w, h, rgba("CHASSIS"))
            col = rgba("INK")
        elif st == "over":
            _pad_housing(d, w, h, rgba("BTN_OVER"))
            col = rgba("CHASSIS_HI")
        else:
            _pad_housing(d, w, h, rgba("BTN"))
            col = rgba("CHASSIS")
        glyph(d, w / 2, h / 2, gs, col)
        save(img, w, h, "%s_%s" % (name, st))


def _cluster_face(st):
    if st == "down":
        return rgba("CHASSIS"), rgba("INK")
    if st == "over":
        return rgba("BTN_OVER"), rgba("CHASSIS_HI")
    return rgba("BTN"), rgba("CHASSIS")


def pad_button_on(name, glyph, w=PAD, h=PAD, gs=None):
    """The lit face of a pad toggle: chassis housing, ink glyph."""
    gs = gs or w * 0.50
    for st in STATES:
        img, d = canvas(w, h)
        if st == "down":
            _pad_housing(d, w, h, rgba("BTN"))
            col = rgba("CHASSIS")
        elif st == "over":
            _pad_housing(d, w, h, rgba("CHASSIS_HI"))
            col = rgba("INK")
        else:
            _pad_housing(d, w, h, rgba("CHASSIS"))
            col = rgba("INK")
        glyph(d, w / 2, h / 2, gs, col)
        d.rectangle([(w / 2 - w * 0.18) * S, (h - 5) * S,
                     (w / 2 + w * 0.18) * S, (h - 3.5) * S], fill=col)
        save(img, w, h, "%s_%s" % (name, st))


def cluster_pill(name, glyph, side):
    """End cap of the nav cluster: round on the outside, square on the inside."""
    w, h, r = PILL_W, PILL_H, PILL_H / 2
    for st in STATES:
        img, d = canvas(w, h)
        body, ink = _cluster_face(st)
        if side == "left":
            d.rounded_rectangle([0, 0, (w + r) * S, h * S], radius=r * S, fill=body)
        else:
            d.rounded_rectangle([-r * S, 0, w * S, h * S], radius=r * S, fill=body)
        cx = w / 2 + (-2 if side == "left" else 2)
        glyph(d, cx, h / 2, 17, ink)
        save(img, w, h, "%s_%s" % (name, st))


def cluster_bar(name, glyph, half):
    """One half of the nav cluster's centre rocker."""
    w, h, r = BAR_W, BAR_H, 7
    for st in STATES:
        img, d = canvas(w, h)
        body, ink = _cluster_face(st)
        if half == "top":
            d.rounded_rectangle([0, 0, w * S, (h + r) * S], radius=r * S, fill=body)
        else:
            d.rounded_rectangle([0, -r * S, w * S, h * S], radius=r * S, fill=body)
        glyph(d, w / 2, h / 2, 13, ink)
        save(img, w, h, "%s_%s" % (name, st))


# --------------------------------------------------------------- sliders ---

def _bar_frame(w, h, frac, groove, fill, radius=None):
    radius = h / 2 if radius is None else radius
    img, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * S, h * S], radius=radius * S, fill=groove)
    fw = round(w * frac)
    if fw >= 2:
        d.rounded_rectangle([0, 0, fw * S, h * S], radius=radius * S, fill=fill)
    return img.resize((w, h), Image.LANCZOS)


def fill_sheet(name, w, h, frames):
    """Vertically stacked frames for a <SliderBackground nbvert=...>."""
    sheet = Image.new("RGBA", (w, h * frames), (0, 0, 0, 0))
    groove = rgba("CHASSIS_DEEP")
    fill = rgba("INK")
    for i in range(frames):
        sheet.paste(_bar_frame(w, h, i / (frames - 1), groove, fill), (0, i * h))
    _record(os.path.join(OUT, name + ".png"))
    sheet.save(os.path.join(OUT, name + ".png"), optimize=True)


def thumb(name, w, h, radius=2.5):
    for st in STATES:
        img, d = canvas(w, h)
        if st == "down":
            body, edge = rgba("INK"), rgba("CHASSIS_HI")
        elif st == "over":
            body, edge = rgba("INK"), rgba("CHASSIS")
        else:
            body, edge = rgba("INK"), rgba("CHASSIS_LO")
        rr(d, [0, 0, w, h], radius, edge)
        rr(d, [1, 1, w - 1, h - 1], max(0.5, radius - 1), body)
        if st != "up":
            rr(d, [w / 2 - 0.75, 3, w / 2 + 0.75, h - 3], 0.75, edge)
        save(img, w, h, "%s_%s" % (name, st))


def eq_track():
    w, h = 6, 110
    img, d = canvas(w, h)
    rr(d, [0, 0, w, h], 3, rgba("CHASSIS_DEEP"))
    rr(d, [2, 2, w - 2, h - 2], 1, (120, 116, 0, 255))
    save(img, w, h, "eq_track")


# ------------------------------------------------------------ indicators ---

def leds():
    specs = (("led_g_on", "LED_G_ON", True), ("led_g_off", "LED_G_OFF", False),
             ("led_r_on", "LED_R_ON", True), ("led_r_off", "LED_R_OFF", False))
    for name, key, lit in specs:
        img, d = canvas(LED, LED)
        rr(d, [0, 0, LED, LED], 3, rgba("BTN"))
        r = 3.6
        c = LED / 2
        if lit:
            d.ellipse([(c - r - 1.8) * S, (c - r - 1.8) * S,
                       (c + r + 1.8) * S, (c + r + 1.8) * S], fill=rgba(key, 70))
        d.ellipse([(c - r) * S, (c - r) * S, (c + r) * S, (c + r) * S], fill=rgba(key))
        if lit:
            d.ellipse([(c - r * 0.42) * S, (c - r * 0.62) * S,
                       (c + r * 0.30) * S, (c - r * 0.05) * S],
                      fill=(255, 255, 255, 150))
        save(img, LED, LED, name)


def badge():
    w, h = 150, 18
    img, d = canvas(w, h)
    rr(d, [0, 0, w, h], 3, rgba("BTN"))
    f = font(JBB, 9 * S)
    text_at(d, (9 * S, h / 2 * S + 1), "VLC", f, rgba("CHASSIS"), anchor="lm", spacing=1.6 * S)
    x = 9 * S + d.textlength("VLC", font=f) + 4 * S * 1.6
    d.rectangle([x + 3 * S, 5 * S, x + 4 * S, (h - 5) * S], fill=rgba("CHASSIS_DEEP"))
    text_at(d, (x + 10 * S, h / 2 * S + 1), "ADVISOR", f, rgba("CHASSIS_LO"),
            anchor="lm", spacing=1.6 * S)
    save(img, w, h, "badge")


def stage_mark():
    w, h = 460, 128
    img, d = canvas(w, h)
    col = rgba("STAGE_MARK")
    f1 = font(STM, 22 * S)
    f2 = font(STM, 46 * S)

    def centred(s, f, y, spacing, fill):
        adv = sum(d.textlength(c, font=f) for c in s) + spacing * (len(s) - 1)
        text_at(d, (w / 2 * S - adv / 2, y * S), s, f, fill, anchor="lt", spacing=spacing)
        return adv

    a1 = centred("GRAND CENTRAL", f1, 14, 6 * S, rgba("STAGE_MARK", 190))
    centred("HACK THE PLANET", f2, 50, 5 * S, col)
    d.rectangle([(w / 2 * S - a1 / 2), 44 * S, (w / 2 * S + a1 / 2), 45 * S],
                fill=rgba("STAGE_MARK", 120))
    save(img, w, h, "stage_mark")


def playtree_icons():
    sz = 10
    img, d = canvas(sz, sz)
    d.rectangle([3 * S, 4 * S, 7 * S, 6 * S], fill=rgba("LCD_INK", 150))
    save(img, sz, sz, "pl_item")

    img, d = canvas(sz, sz)
    d.polygon([(2 * S, 3 * S), (8 * S, 3 * S), (5 * S, 7.5 * S)], fill=rgba("LCD_INK"))
    save(img, sz, sz, "pl_open")

    img, d = canvas(sz, sz)
    d.polygon([(3 * S, 2 * S), (3 * S, 8 * S), (7.5 * S, 5 * S)], fill=rgba("LCD_INK"))
    save(img, sz, sz, "pl_closed")


def grip():
    sz = 14
    img, d = canvas(sz, sz)
    for i, n in enumerate((3, 2, 1)):
        for k in range(n):
            x = sz - 3 - i * 4 - k * 4
            y = sz - 3 - k * 4
            d.rectangle([(x - 1.4) * S, (y - 1.4) * S, (x + 1.4) * S, (y + 1.4) * S],
                        fill=rgba("INK_SOFT"))
    save(img, sz, sz, "grip_se")


# ------------------------------------------------------------------ main ---

def build():
    backgrounds()

    # header / window furniture
    icon_button("sys_close", g_close)
    icon_button("sys_min", g_min)
    icon_button("sys_max", g_max)
    icon_button("sys_unmax", g_unmax)
    icon_button("sys_shade", lambda d, x, y, s, c: g_chev(d, x, y, s, c, up=True))
    icon_button("sys_unshade", lambda d, x, y, s, c: g_chev(d, x, y, s, c, up=False))

    # transport cluster - the pager's nav rocker
    cluster_pill("tr_prev", g_prev, "left")
    cluster_pill("tr_next", g_next, "right")
    cluster_bar("tr_play", g_play, "top")
    cluster_bar("tr_pause", g_pause, "top")
    cluster_bar("tr_stop", g_stop, "bottom")

    # dark pads
    pad_button("pad_open", g_eject)
    pad_button("pad_list", g_list)
    pad_button_on("pad_list_on", g_list)

    # chassis icon buttons
    icon_button("ico_full", g_fullscreen)
    icon_button("ico_play", g_play, gs=13)
    icon_button("ico_pause", g_pause, gs=13)
    icon_button("ico_stop", g_stop, gs=13)
    icon_button("ico_prev", g_prev, gs=15)
    icon_button("ico_next", g_next, gs=15)
    icon_button("ico_snap", g_snapshot)
    icon_button("ico_add", g_plus)
    icon_button("ico_del", g_minus)
    icon_button("ico_sort", g_sort)

    # two-state checkboxes
    active_icon("chk_sound_on", g_sound_on)
    dim_icon("chk_sound_off", g_sound_off)
    dim_icon("chk_loop_off", g_loop)
    active_icon("chk_loop_on", g_loop)
    dim_icon("chk_shuf_off", g_shuffle)
    active_icon("chk_shuf_on", g_shuffle)
    dim_icon("chk_eq_off", g_eq)
    active_icon("chk_eq_on", g_eq)

    # sliders
    fill_sheet("seek_fill", SEEK_W, 6, 61)
    fill_sheet("vol_fill", VOL_W, 6, 21)
    thumb("seek_thumb", 12, 18, radius=3)
    thumb("vol_thumb", 10, 16, radius=3)
    thumb("pls_thumb", 8, 28, radius=4)
    thumb("eqs_thumb", 16, 9, radius=3)
    eq_track()

    leds()
    badge()
    stage_mark()
    playtree_icons()
    grip()


def main():
    global OUT
    ap = argparse.ArgumentParser(description="Generate Cereal Pager skin artwork.")
    ap.add_argument("--out", default=os.path.join(HERE, "assets"))
    args = ap.parse_args()
    OUT = args.out
    os.makedirs(OUT, exist_ok=True)
    build()
    stale = [f for f in os.listdir(OUT) if f.endswith(".png") and f not in WRITTEN]
    for f in stale:
        os.remove(os.path.join(OUT, f))
    print("wrote %d PNGs to %s%s"
          % (len(WRITTEN), OUT,
             " (removed %d stale)" % len(stale) if stale else ""))


if __name__ == "__main__":
    main()
