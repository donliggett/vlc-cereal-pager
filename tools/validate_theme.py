#!/usr/bin/env python3
"""Static checks for theme.xml, of the kind VLC only mutters about in its log.

    python tools/validate_theme.py [theme.xml]

Checks performed:
  * the file is well-formed XML and only uses skins2 elements/attributes
  * every Bitmap and Font file actually exists on disk
  * every bitmap reference (image, up/down/over, up1..down2, bgimage,
    itemimage, openimage, closedimage, SliderBackground/@image) resolves
  * Bitmap ids and control ids are unique
  * Button/Checkbox faces all have the same pixel size as their `up` face
  * boolean expressions only name statuses the skins2 interpreter knows
  * Slider/@value only names a percentage variable skins2 knows
  * every action names a real window / layout and a known command
  * $-escapes in text and tooltips are ones skins2 expands
Exit status is non-zero if anything failed.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------- schema ---
ELEMENTS = {
    "Theme": {"version", "tooltipfont", "magnet", "alpha", "movealpha"},
    "ThemeInfo": {"name", "author", "email", "webpage"},
    "Include": {"file"},
    "IniFile": {"id", "file"},
    "Bitmap": {"id", "file", "alphacolor", "nbframes", "fps", "loop"},
    "SubBitmap": {"id", "x", "y", "width", "height", "nbframes", "fps", "loop"},
    "Font": {"id", "file", "size"},
    "BitmapFont": {"id", "file", "type"},
    "PopupMenu": {"id"},
    "MenuItem": {"label", "action"},
    "MenuSeparator": set(),
    "Window": {"id", "visible", "x", "y", "position", "xoffset", "yoffset",
               "xmargin", "ymargin", "dragdrop", "playondrop"},
    "Layout": {"id", "width", "height", "minwidth", "maxwidth",
               "minheight", "maxheight"},
    "Group": {"id", "x", "y"},
    "Panel": {"id", "x", "y", "lefttop", "rightbottom", "xkeepratio",
              "ykeepratio", "width", "height", "position", "xoffset",
              "yoffset", "xmargin", "ymargin"},
    "Anchor": {"id", "x", "y", "lefttop", "priority", "points", "range"},
    "Image": {"id", "visible", "x", "y", "width", "height", "lefttop",
              "rightbottom", "xkeepratio", "ykeepratio", "image", "action",
              "action2", "resize", "help", "art"},
    "Button": {"id", "visible", "x", "y", "lefttop", "rightbottom",
               "xkeepratio", "ykeepratio", "up", "down", "over", "action",
               "tooltiptext", "help"},
    "Checkbox": {"id", "visible", "x", "y", "lefttop", "rightbottom",
                 "xkeepratio", "ykeepratio", "up1", "down1", "over1",
                 "up2", "down2", "over2", "state", "action1", "action2",
                 "tooltiptext1", "tooltiptext2", "help"},
    "Slider": {"id", "visible", "x", "y", "width", "height", "lefttop",
               "rightbottom", "xkeepratio", "ykeepratio", "up", "down",
               "over", "points", "thickness", "value", "background",
               "tooltiptext", "help"},
    "SliderBackground": {"id", "image", "nbhoriz", "nbvert", "padhoriz", "padvert"},
    "RadialSlider": {"id", "visible", "x", "y", "lefttop", "rightbottom",
                     "xkeepratio", "ykeepratio", "sequence", "nbimages",
                     "minangle", "maxangle", "value", "tooltiptext", "help"},
    "Text": {"id", "visible", "x", "y", "width", "lefttop", "rightbottom",
             "xkeepratio", "ykeepratio", "text", "font", "color", "scrolling",
             "alignment", "focus", "help"},
    "Playlist": {"id", "visible", "x", "y", "width", "height", "position",
                 "xoffset", "yoffset", "xmargin", "ymargin", "lefttop",
                 "rightbottom", "xkeepratio", "ykeepratio", "font", "bgimage",
                 "fgcolor", "playcolor", "bgcolor1", "bgcolor2", "selcolor", "help"},
    "Playtree": {"id", "visible", "x", "y", "width", "height", "position",
                 "xoffset", "yoffset", "xmargin", "ymargin", "lefttop",
                 "rightbottom", "xkeepratio", "ykeepratio", "font", "bgimage",
                 "itemimage", "openimage", "closedimage", "fgcolor", "playcolor",
                 "bgcolor1", "bgcolor2", "selcolor", "help", "flat"},
    "Video": {"id", "visible", "x", "y", "width", "height", "position",
              "xoffset", "yoffset", "xmargin", "ymargin", "lefttop",
              "rightbottom", "xkeepratio", "ykeepratio", "autoresize", "help"},
}

BITMAP_REFS = ("image", "up", "down", "over", "up1", "down1", "over1",
               "up2", "down2", "over2", "bgimage", "itemimage",
               "openimage", "closedimage")

ANCHORS = {"lefttop", "leftbottom", "righttop", "rightbottom"}

BOOLS = {
    "true", "false",
    "equalizer.isEnabled", "vlc.hasVout", "vlc.hasAudio", "vlc.isFullscreen",
    "vlc.isPlaying", "vlc.isStopped", "vlc.isPaused", "vlc.isSeekable",
    "vlc.canRecord", "vlc.isRecording", "vlc.isMute", "vlc.isOnTop",
    "playlist.isRandom", "playlist.isLoop", "playlist.isRepeat", "dvd.isActive",
}
BOOL_SUFFIXES = (".isMaximized", ".isVisible", ".isActive")

PERCENTS = {"time", "volume", "equalizer.preamp"}
PERCENT_RE = re.compile(r"^equalizer\.band\([0-9]\)$")

COMMANDS = {
    "none",
    "dialogs.changeSkin()", "dialogs.fileSimple()", "dialogs.file()",
    "dialogs.directory()", "dialogs.disc()", "dialogs.net()",
    "dialogs.messages()", "dialogs.prefs()", "dialogs.fileInfo()",
    "dialogs.playlist()", "dialogs.streamingWizard()", "dialogs.popup()",
    "dialogs.audioPopup()", "dialogs.videoPopup()", "dialogs.miscPopup()",
    "equalizer.enable()", "equalizer.disable()",
    "vlc.play()", "vlc.pause()", "vlc.stop()", "vlc.faster()", "vlc.slower()",
    "vlc.mute()", "vlc.volumeUp()", "vlc.volumeDown()", "vlc.fullscreen()",
    "vlc.snapshot()", "vlc.toggleRecord()", "vlc.nextFrame()", "vlc.onTop()",
    "vlc.minimize()", "vlc.quit()",
    "playlist.add()", "playlist.del()", "playlist.next()", "playlist.previous()",
    "playlist.sort()", "playlist.setRandom(true)", "playlist.setRandom(false)",
    "playlist.setLoop(true)", "playlist.setLoop(false)",
    "playlist.setRepeat(true)", "playlist.setRepeat(false)",
    "playlist.load()", "playlist.save()",
    "dvd.nextTitle()", "dvd.previousTitle()", "dvd.nextChapter()",
    "dvd.previousChapter()", "dvd.rootMenu()",
    "move", "resizeS", "resizeE", "resizeSE",
}
WIN_CMD_RE = re.compile(r"^([\w.]+)\.(show|hide|maximize|unmaximize)\(\)$")
LAYOUT_CMD_RE = re.compile(r"^([\w.]+)\.setLayout\(([\w.-]+)\)$")

ESCAPES = set("BVRTLDNFSHtld")

problems = []
notes = []


def bad(msg):
    problems.append(msg)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "theme.xml")
    root_dir = os.path.dirname(os.path.abspath(path))
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        sys.exit("theme.xml is not well-formed XML: %s" % exc)
    root = tree.getroot()

    bitmaps, sizes, fonts = {}, {}, set()
    windows, layouts, ctrl_ids = set(), set(), {}

    # ---- pass 1: declarations -------------------------------------------
    for el in root.iter():
        if el.tag not in ELEMENTS:
            bad("unknown element <%s>" % el.tag)
            continue
        for attr in el.attrib:
            if attr not in ELEMENTS[el.tag]:
                bad("<%s> has no attribute '%s'" % (el.tag, attr))
        for attr in ("lefttop", "rightbottom"):
            v = el.get(attr)
            if v is not None and v not in ANCHORS:
                bad("<%s id=%s> %s=\"%s\" is not one of %s"
                    % (el.tag, el.get("id"), attr, v, sorted(ANCHORS)))

        if el.tag in ("Bitmap", "SubBitmap"):
            bid = el.get("id")
            if bid in bitmaps:
                bad("duplicate Bitmap id '%s'" % bid)
            bitmaps[bid] = el
            if el.tag == "Bitmap":
                f = os.path.join(root_dir, el.get("file", ""))
                if not os.path.isfile(f):
                    bad("Bitmap '%s' points at a missing file: %s"
                        % (bid, el.get("file")))
                else:
                    try:
                        from PIL import Image
                        with Image.open(f) as im:
                            sizes[bid] = im.size
                    except ImportError:
                        pass
        elif el.tag in ("Font", "BitmapFont"):
            fonts.add(el.get("id"))
            f = os.path.join(root_dir, el.get("file", ""))
            if not os.path.isfile(f):
                bad("Font '%s' points at a missing file: %s"
                    % (el.get("id"), el.get("file")))
        elif el.tag == "Window":
            windows.add(el.get("id"))
        elif el.tag == "Layout":
            layouts.add(el.get("id"))

    # ---- pass 2: references ---------------------------------------------
    for el in root.iter():
        tag, cid = el.tag, el.get("id")

        if tag not in ("Bitmap", "SubBitmap", "Font", "BitmapFont",
                       "Window", "Layout", "Theme", "ThemeInfo"):
            if cid and cid != "none":
                if cid in ctrl_ids:
                    bad("duplicate control id '%s' (<%s> and <%s>)"
                        % (cid, ctrl_ids[cid], tag))
                ctrl_ids[cid] = tag

        for attr in BITMAP_REFS:
            ref = el.get(attr)
            if ref and ref != "none" and ref not in bitmaps:
                bad("<%s id=%s> %s=\"%s\" is not a declared Bitmap"
                    % (tag, cid, attr, ref))

        if tag in ("Button", "Checkbox") and sizes:
            base = "up" if tag == "Button" else "up1"
            ref = el.get(base)
            if ref in sizes:
                for attr in ("down", "over", "up1", "down1", "over1",
                             "up2", "down2", "over2"):
                    other = el.get(attr)
                    if other in sizes and sizes[other] != sizes[ref]:
                        bad("<%s id=%s> face '%s' is %s but '%s' is %s"
                            % (tag, cid, attr, sizes[other], base, sizes[ref]))

        if tag in ("Text", "Playlist", "Playtree"):
            f = el.get("font")
            if f and f not in fonts:
                bad("<%s id=%s> font=\"%s\" is not declared" % (tag, cid, f))

        if tag == "Slider" and el.get("value"):
            v = el.get("value")
            if v != "none" and v not in PERCENTS and not PERCENT_RE.match(v):
                bad("<Slider id=%s> value=\"%s\" is not a known percentage "
                    "variable" % (cid, v))

        for attr in ("visible", "state"):
            expr = el.get(attr)
            if expr:
                check_bool(expr, tag, cid, attr, windows, layouts)

        for attr in ("action", "action2", "action1"):
            act = el.get(attr)
            if act:
                check_action(act, tag, cid, attr, windows, layouts)

        for attr in ("text", "tooltiptext", "tooltiptext1", "tooltiptext2"):
            s = el.get(attr)
            if s:
                for m in re.finditer(r"\$(.)", s):
                    if m.group(1) not in ESCAPES:
                        bad("<%s id=%s> %s uses unknown escape '$%s'"
                            % (tag, cid, attr, m.group(1)))

    # ---- pass 3: housekeeping -------------------------------------------
    if "main" not in windows:
        bad("there is no <Window id=\"main\"> - skins2 needs one")

    used = set()
    for el in root.iter():
        for attr in BITMAP_REFS:
            if el.get(attr):
                used.add(el.get(attr))
    unused = sorted(set(bitmaps) - used)
    if unused:
        notes.append("%d declared bitmaps are never used: %s"
                     % (len(unused), ", ".join(unused)))

    theme_font = root.get("tooltipfont")
    if theme_font and theme_font not in fonts:
        bad("Theme tooltipfont=\"%s\" is not declared" % theme_font)

    # ---- report ----------------------------------------------------------
    print("theme.xml: %d bitmaps, %d fonts, %d windows, %d layouts, %d controls"
          % (len(bitmaps), len(fonts), len(windows), len(layouts), len(ctrl_ids)))
    for n in notes:
        print("  note: %s" % n)
    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("no problems found")
    return 0


def check_bool(expr, tag, cid, attr, windows, layouts):
    for tok in re.split(r"[()\s]+", expr):
        if not tok or tok in ("and", "or", "not"):
            continue
        if tok in BOOLS:
            continue
        if any(tok.endswith(s) for s in BOOL_SUFFIXES):
            owner = tok.rsplit(".", 1)[0]
            if owner not in windows and owner not in layouts:
                bad("<%s id=%s> %s=\"%s\" names '%s', which is neither a "
                    "Window nor a Layout" % (tag, cid, attr, expr, owner))
            continue
        bad("<%s id=%s> %s=\"%s\" uses unknown status '%s'"
            % (tag, cid, attr, expr, tok))


def check_action(act, tag, cid, attr, windows, layouts):
    for one in [a.strip() for a in act.split(";") if a.strip()]:
        if one in COMMANDS:
            continue
        m = WIN_CMD_RE.match(one)
        if m:
            if m.group(1) not in windows:
                bad("<%s id=%s> %s=\"%s\" targets unknown window '%s'"
                    % (tag, cid, attr, act, m.group(1)))
            continue
        m = LAYOUT_CMD_RE.match(one)
        if m:
            if m.group(1) not in windows:
                bad("<%s id=%s> %s=\"%s\" targets unknown window '%s'"
                    % (tag, cid, attr, act, m.group(1)))
            if m.group(2) not in layouts:
                bad("<%s id=%s> %s=\"%s\" targets unknown layout '%s'"
                    % (tag, cid, attr, act, m.group(2)))
            continue
        bad("<%s id=%s> %s=\"%s\" is not a known action" % (tag, cid, attr, one))


if __name__ == "__main__":
    sys.exit(main())
