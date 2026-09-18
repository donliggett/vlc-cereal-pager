#!/usr/bin/env python3
"""Render theme.xml layouts to PNG, without launching VLC.

    python tools/preview.py                     # every layout, default size
    python tools/preview.py --layout normal --width 1100 --height 640

It is a deliberately small re-implementation of the bits of the skins2 layout
model that affect what you see: panels, the lefttop/rightbottom resize policy,
xkeepratio/ykeepratio, mosaic vs scale image fills, slider backgrounds picked
by value, and text with the real fonts.  Good enough to catch a control that
collides, drifts or falls off the edge when the window is resized - which is
exactly the class of bug that is tedious to find by hand in VLC.

Video and Playtree are drawn as labelled placeholders.
"""

import argparse
import os
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# stand-in values for the $ escapes, so text boxes get realistic widths
SAMPLE = {
    "$N": "hackers.1995.remux.mkv", "$t": "0:41:07", "$d": "1:47:22",
    "$T": "0:41:07", "$D": "1:47:22", "$L": "1:06:15", "$l": "1:06:15",
    "$V": "68", "$R": "1.00", "$B": "1536", "$S": "48", "$F": "hackers.mkv",
    "$H": "",
}
DEMO_VALUES = {"time": 0.38, "volume": 0.68,
               "equalizer.preamp": 0.5}


def demo_value(name):
    if name in DEMO_VALUES:
        return DEMO_VALUES[name]
    if name and name.startswith("equalizer.band"):
        return 0.5
    return 0.0


def expand(s):
    if not s:
        return ""
    for k, v in SAMPLE.items():
        s = s.replace(k, v)
    return s


def num(v, default=0):
    try:
        return int(str(v).replace("px", ""))
    except (TypeError, ValueError):
        return default


def truthy(v):
    return str(v).lower() == "true"


class Theme:
    def __init__(self, path):
        self.dir = os.path.dirname(os.path.abspath(path))
        self.root = ET.parse(path).getroot()
        self.bitmaps, self.fonts = {}, {}
        for el in self.root.iter("Bitmap"):
            self.bitmaps[el.get("id")] = os.path.join(self.dir, el.get("file"))
        for el in self.root.iter("Font"):
            self.fonts[el.get("id")] = (os.path.join(self.dir, el.get("file")),
                                        num(el.get("size"), 12))
        self._cache = {}

    def bmp(self, ref):
        if not ref or ref == "none" or ref not in self.bitmaps:
            return None
        if ref not in self._cache:
            self._cache[ref] = Image.open(self.bitmaps[ref]).convert("RGBA")
        return self._cache[ref]

    def font(self, ref):
        path, size = self.fonts.get(ref, (None, 12))
        if not path:
            return ImageFont.load_default()
        key = ("f", path, size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(path, size)
        return self._cache[key]

    def layouts(self):
        out = []
        for win in self.root.iter("Window"):
            for lay in win.findall("Layout"):
                out.append((win, lay))
        return out


def intrinsic(theme, el):
    """Size skins2 infers when width/height are absent: an Image takes its
    bitmap's size, a Button its `up` face, a Checkbox its `up1` face."""
    ref = {"Image": "image", "Button": "up", "Checkbox": "up1"}.get(el.tag)
    if not ref:
        return None
    img = theme.bmp(el.get(ref))
    return (img.width, img.height) if img else None


def place(el, box, dw, dh, nat=None):
    """Apply the skins2 resize policy.  box is the container (x, y, w, h) at
    the rendered size; dw/dh are how much the container grew from its design
    size.  Returns the control's (x, y, w, h)."""
    x, y = num(el.get("x")), num(el.get("y"))
    w, h = num(el.get("width"), -1), num(el.get("height"), -1)
    if nat:
        if w <= 0:
            w = nat[0]
        if h <= 0:
            h = nat[1]
    lt = el.get("lefttop", "lefttop")
    rb = el.get("rightbottom", "lefttop")

    x0, y0 = x, y
    x1 = x + (w if w > 0 else 0)
    y1 = y + (h if h > 0 else 0)

    if truthy(el.get("xkeepratio")):
        left, right = x0, box[4] - x1          # box[4] = design width
        total = left + right
        if total > 0:
            x0 = x0 + dw * left / total
            x1 = x0 + (x1 - x)
    else:
        if lt in ("righttop", "rightbottom"):
            x0 += dw
        if rb in ("righttop", "rightbottom"):
            x1 += dw

    if truthy(el.get("ykeepratio")):
        top, bottom = y0, box[5] - y1          # box[5] = design height
        total = top + bottom
        if total > 0:
            y0 = y0 + dh * top / total
            y1 = y0 + (y1 - y)
    else:
        if lt in ("leftbottom", "rightbottom"):
            y0 += dh
        if rb in ("leftbottom", "rightbottom"):
            y1 += dh

    return (box[0] + x0, box[1] + y0,
            (x1 - x0) if w > 0 else w, (y1 - y0) if h > 0 else h)


def fill(canvas, img, x, y, w, h, mode):
    if img is None or w <= 0 or h <= 0:
        return
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if mode == "scale":
        canvas.alpha_composite(img.resize((w, h), Image.LANCZOS), (x, y))
        return
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for ty in range(0, h, img.height):
        for tx in range(0, w, img.width):
            tile.alpha_composite(img, (tx, ty))
    canvas.alpha_composite(tile.crop((0, 0, w, h)), (x, y))


def draw_controls(theme, parent, canvas, box, marks):
    """box = (ox, oy, w, h, design_w, design_h)"""
    dw = box[2] - box[4]
    dh = box[3] - box[5]
    d = ImageDraw.Draw(canvas)

    for el in parent:
        tag = el.tag
        if tag == "Anchor" or tag == "SliderBackground":
            continue
        if el.get("visible") in ("false",):
            continue

        x, y, w, h = place(el, box, dw, dh, intrinsic(theme, el))

        if tag in ("Panel", "Group"):
            pw = w if w > 0 else box[2]
            ph = h if h > 0 else box[3]
            draw_controls(theme, el, canvas,
                          (x, y, pw, ph, num(el.get("width"), box[4]),
                           num(el.get("height"), box[5])), marks)

        elif tag == "Image":
            img = theme.bmp(el.get("image"))
            if img is None:
                continue
            fill(canvas, img, x, y,
                 w if w > 0 else img.width, h if h > 0 else img.height,
                 el.get("resize", "mosaic"))

        elif tag in ("Button", "Checkbox"):
            ref = el.get("up") if tag == "Button" else el.get("up1")
            img = theme.bmp(ref)
            if img is None:
                continue
            canvas.alpha_composite(img, (int(round(x)), int(round(y))))
            if el.get("visible") is None:
                marks.append((x, y, img.width, img.height))

        elif tag == "Text":
            f = theme.font(el.get("font"))
            s = expand(el.get("text", ""))
            col = el.get("color", "#000000")
            tw = w if w > 0 else 0
            align = el.get("alignment", "left")
            aw = d.textlength(s, font=f)
            tx = x
            if tw:
                if align == "right":
                    tx = x + tw - aw
                elif align == "center":
                    tx = x + (tw - aw) / 2
            d.text((tx, y), s, font=f, fill=col)

        elif tag == "Slider":
            bg = el.find("SliderBackground")
            val = demo_value(el.get("value"))
            pts = [tuple(int(n) for n in p.split(","))
                   for p in el.get("points", "(0,0)")
                   .replace("(", "").strip(")").split("),")]
            if bg is not None:
                sheet = theme.bmp(bg.get("image"))
                if sheet is not None:
                    nbv = num(bg.get("nbvert"), 1)
                    nbh = num(bg.get("nbhoriz"), 1)
                    fh = sheet.height // nbv
                    fw = sheet.width // nbh
                    idx = min(nbv * nbh - 1, int(round(val * (nbv * nbh - 1))))
                    frame = sheet.crop((0, idx * fh, fw, idx * fh + fh))
                    fill(canvas, frame, x, y,
                         w if w > 0 else fw, h if h > 0 else fh, "scale")
            p0, p1 = pts[0], pts[-1]
            sx = (w / max(1, num(el.get("width"), 1))) if w > 0 else 1
            sy = (h / max(1, num(el.get("height"), 1))) if h > 0 else 1
            cx = x + (p0[0] + (p1[0] - p0[0]) * val) * sx
            cy = y + (p0[1] + (p1[1] - p0[1]) * val) * sy
            cur = theme.bmp(el.get("up"))
            if cur is not None:
                canvas.alpha_composite(cur, (int(round(cx - cur.width / 2)),
                                             int(round(cy - cur.height / 2))))
                if el.get("visible") is None:
                    marks.append((cx - cur.width / 2, cy - cur.height / 2,
                                  cur.width, cur.height))

        elif tag in ("Video", "Playtree", "Playlist"):
            bgimg = theme.bmp(el.get("bgimage"))
            if bgimg is not None:
                fill(canvas, bgimg, x, y, w, h, "mosaic")
            d.rectangle([x, y, x + w - 1, y + h - 1],
                        outline=(0, 0, 0, 70) if tag != "Video" else (60, 60, 40, 255))
            f = theme.font("ui")
            label = {"Video": "VIDEO", "Playtree": "PLAYTREE",
                     "Playlist": "PLAYLIST"}[tag]
            d.text((x + 10, y + 8), label, font=f,
                   fill="#6A6A4A" if tag == "Video" else "#4A4808")
            if tag in ("Playtree", "Playlist"):
                for i in range(8):
                    d.text((x + 24, y + 30 + i * 18),
                           "%02d  track-%02d.flac" % (i + 1, i + 1),
                           font=f, fill="#0A0A04" if i == 2 else "#4A4808")
            draw_controls(theme, el, canvas, box, marks)


def overlaps(marks):
    """Collisions between controls that are ALWAYS visible.  Controls carrying
    a `visible` expression are skipped: play/pause and maximise/restore are
    meant to share a spot."""
    out = []
    for i in range(len(marks)):
        for j in range(i + 1, len(marks)):
            a, b = marks[i], marks[j]
            if (a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and
                    a[1] < b[1] + b[3] and b[1] < a[1] + a[3]):
                out.append((a, b))
    return out


def render(theme, win, lay, width=None, height=None):
    dw = num(lay.get("width"))
    dh = num(lay.get("height"))
    w = width or dw
    h = height or dh
    w = max(num(lay.get("minwidth"), 1) or 1, min(w, num(lay.get("maxwidth"), 99999)))
    h = max(num(lay.get("minheight"), 1) or 1, min(h, num(lay.get("maxheight"), 99999)))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    marks = []
    draw_controls(theme, lay, canvas, (0, 0, w, h, dw, dh), marks)
    return canvas, overlaps(marks), (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=os.path.join(HERE, "theme.xml"))
    ap.add_argument("--out", default=os.path.join(HERE, "docs", "preview"))
    ap.add_argument("--layout")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    args = ap.parse_args()

    theme = Theme(args.theme)
    os.makedirs(args.out, exist_ok=True)
    rc = 0
    for win, lay in theme.layouts():
        lid = lay.get("id")
        if args.layout and args.layout != lid:
            continue
        canvas, clashes, (w, h) = render(theme, win, lay, args.width, args.height)
        name = "%s-%dx%d.png" % (lid, w, h)
        canvas.convert("RGB").save(os.path.join(args.out, name))
        msg = "%-12s %4dx%-4d -> %s" % (lid, w, h, name)
        if clashes:
            rc = 1
            msg += "   %d OVERLAPPING CONTROL(S)" % len(clashes)
        print(msg)
        for a, b in clashes:
            print("     %s  vs  %s" % (a, b))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
