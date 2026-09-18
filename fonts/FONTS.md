# Bundled fonts

Both families are licensed under the **SIL Open Font License 1.1**, whose full
text is in `OFL-1.1.txt`. The OFL permits bundling and redistribution inside a
larger work; it does not extend the repository's MIT licence to the font files,
and it does not permit selling the fonts on their own.

| File | Family | Copyright | Used for |
| --- | --- | --- | --- |
| `ShareTechMono-Regular.ttf` | Share Tech Mono | Copyright © Carrois Apostrophe | the LCD readout, the stage watermark |
| `JetBrainsMono-Medium.ttf` | JetBrains Mono | Copyright © JetBrains s.r.o. | UI labels, playlist rows, tooltips |
| `JetBrainsMono-Bold.ttf` | JetBrains Mono | Copyright © JetBrains s.r.o. | window titles |

Both were fetched from the Google Fonts CDN. Neither has been modified,
subsetted or renamed.

skins2 renders fonts through FreeType and takes a plain path in `<Font file=>`,
so these ship inside the `.vlt` and nothing needs to be installed on the system.
