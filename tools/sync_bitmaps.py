#!/usr/bin/env python3
"""Regenerate the <Bitmap> block in theme.xml from whatever is in assets/.

    python tools/sync_bitmaps.py

Every PNG becomes one <Bitmap>, its id being the file stem.  The block is
delimited by the BITMAPS:BEGIN / BITMAPS:END comments, so the rest of
theme.xml is left exactly as written.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(HERE, "theme.xml")
ASSETS = os.path.join(HERE, "assets")

BEGIN = "<!-- BITMAPS:BEGIN"
END = "<!-- BITMAPS:END"

# PNG alpha is what actually keys the transparency; alphacolor is kept at a
# magenta that never appears in the palette so it can never key by accident.
ALPHA = "#FF00FF"


def main():
    names = sorted(f[:-4] for f in os.listdir(ASSETS) if f.endswith(".png"))
    if not names:
        sys.exit("no PNGs in %s - run tools/generate_assets.py first" % ASSETS)

    width = max(len(n) for n in names)
    rows = ['  <Bitmap id="%-*s file="assets/%-*s alphacolor="%s"/>'
            % (width + 1, n + '"', width + 5, n + '.png"', ALPHA) for n in names]

    src = open(THEME, encoding="utf-8").read()
    begin = src.index(BEGIN)
    begin = src.index("\n", begin) + 1
    end = src.index(END)
    out = src[:begin] + "\n".join(rows) + "\n  " + src[end:]
    open(THEME, "w", encoding="utf-8").write(out)
    print("declared %d bitmaps in theme.xml" % len(names))


if __name__ == "__main__":
    main()
