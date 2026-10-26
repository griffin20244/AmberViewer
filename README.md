<div align="center">

# 🟡 AmberViewer

**A fast, minimal, dark image viewer with an amber soul.**
One Python file. No bloat. Built for people who open a lot of textures.

![Python](https://img.shields.io/badge/python-3.8%2B-d1a411?style=flat-square&logo=python&logoColor=black&labelColor=000000)
![Pillow](https://img.shields.io/badge/powered%20by-Pillow-d1a411?style=flat-square&labelColor=000000)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-d1a411?style=flat-square&labelColor=000000)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-d1a411?style=flat-square&labelColor=000000)

</div>

---

## ✨ Features

- **Wide format support** — TGA, PNG, JPEG, BMP, GIF, TIFF, WebP, ICO and DDS
- **Smooth zoom & pan** — scroll to zoom around the cursor, drag to pan, double-click to toggle Fit / 100%
- **Low memory footprint** — only the visible part of the image is rendered, so 8000×8000 textures at 3200% zoom don't eat your RAM
- **Snappy by design** — fast resampling while you interact, then a crisp Lanczos pass the moment you stop
- **Pixel-perfect zoom** — nearest-neighbour above 300% so you can inspect individual pixels
- **Transparency done right** — alpha channels are shown over a checkerboard instead of being swallowed by the black background
- **Folder browsing** — `←` / `→` to flip through every image in the folder; unreadable files are skipped, not fatal
- **Animation support** — animated GIF, WebP and APNG play back, `Space` pauses
- **EXIF-aware** — phone photos show up the right way round
- **16-bit grayscale** — depth maps and heightmaps are scaled sensibly instead of clipped
- **Save / convert** — export the current image to PNG, JPEG, BMP, GIF, TIFF, WebP or TGA
- **"Open with" ready** — pass a file path as an argument and it opens straight away
- **HiDPI friendly** on Windows

## 📦 Installation

```bash
pip install pillow
```

Then grab `amber_viewer.py` from this repo (clone it or download it as a ZIP) and run it.

> **Linux:** Tkinter is packaged separately on most distros.
> `sudo apt install python3-tk` (Debian/Ubuntu) · `sudo dnf install python3-tkinter` (Fedora)

## 🚀 Usage

```bash
python amber_viewer.py                 # launch empty, then Ctrl+O
python amber_viewer.py path/to/image.tga   # open a file directly
```

### Mouse

| Action | Result |
|---|---|
| Scroll wheel | Zoom in / out around the cursor |
| Click + drag | Pan the image |
| Double-click | Toggle between Fit and 100% (at the cursor) |

### Keyboard

| Key | Action |
|---|---|
| `Ctrl` + `O` | Open an image |
| `Ctrl` + `S` | Save / convert the current image |
| `←` / `→` | Previous / next image in the folder |
| `Ctrl` + `+` / `Ctrl` + `-` | Zoom in / out |
| `F` or `Ctrl` + `0` | Fit to window |
| `1` | Actual size (100%) |
| `Space` | Play / pause animation |

## 🖼️ Supported formats

| Format | Open | Save | Notes |
|---|:---:|:---:|---|
| PNG | ✅ | ✅ | APNG animation supported |
| JPEG | ✅ | ✅ | Alpha is flattened onto white on save |
| TGA | ✅ | ✅ | Alpha preserved |
| BMP | ✅ | ✅ | |
| GIF | ✅ | ✅ | Animated playback; saves the current frame only |
| TIFF | ✅ | ✅ | Only the first page is shown |
| WebP | ✅ | ✅ | Animated playback supported |
| ICO | ✅ | — | |
| DDS | ✅ | — | Depends on your Pillow version (DXT1/3/5 are widely supported) |

## 🛠️ Build a standalone executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AmberViewer amber_viewer.py
```

The result lands in `dist/`. On Windows you can then right-click an image →
**Open with** → pick `AmberViewer.exe`.

## 🎨 Make it yours

All colors live at the top of `AmberViewer.__init__`:

```python
self.accent       = "#d1a411"   # the amber
self.accent_hover = "#f0c93a"
self.bg           = "#000000"
self.muted        = "#9a9a9a"
self.checker_a    = (38, 38, 38)   # transparency checkerboard
self.checker_b    = (62, 62, 62)
```

Zoom limits, animation memory budget and the high-quality re-render delay are
constants at the top of the file (`MIN_ZOOM`, `MAX_ZOOM`, `MAX_FRAME_BYTES`,
`HQ_DELAY_MS`).

## ⚠️ Known limitations

- Saving an animated image writes only the currently displayed frame.
- Multi-page TIFFs show their first page only.
- Very large animations are truncated to a ~400 MB frame budget to keep memory in check.
- No image editing — it's a viewer (with a convert-on-save escape hatch).

## 🗺️ Ideas for later

- [ ] Drag & drop files onto the window
- [ ] Slideshow mode
- [ ] Channel view (R / G / B / A) for texture work
- [ ] Copy image to clipboard
- [ ] Pixel inspector (coordinates + RGBA under the cursor)

---

<div align="center">
<sub>Made with 🟡 and Python.</sub>
</div>
