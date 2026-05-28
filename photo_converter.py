from __future__ import annotations

import os
from pathlib import Path
from tkinter import BooleanVar, IntVar, StringVar, Tk, filedialog, messagebox
from tkinter import font as tkfont
from tkinter import ttk

from PIL import Image, ImageOps, features

try:
    from pillow_heif import register_heif_opener
except ImportError:
    register_heif_opener = None
else:
    register_heif_opener()

try:
    import rawpy
except ImportError:
    rawpy = None

INPUT_TYPES = [
    (
        "Image files",
        "*.jpg *.jpeg *.jpe *.png *.heic *.heif *.hif *.webp *.avif *.dng *.raw *.nef *.cr2 *.cr3 *.arw *.rw2 *.orf *.raf *.bmp *.dib *.gif "
        "*.tif *.tiff *.ico *.cur *.jfif *.pjpeg *.pjp *.apng *.ppm *.pgm *.pbm *.pnm "
        "*.tga *.icb *.vda *.vst *.dds *.blp *.pcx *.sgi *.bw *.rgb *.rgba *.pdf",
    ),
    ("Phone photos", "*.jpg *.jpeg *.png *.heic *.heif *.hif *.webp *.avif *.dng"),
    ("iPhone photos", "*.heic *.heif *.hif *.jpg *.jpeg *.png"),
    ("Android photos", "*.jpg *.jpeg *.png *.webp *.heic *.heif *.avif *.dng"),
    ("HEIC / HEIF", "*.heic *.heif *.hif"),
    ("AVIF", "*.avif"),
    ("PNG", "*.png"),
    ("JPEG", "*.jpg *.jpeg"),
    ("WebP", "*.webp"),
    ("BMP", "*.bmp"),
    ("GIF", "*.gif"),
    ("TIFF", "*.tif *.tiff"),
    ("ICO", "*.ico"),
    ("All files", "*.*"),
]

OUTPUT_FORMATS = {
    "PNG": {"ext": ".png", "pil": "PNG", "lossy": False, "alpha": True},
    "JPEG": {"ext": ".jpg", "pil": "JPEG", "lossy": True, "alpha": False},
    "WebP": {"ext": ".webp", "pil": "WEBP", "lossy": True, "alpha": True, "feature": "webp"},
    "AVIF": {"ext": ".avif", "pil": "AVIF", "lossy": True, "alpha": True, "feature": "avif"},
    "HEIC": {"ext": ".heic", "pil": "HEIF", "lossy": True, "alpha": True, "requires_heif": True},
    "HEIF": {"ext": ".heif", "pil": "HEIF", "lossy": True, "alpha": True, "requires_heif": True},
    "BMP": {"ext": ".bmp", "pil": "BMP", "lossy": False, "alpha": False},
    "TIFF": {"ext": ".tiff", "pil": "TIFF", "lossy": False, "alpha": True},
    "GIF": {"ext": ".gif", "pil": "GIF", "lossy": False, "alpha": False},
    "ICO": {"ext": ".ico", "pil": "ICO", "lossy": False, "alpha": True},
    "PDF": {"ext": ".pdf", "pil": "PDF", "lossy": False, "alpha": False},
    "TGA": {"ext": ".tga", "pil": "TGA", "lossy": False, "alpha": True},
    "PPM": {"ext": ".ppm", "pil": "PPM", "lossy": False, "alpha": False},
}


def available_formats() -> list[str]:
    formats = []
    for name, options in OUTPUT_FORMATS.items():
        feature = options.get("feature")
        if feature and not features.check(feature):
            continue
        if options.get("requires_heif") and register_heif_opener is None:
            continue
        formats.append(name)
    return formats


class PhotoConverter:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("사진 포맷 변환기")
        self.root.geometry("820x560")
        self.root.minsize(740, 500)
        self._configure_fonts()

        self.files: list[Path] = []
        self.output_dir = StringVar(value=str(Path.cwd() / "converted"))
        self.formats = available_formats()
        self.output_format = StringVar(value=self.formats[0])
        self.quality = IntVar(value=92)
        self.keep_exif = BooleanVar(value=True)
        self.resize_enabled = BooleanVar(value=False)
        self.max_width = IntVar(value=1920)
        self.max_height = IntVar(value=1080)
        self.status = StringVar(value="파일을 추가하세요.")

        self._build_ui()
        self._update_notice()

    def _configure_fonts(self) -> None:
        font_name = "Malgun Gothic"
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            tkfont.nametofont(name).configure(family=font_name)

        style = ttk.Style(self.root)
        style.configure(".", font=(font_name, 10))
        style.configure("Treeview", font=(font_name, 10))
        style.configure("Treeview.Heading", font=(font_name, 10, "bold"))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(16, 14, 16, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="사진 포맷 변환기", font=("Malgun Gothic", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="로컬에서 변환합니다. 서버 업로드는 없습니다.", foreground="#5f6b7a").grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(self.root, padding=(16, 8, 16, 12))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        file_area = ttk.Frame(body)
        file_area.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        file_area.columnconfigure(0, weight=1)
        file_area.rowconfigure(1, weight=1)

        file_buttons = ttk.Frame(file_area)
        file_buttons.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(file_buttons, text="파일 추가", command=self.add_files).pack(side="left")
        ttk.Button(file_buttons, text="목록 비우기", command=self.clear_files).pack(side="left", padx=(8, 0))

        self.file_list = ttk.Treeview(file_area, columns=("name", "format", "size"), show="headings", selectmode="extended")
        self.file_list.heading("name", text="파일")
        self.file_list.heading("format", text="형식")
        self.file_list.heading("size", text="크기")
        self.file_list.column("name", width=360, anchor="w")
        self.file_list.column("format", width=110, anchor="center")
        self.file_list.column("size", width=110, anchor="e")
        self.file_list.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(file_area, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        options = ttk.Frame(body, padding=14)
        options.grid(row=0, column=1, sticky="ns")

        ttk.Label(options, text="출력 폴더").grid(row=0, column=0, sticky="w")
        output_row = ttk.Frame(options)
        output_row.grid(row=1, column=0, sticky="ew", pady=(6, 14))
        output_row.columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self.output_dir, width=28).grid(row=0, column=0, sticky="ew")
        ttk.Button(output_row, text="선택", command=self.choose_output_dir).grid(row=0, column=1, padx=(6, 0))

        ttk.Label(options, text="변환 포맷").grid(row=2, column=0, sticky="w")
        format_box = ttk.Combobox(options, textvariable=self.output_format, values=self.formats, state="readonly", width=18)
        format_box.grid(row=3, column=0, sticky="ew", pady=(6, 12))
        format_box.bind("<<ComboboxSelected>>", lambda _event: self._update_notice())

        self.notice_label = ttk.Label(options, wraplength=260, foreground="#5f6b7a")
        self.notice_label.grid(row=4, column=0, sticky="ew", pady=(0, 14))

        ttk.Label(options, text="품질").grid(row=5, column=0, sticky="w")
        quality_row = ttk.Frame(options)
        quality_row.grid(row=6, column=0, sticky="ew", pady=(6, 14))
        ttk.Scale(quality_row, from_=40, to=100, variable=self.quality, orient="horizontal").pack(side="left", fill="x", expand=True)
        ttk.Label(quality_row, textvariable=self.quality, width=4).pack(side="left", padx=(8, 0))

        ttk.Checkbutton(options, text="EXIF 보존", variable=self.keep_exif).grid(row=7, column=0, sticky="w", pady=(0, 10))
        ttk.Checkbutton(options, text="최대 크기 제한", variable=self.resize_enabled, command=self._toggle_resize).grid(row=8, column=0, sticky="w")

        resize_row = ttk.Frame(options)
        resize_row.grid(row=9, column=0, sticky="ew", pady=(6, 14))
        self.width_entry = ttk.Entry(resize_row, textvariable=self.max_width, width=8, state="disabled")
        self.height_entry = ttk.Entry(resize_row, textvariable=self.max_height, width=8, state="disabled")
        self.width_entry.pack(side="left")
        ttk.Label(resize_row, text=" x ").pack(side="left")
        self.height_entry.pack(side="left")

        ttk.Button(options, text="변환 시작", command=self.convert).grid(row=10, column=0, sticky="ew", pady=(8, 0))

        footer = ttk.Frame(self.root, padding=(16, 0, 16, 14))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(footer, textvariable=self.status).grid(row=0, column=1, sticky="e")

    def _toggle_resize(self) -> None:
        state = "normal" if self.resize_enabled.get() else "disabled"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)

    def _update_notice(self) -> None:
        fmt = self.output_format.get()
        if OUTPUT_FORMATS[fmt]["lossy"]:
            text = f"{fmt}는 손실 압축입니다. 품질 100도 원본과 완전히 같지는 않습니다."
        else:
            text = f"{fmt} 저장은 기본적으로 무손실입니다. 단, 크기 변경이나 색상 모드 변환이 있으면 픽셀 값은 바뀔 수 있습니다."
        if fmt in {"ICO", "GIF"}:
            text += " 이 포맷은 색상/크기 제한 때문에 원본과 표현이 달라질 수 있습니다."
        self.notice_label.configure(text=text)

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="사진 선택", filetypes=INPUT_TYPES)
        for name in selected:
            path = Path(name)
            if path not in self.files:
                self.files.append(path)
        self.refresh_file_list()

    def clear_files(self) -> None:
        self.files.clear()
        self.refresh_file_list()

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="출력 폴더 선택", initialdir=self.output_dir.get())
        if selected:
            self.output_dir.set(selected)

    def refresh_file_list(self) -> None:
        self.file_list.delete(*self.file_list.get_children())
        for path in self.files:
            size = path.stat().st_size if path.exists() else 0
            self.file_list.insert("", "end", values=(path.name, path.suffix.lower() or "unknown", self._format_bytes(size)))
        self.status.set(f"{len(self.files)}개 파일 선택됨" if self.files else "파일을 추가하세요.")

    def convert(self) -> None:
        if not self.files:
            messagebox.showwarning("파일 없음", "변환할 사진을 먼저 추가하세요.")
            return

        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        self.progress.configure(maximum=len(self.files), value=0)
        failures: list[str] = []

        for index, source in enumerate(self.files, start=1):
            self.status.set(f"변환 중: {source.name}")
            self.root.update_idletasks()

            try:
                self._convert_one(source, output_path)
            except Exception as exc:
                failures.append(f"{source.name}: {exc}")

            self.progress.configure(value=index)

        if failures:
            messagebox.showwarning("일부 실패", "\n".join(failures[:8]))
            self.status.set(f"완료, 실패 {len(failures)}개")
        else:
            messagebox.showinfo("완료", f"{len(self.files)}개 파일을 변환했습니다.")
            self.status.set("변환 완료")

        if os.name == "nt":
            os.startfile(output_path)

    def _convert_one(self, source: Path, output_dir: Path) -> None:
        fmt_name = self.output_format.get()
        fmt = OUTPUT_FORMATS[fmt_name]
        target = self._unique_target(output_dir / f"{source.stem}{fmt['ext']}")

        with self._open_image(source) as image:
            exif = image.info.get("exif") if self.keep_exif.get() else None
            image = ImageOps.exif_transpose(image)

            if self.resize_enabled.get():
                image.thumbnail((self.max_width.get(), self.max_height.get()), Image.Resampling.LANCZOS)

            save_kwargs = {}
            if fmt_name in {"JPEG", "WebP", "AVIF", "HEIC", "HEIF"}:
                save_kwargs["quality"] = self.quality.get()
                save_kwargs["method"] = 6 if fmt_name == "WebP" else None
            if fmt_name == "JPEG":
                image = self._flatten_for_jpeg(image)
                save_kwargs["optimize"] = True
            elif not fmt.get("alpha", True) and image.mode in {"RGBA", "LA"}:
                image = self._flatten_for_jpeg(image)
            elif fmt_name == "GIF":
                image = image.convert("P", palette=Image.Palette.ADAPTIVE)
            elif fmt_name == "ICO":
                image = image.convert("RGBA")
            elif fmt_name == "PDF":
                image = self._flatten_for_jpeg(image)
            elif image.mode == "P":
                image = image.convert("RGBA")

            if exif and fmt_name in {"JPEG", "WebP", "TIFF", "HEIC", "HEIF", "AVIF"}:
                save_kwargs["exif"] = exif

            save_kwargs = {key: value for key, value in save_kwargs.items() if value is not None}
            image.save(target, fmt["pil"], **save_kwargs)

    @staticmethod
    def _open_image(source: Path) -> Image.Image:
        if source.suffix.lower() in {".dng", ".raw", ".nef", ".cr2", ".cr3", ".arw", ".rw2", ".orf", ".raf"}:
            if rawpy is None:
                raise RuntimeError("RAW/DNG 입력은 rawpy 설치가 필요합니다.")
            with rawpy.imread(str(source)) as raw:
                rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=8)
            return Image.fromarray(rgb)
        return Image.open(source)

    @staticmethod
    def _flatten_for_jpeg(image: Image.Image) -> Image.Image:
        if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
            background = Image.new("RGB", image.size, "white")
            background.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
            return background
        return image.convert("RGB")

    @staticmethod
    def _unique_target(path: Path) -> Path:
        if not path.exists():
            return path

        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _format_bytes(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / 1024 / 1024:.1f} MB"


def main() -> None:
    root = Tk()
    try:
        root.call("tk", "scaling", 1.2)
    except Exception:
        pass
    PhotoConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
