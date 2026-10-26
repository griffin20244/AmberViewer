# 🟡 AmberViewer

**A lightweight, minimal image viewer with a dark theme and amber accents.**

Fast image browsing, smooth zooming, and simple format conversion — without unnecessary clutter.

## Features

- **Broad format support** — TGA, PNG, JPEG, BMP, GIF, TIFF, WebP, ICO, and DDS.
- **Zoom and pan** — navigate images smoothly with mouse and keyboard controls.
- **Folder navigation** — browse images using the previous and next controls.
- **Animation playback** — supports animated GIF, WebP, and APNG.
- **Transparency preview** — view transparent images against a checkerboard background.
- **Image conversion** — export supported images to PNG, JPEG, BMP, GIF, TIFF, WebP, or TGA.
- **HiDPI support** — clear rendering on high-resolution displays.
- **Minimal interface** — a dark theme with amber accents.

## Download

Download the latest Windows release from [**GitHub Releases**](https://github.com/griffin20244/AmberViewer/releases).

## Controls

| Action | Shortcut |
|---|---|
| Open image | `Ctrl + O` |
| Save / convert | `Ctrl + S` |
| Zoom | Mouse wheel or `+` / `−` |
| Pan | Click and drag |
| Fit to window | `F` or `Ctrl + 0` |
| Actual size | `1` |
| Previous / next image | `←` / `→` |
| Pause / resume animation | `Space` |
| Toggle fit and actual size | Double-click |

## Supported Formats

| Format | Open | Export |
|---|:---:|:---:|
| PNG / APNG | ✓ | ✓ |
| JPEG | ✓ | ✓ |
| TGA | ✓ | ✓ |
| BMP | ✓ | ✓ |
| GIF | ✓ | ✓ |
| TIFF | ✓ | ✓ |
| WebP | ✓ | ✓ |
| ICO | ✓ | — |
| DDS | ✓ | — |

Format support may vary depending on the image variant and Pillow version. Animated images exported to a still-image format are saved as a single frame.

## Run from Source

**Requirements:** Python and Pillow.

```bash
python -m pip install Pillow
python AmberViewer.py
```

To open a specific image directly:

```bash
python AmberViewer.py path/to/image.tga
```

## License

See the [LICENSE](https://github.com/griffin20244/AmberViewer/blob/main/LICENSE) file for licensing terms.

---
**In short:** If you want to open TGA files more easily than ever, AmberViewer is the tool for you.

<p align="center">Made with 🟡 and Python.</p>


