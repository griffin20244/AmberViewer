import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageSequence, ImageTk

try:
    _R = Image.Resampling
    NEAREST, BILINEAR, LANCZOS = _R.NEAREST, _R.BILINEAR, _R.LANCZOS
except AttributeError:  # Pillow < 9.1
    NEAREST, BILINEAR, LANCZOS = Image.NEAREST, Image.BILINEAR, Image.LANCZOS


APP_NAME = "AmberViewer"
SUPPORTED_EXTENSIONS = {
    ".tga", ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".tif", ".tiff", ".webp", ".ico", ".dds",
}
ANIMATED_FORMATS = {"GIF", "WEBP", "PNG"}
MAX_FRAMES = 500
MAX_FRAME_BYTES = 400 * 1024 * 1024
MIN_ZOOM, MAX_ZOOM = 0.02, 32.0
ZOOM_STEP = 1.2
HQ_DELAY_MS = 150


def resource_path(filename):
    """Return a resource path for source runs and PyInstaller bundles."""
    base_path = getattr(
        sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base_path, filename)


class AmberViewer:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x700")
        self.root.minsize(640, 420)

        self.bg = "#000000"
        self.panel = "#000000"
        self.accent = "#d1a411"
        self.accent_hover = "#f0c93a"
        self.text = "#FFFFFF"
        self.muted = "#9a9a9a"
        self.canvas_bg = "#000000"
        self.button_text_on_accent = "#000000"
        self.checker_a = (38, 38, 38)
        self.checker_b = (62, 62, 62)

        # image state
        self.source_image = None
        self.frames = []
        self.durations = []
        self.frame_index = 0
        self.playing = True
        self.photo = None
        self.current_path = None

        # view state
        self.fit_mode = True
        self.zoom = 1.0          # absolute scale, used when fit_mode is False
        self.offset = [0.0, 0.0]  # pan offset from canvas center, in pixels

        # folder navigation cache
        self.folder_dir = None
        self.folder_mtime = None
        self.folder_images = []

        # internals
        self._hq_job = None
        self._anim_job = None
        self._drag_last = None
        self._checker = None

        self.root.configure(bg=self.bg)
        self._build_ui()
        self._bind_shortcuts()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        try:
            ttk.Style().theme_use("clam")
        except tk.TclError:
            pass

        style = ttk.Style()
        style.configure(
            "Amber.TButton",
            background=self.accent,
            foreground=self.button_text_on_accent,
            padding=(12, 7),
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.map(
            "Amber.TButton",
            background=[
                ("active", self.accent_hover),
                ("pressed", self.accent_hover),
            ],
            foreground=[("active", self.button_text_on_accent)],
        )
        style.configure(
            "Plain.TButton",
            background=self.panel,
            foreground=self.text,
            padding=(10, 7),
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.map(
            "Plain.TButton",
            background=[
                ("active", self.accent),
                ("pressed", self.accent),
            ],
            foreground=[
                ("active", self.button_text_on_accent),
                ("pressed", self.button_text_on_accent),
            ],
        )

        toolbar = tk.Frame(self.root, bg=self.panel, padx=12, pady=10)
        toolbar.pack(side="top", fill="x")

        tk.Label(
            toolbar,
            text=APP_NAME,
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left", padx=(2, 16))

        self._button(toolbar, "Open", self.open_file, "Amber.TButton")
        self._button(toolbar, "Save", self.save_as)

        tk.Frame(toolbar, bg="#444444", width=1, height=28).pack(
            side="left", padx=10
        )

        self._button(toolbar, "−", self.zoom_out, width=3, padx=2)
        self._button(toolbar, "Fit", self.fit_image, padx=2)
        self._button(toolbar, "1:1", self.actual_size, padx=2)
        self._button(toolbar, "+", self.zoom_in, width=3, padx=2)

        # Pack Next first so that "Prev" appears to its left.
        self._button(toolbar, "Next", self.next_image, side="right")
        self._button(toolbar, "Prev", self.prev_image, side="right")

        # Footer first, so it never gets clipped when the window is small.
        footer = tk.Frame(self.root, bg=self.bg, padx=15, pady=7)
        footer.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Open an image to get started")
        tk.Label(
            footer,
            textvariable=self.status_var,
            bg=self.bg,
            fg=self.muted,
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(side="left", fill="x", expand=True)

        self.zoom_var = tk.StringVar(value="")
        tk.Label(
            footer,
            textvariable=self.zoom_var,
            bg=self.bg,
            fg=self.muted,
            font=("Segoe UI", 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(
            self.root,
            bg=self.canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self._wheel_zoom(True, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self._wheel_zoom(False, e.x, e.y))
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.canvas.bind("<Double-Button-1>", self._toggle_zoom)

    def _button(self, parent, text, command, style="Plain.TButton",
                side="left", padx=3, width=None):
        # takefocus=False: otherwise Space would re-trigger the last
        # clicked button instead of toggling animation.
        kwargs = {"takefocus": False}
        if width is not None:
            kwargs["width"] = width
        button = ttk.Button(
            parent, text=text, style=style, command=command, **kwargs
        )
        button.pack(side=side, padx=padx)
        return button

    def _bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda _e: self.open_file())
        self.root.bind("<Control-s>", lambda _e: self.save_as())
        self.root.bind("<Control-plus>", lambda _e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda _e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda _e: self.zoom_out())
        self.root.bind("<Control-0>", lambda _e: self.fit_image())
        self.root.bind("<Key-f>", lambda _e: self.fit_image())
        self.root.bind("<Key-1>", lambda _e: self.actual_size())
        self.root.bind("<space>", lambda _e: self.toggle_play())
        self.root.bind("<Left>", lambda _e: self.prev_image())
        self.root.bind("<Right>", lambda _e: self.next_image())

    # ------------------------------------------------------------- loading

    def open_file(self):
        initial = os.path.dirname(self.current_path) if self.current_path else None
        path = filedialog.askopenfilename(
            title="Open image",
            initialdir=initial,
            filetypes=[
                (
                    "Image files",
                    "*.tga *.png *.jpg *.jpeg *.bmp *.gif "
                    "*.tif *.tiff *.webp *.ico *.dds",
                ),
                ("TGA images", "*.tga"),
                ("DDS textures", "*.dds"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._load_image(path, refresh_list=True)

    def _to_display(self, image):
        """Convert any Pillow image into something Tk-friendly (RGB/RGBA)."""
        if image.mode.startswith("I") or image.mode == "F":
            # 16-bit / 32-bit grayscale: scale into 8 bits instead of clipping.
            try:
                image = image.convert("I")
                _low, high = image.getextrema()
                if high > 255:
                    factor = 255.0 / high
                    image = image.point(lambda i: i * factor)
                image = image.convert("L")
            except Exception:
                image = image.convert("L")

        has_alpha = "A" in image.getbands() or "transparency" in image.info
        return image.convert("RGBA" if has_alpha else "RGB")

    def _read_frames(self, path):
        frames, durations = [], []
        with Image.open(path) as image:
            animated = (
                image.format in ANIMATED_FORMATS
                and getattr(image, "n_frames", 1) > 1
            )
            if animated:
                total_bytes = 0
                for index, frame in enumerate(ImageSequence.Iterator(image)):
                    if index >= MAX_FRAMES:
                        break
                    converted = self._to_display(frame)
                    total_bytes += converted.width * converted.height * 4
                    if frames and total_bytes > MAX_FRAME_BYTES:
                        break
                    frames.append(converted)
                    durations.append(max(20, int(frame.info.get("duration") or 100)))
            else:
                image.load()
                frames.append(self._to_display(ImageOps.exif_transpose(image)))
                durations.append(0)
        return frames, durations

    def _load_image(self, path, refresh_list=True, silent=False):
        try:
            frames, durations = self._read_frames(path)
        except Exception as error:
            if not silent:
                messagebox.showerror(
                    "Unable to open image",
                    f"Could not open this image:\n{error}",
                    parent=self.root,
                )
            return False

        self._stop_animation()
        self.frames = frames
        self.durations = durations
        self.frame_index = 0
        self.source_image = frames[0]
        self.current_path = os.path.abspath(path)

        self.fit_mode = True
        self.zoom = 1.0
        self.offset = [0.0, 0.0]

        self._ensure_folder_list(force=refresh_list)
        self.root.title(f"{os.path.basename(self.current_path)} — {APP_NAME}")
        self._update_status()
        self._render("hq")
        self._start_animation()
        return True

    # ---------------------------------------------------- folder navigation

    def _ensure_folder_list(self, force=False):
        folder = os.path.dirname(self.current_path)
        try:
            mtime = os.path.getmtime(folder)
        except OSError:
            mtime = None

        if (
            not force
            and folder == self.folder_dir
            and mtime == self.folder_mtime
        ):
            return

        try:
            names = sorted(os.listdir(folder), key=str.casefold)
        except OSError:
            names = []

        self.folder_dir = folder
        self.folder_mtime = mtime
        self.folder_images = [
            os.path.join(folder, name)
            for name in names
            if os.path.splitext(name)[1].lower() in SUPPORTED_EXTENSIONS
        ]

    def _change_image(self, step):
        if not self.current_path:
            return

        self._ensure_folder_list()
        if self.current_path not in self.folder_images:
            self._ensure_folder_list(force=True)
        if self.current_path not in self.folder_images:
            return

        count = len(self.folder_images)
        index = self.folder_images.index(self.current_path)
        skipped = 0

        for _ in range(count - 1):
            index = (index + step) % count
            if self._load_image(
                self.folder_images[index], refresh_list=False, silent=True
            ):
                if skipped:
                    self.status_var.set(
                        self.status_var.get()
                        + f"  ·  skipped {skipped} unreadable"
                    )
                return
            skipped += 1

        self.status_var.set("No other readable images in this folder")

    def prev_image(self):
        self._change_image(-1)

    def next_image(self):
        self._change_image(1)

    def _update_status(self):
        width, height = self.source_image.size
        parts = [os.path.basename(self.current_path), f"{width:,} × {height:,} px"]
        if len(self.frames) > 1:
            parts.append(f"{len(self.frames)} frames")
        try:
            position = self.folder_images.index(self.current_path) + 1
            parts.append(f"{position}/{len(self.folder_images)}")
        except ValueError:
            pass
        self.status_var.set("  ·  ".join(parts))

    # ----------------------------------------------------------- animation

    def _start_animation(self):
        self._stop_animation()
        if self.playing and len(self.frames) > 1:
            delay = self.durations[self.frame_index]
            self._anim_job = self.root.after(delay, self._tick)

    def _stop_animation(self):
        if self._anim_job is not None:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None

    def _tick(self):
        self._anim_job = None
        if len(self.frames) < 2:
            return
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.source_image = self.frames[self.frame_index]
        self._render("fast")
        self._start_animation()

    def toggle_play(self):
        if len(self.frames) < 2:
            return
        self.playing = not self.playing
        if self.playing:
            self._start_animation()
        else:
            self._stop_animation()

    # ----------------------------------------------------------- rendering

    def _canvas_size(self):
        return max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)

    def _fit_scale(self, cw, ch):
        iw, ih = self.source_image.size
        return min(cw / iw, ch / ih, 1.0)

    def _scale(self, cw, ch):
        return self._fit_scale(cw, ch) if self.fit_mode else self.zoom

    def _get_checker(self, width, height):
        if (
            self._checker is None
            or self._checker.width < width
            or self._checker.height < height
        ):
            self._checker = self._build_checker(width + 32, height + 32)
        return self._checker

    def _build_checker(self, width, height, cell=8):
        tile = Image.new("RGB", (cell * 2, cell * 2), self.checker_a)
        tile.paste(self.checker_b, (0, 0, cell, cell))
        tile.paste(self.checker_b, (cell, cell, cell * 2, cell * 2))

        row = Image.new("RGB", (width, cell * 2))
        for x in range(0, width, cell * 2):
            row.paste(tile, (x, 0))

        full = Image.new("RGB", (width, height))
        for y in range(0, height, cell * 2):
            full.paste(row, (0, y))
        return full

    def _render(self, quality="hq"):
        """Render only the visible part of the image.

        quality: "fast" (bilinear, used while interacting) or "hq" (Lanczos).
        """
        if self.source_image is None:
            return

        cw, ch = self._canvas_size()
        iw, ih = self.source_image.size
        scale = self._scale(cw, ch)
        dw, dh = iw * scale, ih * scale

        # Keep the image reachable: allow panning only along overflowing axes.
        if self.fit_mode:
            self.offset = [0.0, 0.0]
        else:
            max_x = max(0.0, (dw - cw) / 2)
            max_y = max(0.0, (dh - ch) / 2)
            self.offset[0] = max(-max_x, min(max_x, self.offset[0]))
            self.offset[1] = max(-max_y, min(max_y, self.offset[1]))

        x0 = cw / 2 + self.offset[0] - dw / 2
        y0 = ch / 2 + self.offset[1] - dh / 2

        # Visible rectangle in displayed-image coordinates.
        vx0, vy0 = max(0.0, -x0), max(0.0, -y0)
        vx1, vy1 = min(dw, cw - x0), min(dh, ch - y0)

        old_items = self.canvas.find_withtag("img")
        self.zoom_var.set(f"{round(scale * 100)}%")

        if vx1 - vx0 < 1 or vy1 - vy0 < 1:
            for item in old_items:
                self.canvas.delete(item)
            return

        out_w = max(1, round(vx1 - vx0))
        out_h = max(1, round(vy1 - vy0))
        box = (
            max(0.0, vx0 / scale),
            max(0.0, vy0 / scale),
            min(float(iw), vx1 / scale),
            min(float(ih), vy1 / scale),
        )

        if scale >= 3:
            resample = NEAREST  # crisp pixels when zoomed way in
        elif quality == "fast":
            resample = BILINEAR
        else:
            resample = LANCZOS

        region = self.source_image.resize((out_w, out_h), resample, box=box)
        px = int(round(x0 + vx0))
        py = int(round(y0 + vy0))

        if region.mode == "RGBA":
            backdrop = self._get_checker(cw, ch).crop(
                (px, py, px + out_w, py + out_h)
            )
            backdrop.paste(region.convert("RGB"), (0, 0), region.getchannel("A"))
            region = backdrop

        self.photo = ImageTk.PhotoImage(region)
        self.canvas.create_image(
            px, py, image=self.photo, anchor="nw", tags="img"
        )
        for item in old_items:
            self.canvas.delete(item)

    def _render_interactive(self):
        """Fast render now, high-quality render once the user stops."""
        self._render("fast")
        if self._hq_job is not None:
            self.root.after_cancel(self._hq_job)
        self._hq_job = self.root.after(HQ_DELAY_MS, self._render_hq)

    def _render_hq(self):
        self._hq_job = None
        self._render("hq")

    # ---------------------------------------------------------- zoom / pan

    def _on_resize(self, _event):
        if self.source_image is not None:
            self._render_interactive()

    def _on_mousewheel(self, event):
        if event.delta:
            self._wheel_zoom(event.delta > 0, event.x, event.y)

    def _wheel_zoom(self, zoom_in, x, y):
        factor = ZOOM_STEP if zoom_in else 1 / ZOOM_STEP
        self._zoom_by(factor, x, y)

    def _zoom_by(self, factor, px=None, py=None):
        if self.source_image is None:
            return
        cw, ch = self._canvas_size()
        self._zoom_to(self._scale(cw, ch) * factor, px, py)

    def _zoom_to(self, new_scale, px=None, py=None):
        """Zoom to an absolute scale, keeping the point (px, py) fixed."""
        if self.source_image is None:
            return

        cw, ch = self._canvas_size()
        current = self._scale(cw, ch)
        new_scale = max(MIN_ZOOM, min(MAX_ZOOM, new_scale))

        if px is None or py is None:
            px, py = cw / 2, ch / 2

        # Image-space point currently under the cursor.
        ux = (px - cw / 2 - self.offset[0]) / current
        uy = (py - ch / 2 - self.offset[1]) / current

        self.offset = [
            px - cw / 2 - ux * new_scale,
            py - ch / 2 - uy * new_scale,
        ]
        self.zoom = new_scale
        self.fit_mode = False
        self._render_interactive()

    def zoom_in(self):
        self._zoom_by(ZOOM_STEP)

    def zoom_out(self):
        self._zoom_by(1 / ZOOM_STEP)

    def actual_size(self):
        self._zoom_to(1.0)

    def fit_image(self):
        if self.source_image is None:
            return
        self.fit_mode = True
        self.zoom = 1.0
        self.offset = [0.0, 0.0]
        self._render_interactive()

    def _toggle_zoom(self, event):
        if self.source_image is None:
            return
        if self.fit_mode:
            self._zoom_to(1.0, event.x, event.y)
        else:
            self.fit_image()

    def _drag_start(self, event):
        self._drag_last = (event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _drag_move(self, event):
        if self.source_image is None or self._drag_last is None:
            return
        self.offset[0] += event.x - self._drag_last[0]
        self.offset[1] += event.y - self._drag_last[1]
        self._drag_last = (event.x, event.y)
        self._render_interactive()

    def _drag_end(self, _event):
        self._drag_last = None
        self.canvas.configure(cursor="")

    # -------------------------------------------------------------- saving

    def save_as(self):
        if self.source_image is None:
            messagebox.showinfo("Save", "Open an image first.", parent=self.root)
            return

        initial_name = os.path.splitext(os.path.basename(self.current_path))[0]

        path = filedialog.asksaveasfilename(
            title="Save image as",
            initialdir=os.path.dirname(self.current_path),
            initialfile=initial_name,
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("JPEG image", "*.jpg *.jpeg"),
                ("BMP image", "*.bmp"),
                ("GIF image", "*.gif"),
                ("TIFF image", "*.tif *.tiff"),
                ("WebP image", "*.webp"),
                ("TGA image", "*.tga"),
            ],
            confirmoverwrite=True,
        )
        if not path:
            return

        extension = os.path.splitext(path)[1].lower()
        format_by_extension = {
            ".png": "PNG",
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".bmp": "BMP",
            ".gif": "GIF",
            ".tif": "TIFF",
            ".tiff": "TIFF",
            ".webp": "WEBP",
            ".tga": "TGA",
        }
        image_format = format_by_extension.get(extension)

        if image_format is None:
            messagebox.showerror(
                "Unsupported format",
                "Choose a supported image file extension.",
                parent=self.root,
            )
            return

        try:
            image = self.source_image

            if image_format == "JPEG":
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=image.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")
            elif image_format == "BMP":
                image = image.convert("RGB")

            image.save(path, format=image_format)
        except Exception as error:
            messagebox.showerror(
                "Unable to save image",
                f"Could not save this image:\n{error}",
                parent=self.root,
            )
            return

        self.status_var.set(f"Saved as {os.path.basename(path)}")


def main():
    if sys.platform == "win32":
        try:  # crisp rendering on high-DPI displays
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    try:
        root.iconbitmap(resource_path("icon.ico"))
    except (tk.TclError, OSError):
        # Keep the viewer usable if the optional icon resource is unavailable.
        pass

    app = AmberViewer(root)

    # "Open with" / drag a file onto the script or exe.
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        root.after_idle(lambda: app._load_image(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()
