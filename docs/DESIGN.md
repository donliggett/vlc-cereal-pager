# Design notes

## The source

One frame: a yellow Motorola Advisor pager held in a hand, its LCD showing two
lines of text. The parts worth keeping were the colour, the two-line readout,
the black rubber keys against the yellow shell, and the nav rocker — a rounded
cap on each side with a stacked pair of keys between them.

The parts worth dropping were everything that makes it look like a 1993
injection moulding: the bevels, the moulded seams, the scuffs, the shadow under
the lip of the case. What is left is flat colour, hairline rules and one
typeface family.

## Palette

`tools/palette.py` is the single source of truth. Every colour in the artwork
and every `color=` in `theme.xml` comes from it.

| Token | Hex | Where it lands |
| --- | --- | --- |
| `CHASSIS` | `#EDE600` | the shell — header, deck, window bodies |
| `CHASSIS_HI` | `#F7F35C` | 1px top highlight, hover fills |
| `CHASSIS_LO` | `#C6C000` | seams, hover pads |
| `CHASSIS_DEEP` | `#969100` | unfilled slider grooves |
| `INK` | `#121208` | glyphs, rules, slider fill |
| `INK_SOFT` | `#706C0C` | inactive toggles, secondary labels |
| `LCD_BG` → `LCD_BG2` | `#CECA0A` → `#B8B406` | the readout field, top to bottom |
| `LCD_INK` | `#141508` | the big readout line |
| `LCD_DIM` | `#807D05` | the small readout line |
| `BTN` / `BTN_OVER` | `#1A1A14` / `#2E2E24` | rubber keys, at rest and hovered |
| `LED_G_ON` / `LED_R_ON` | `#56FF7A` / `#FF4A3A` | status lamps |
| `STAGE` | `#0A0A07` | the picture area when there is no picture |

The yellow is loud enough that contrast has to be managed carefully: ink on
chassis is about 11:1, and the dim readout line against the lit field is
deliberately low — it should read like an unlit segment, not like body copy.

## Grid

Design size is 800×520. Everything is stated in those coordinates; the resize
policy does the rest.

```
header   y   0 ..  36
stage    y  36 .. H-128       full bleed, left and right edges untouched
deck     y H-128 .. H
```

Deck-local:

```
  0          1px ink rule
  5 ..  49   LCD readout      line 1 at y 7 (13px), line 2 at y 23 (20px)
 50          1px seam
 58 ..  64   seek bar, x 18 .. W-18
 74 .. 122   control row, everything centred on y 98
```

Control row, left to right: open (32px pad), playlist (32px pad), snapshot
(26px icon) · nav cluster (176×44, centred) · shuffle, loop, mute (26px each),
volume (84×6), fullscreen.

`minwidth` is 700 because that is the point at which the centred nav cluster
would touch the right-hand group.

## Resize policy

skins2 resizes a control by which corner of its container each of its own
corners is pinned to:

* full-bleed strips — `lefttop="lefttop" rightbottom="righttop"`, so they
  stretch horizontally and keep their height
* the deck — a `Panel` with `lefttop="leftbottom" rightbottom="rightbottom"`,
  so it rides the bottom edge; its children then work in deck-local coordinates
* the right-hand group — `lefttop="righttop" rightbottom="righttop"`, so each
  control keeps its distance from the right edge
* the stage and the video — pinned `lefttop` to `rightbottom`, so they absorb
  every pixel the window gains

`xkeepratio` is a trap worth naming, because this skin hit it. It does not pin
a control to the centre; it preserves the *ratio* of the space on its left to
the space on its right. Five buttons sitting side by side each have a different
ratio, so under `xkeepratio` they drift apart and eventually overlap. The fix
is to put the group in a `Panel`, give the *panel* `xkeepratio`, and let the
children inside use plain `lefttop` anchoring. `tools/preview.py` catches this
class of bug by rendering at the extremes and reporting collisions between
always-visible controls.

## Sliders

A skins2 `<Slider>` is a Bezier curve plus a cursor bitmap that is drawn
*centred* on the curve point. The optional `<SliderBackground>` is a sprite
sheet: the control divides it into `nbhoriz × nbvert` frames and draws the one
whose index matches the slider's value, scaled to the control's rect.

That is what makes a filled bar possible. `seek_fill.png` is 61 frames stacked
vertically, each 764×6, filled 0/60 through 60/60. `vol_fill.png` is 21 frames
of 84×6. Because the whole sheet scales with the control, the fill stays
proportionally correct at any window width.

Frames are stacked *vertically* on purpose: a horizontal strip would have to be
`61 × 764` pixels wide, since skins2 scales the sheet first and divides second.

## Typography

* **Share Tech Mono** for the readout and the watermark — squared-off, LCD-ish,
  but clean rather than dot-matrix.
* **JetBrains Mono** (Medium and Bold) for UI labels, the playlist and tooltips.

Both are SIL OFL 1.1 and are bundled in `fonts/`.

## Artwork

`tools/generate_assets.py` draws all 131 PNGs at 4× supersample and downsamples
with Lanczos, so curves stay crisp at 26px. Every button has three faces:

* **up** — dark pad, yellow glyph (or bare ink glyph on the chassis)
* **over** — the pad lightens; bare icons get a `CHASSIS_LO` hover plate
* **down** — full inversion: yellow pad, ink glyph

Two-state checkboxes add a fourth signal — the "on" face carries a short
underline bar, so loop and shuffle read as engaged without relying on colour.

The generator deletes any PNG in `assets/` it did not write, so removing a
control from the build removes its artwork too.
