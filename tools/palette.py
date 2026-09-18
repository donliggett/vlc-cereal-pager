"""Cereal Pager - colour tokens.

Single source of truth for every colour used by the skin. Import from
generate_assets.py; the hex strings are also what theme.xml references for
text colours, so keep the two in sync via `python tools/palette.py --xml`.
"""

PALETTE = {
    # chassis -------------------------------------------------------------
    "CHASSIS":      (237, 230, 0),    # #EDE600  the base yellow
    "CHASSIS_HI":   (247, 243, 92),   # #F7F35C  top hairline
    "CHASSIS_LO":   (198, 192, 0),    # #C6C000  seam / recess
    "CHASSIS_DEEP": (150, 145, 0),    # #969100  deepest recess
    # ink -----------------------------------------------------------------
    "INK":          (18, 18, 8),      # #121208  primary ink
    "INK_SOFT":     (112, 108, 12),   # #706C0C  secondary ink
    # readout -------------------------------------------------------------
    "LCD_BG":       (206, 202, 10),   # #CECA0A  lit field, top
    "LCD_BG2":      (184, 180, 6),    # #B8B406  lit field, bottom
    "LCD_INK":      (20, 21, 8),      # #141508  primary readout glyphs
    "LCD_DIM":      (128, 125, 5),    # #807D05  secondary readout glyphs
    "LCD_GHOST":    (168, 164, 8),    # #A8A408  unlit dot-matrix
    # button housings -----------------------------------------------------
    "BTN":          (26, 26, 20),     # #1A1A14  dark pad, at rest
    "BTN_OVER":     (46, 46, 36),     # #2E2E24  dark pad, hover
    # indicators ----------------------------------------------------------
    "LED_G_ON":     (86, 255, 122),
    "LED_G_OFF":    (44, 88, 52),
    "LED_R_ON":     (255, 74, 58),
    "LED_R_OFF":    (100, 38, 30),
    # stage ---------------------------------------------------------------
    "STAGE":        (10, 10, 7),      # #0A0A07  letterbox / no-signal field
    "STAGE_MARK":   (58, 56, 10),     # #3A380A  watermark on the stage
}


def rgb(name):
    return PALETTE[name]


def rgba(name, a=255):
    r, g, b = PALETTE[name]
    return (r, g, b, a)


def hexof(name):
    return "#%02X%02X%02X" % PALETTE[name]


if __name__ == "__main__":
    for k in PALETTE:
        print("%-14s %s" % (k, hexof(k)))
