# Building and hacking on the skin

## Requirements

* Python 3.8+
* Pillow — `pip install pillow`
* VLC 3.x on Windows or Linux (macOS builds do not include skins2)

## The pipeline

```
tools/palette.py          colour tokens, imported by everything
        │
tools/generate_assets.py  draws assets/*.png  (and prunes stale ones)
        │
tools/sync_bitmaps.py     rewrites the <Bitmap> block inside theme.xml
        │
tools/preview.py          renders docs/preview/*.png, flags collisions
        │
tools/validate_theme.py   static checks against the skins2 schema
        │
build.ps1 / build.sh      packages dist/CerealPager.vlt
```

`build.ps1` (PowerShell 5.1, no `&&`) and `build.sh` both run the whole thing.
Pass `-Quick` / `--quick` to skip straight to validate-and-package.

## Changing the colour

Edit `tools/palette.py`, then rebuild. If you change a colour that `theme.xml`
also names — the readout inks, the playlist colours — update those `color=`,
`fgcolor=` and `bgcolor=` attributes to match; `python tools/palette.py` prints
the hex for every token.

## Changing the layout

Coordinates live in `theme.xml` and are all stated at the 800×520 design size.
After any edit:

```bash
python tools/validate_theme.py
python tools/preview.py --layout normal --width 700 --height 340
python tools/preview.py --layout normal --width 1400 --height 820
```

The preview exits non-zero if two always-visible controls overlap. Check both
extremes — most layout bugs in skins2 only appear at the ends of the range.

## What the validator checks

* well-formed XML, and only skins2 elements and attributes
* every `<Bitmap>` and `<Font>` file exists on disk
* every bitmap reference resolves to something declared
* Bitmap ids and control ids are unique
* all faces of a Button or Checkbox are the same pixel size
* `visible=` and `state=` only name statuses skins2 knows
* `<Slider value=>` names a real percentage variable
* every action is a known command, or targets a window/layout that exists
* `$` escapes in text and tooltips are ones skins2 expands

Most of these are things VLC will not tell you about: it logs a line to the
messages window and silently drops the control.

## Iterating against VLC

VLC caches the skin it unpacked. After rebuilding:

1. Restart VLC, or
2. **Tools → Preferences → Interface → Use custom skin**, re-select the `.vlt`.

To watch for errors while a skin loads, start VLC with `--verbose 2`, or open
**Tools → Messages** and set the verbosity to Debug. Missing bitmaps, unknown
actions and bad variable names all show up as `skins2` errors there.

For faster iteration, point VLC at the unpacked `theme.xml` instead of the
`.vlt` — the file picker accepts `.xml` — and you only need to re-select it
after each change.

## Packaging notes

A `.vlt` is an ordinary archive whose *root* contains `theme.xml`, with assets
and fonts in subdirectories beside it. Both formats work:

* `tar.gz` — what `build.sh` produces, and the original skins2 format
* `zip` — what `build.ps1` produces, supported since VLC 0.8.5 and the one
  PowerShell 5.1 can make without extra tools

Do not wrap the contents in an extra top-level folder; VLC looks for
`theme.xml` at the root of what it unpacked.
