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
        self.root.geometry("980x620")
        self.root.minsize(920, 580)
        
        self.entries: list[dict] = []
        self.output_dir = StringVar(value=str(Path.cwd() / "converted"))
        self.formats = available_formats()
        self.output_format = StringVar(value=self.formats[0])
        self.quality = IntVar(value=92)
        self.keep_exif = BooleanVar(value=True)
        self.grayscale = BooleanVar(value=False)
        self.filename_prefix = StringVar(value="")
        self.filename_suffix = StringVar(value="")
        
        self.resize_mode = StringVar(value="원본 크기")
        self.resize_pct = IntVar(value=80)
        self.max_width = IntVar(value=1920)
        self.max_height = IntVar(value=1080)
        
        self.rotate_angle = StringVar(value="0")
        self.rotate_angle_label = StringVar(value="회전 없음")
        self.flip_horizontal = BooleanVar(value=False)
        self.flip_vertical = BooleanVar(value=False)
        
        self.status = StringVar(value="파일을 추가하세요.")

        self._configure_fonts()
        self._build_ui()
        
        # Initialize UI state
        self._toggle_resize()
        self._update_notice()

    def _configure_fonts(self) -> None:
        font_name = "Malgun Gothic"
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            tkfont.nametofont(name).configure(family=font_name)

        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Palette
        bg_color = "#f8fafc"
        panel_color = "#ffffff"
        accent_color = "#4f46e5"  # Indigo
        accent_hover = "#4338ca"
        text_color = "#0f172a"
        muted_color = "#64748b"
        border_color = "#cbd5e1"

        self.root.configure(bg=bg_color)

        style.configure(".", font=(font_name, 10), background=bg_color, foreground=text_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, bordercolor=border_color)
        style.configure("TLabelframe.Label", font=(font_name, 10, "bold"), background=bg_color, foreground=accent_color)
        
        style.configure("TLabel", background=bg_color, foreground=text_color)
        style.configure("Header.TLabel", font=(font_name, 18, "bold"), background=bg_color, foreground=text_color)
        style.configure("Subheader.TLabel", font=(font_name, 9), background=bg_color, foreground=muted_color)
        style.configure("Notice.TLabel", font=(font_name, 9), background="#eff6ff", foreground="#1e3a8a", borderwidth=1, relief="flat")

        # Flat button styles
        style.configure("TButton", font=(font_name, 10, "bold"), borderwidth=1, focuscolor="", relief="flat")
        style.configure("Primary.TButton", background=accent_color, foreground="#ffffff")
        style.map("Primary.TButton", 
                  background=[("active", accent_hover), ("pressed", accent_hover), ("disabled", "#e2e8f0")],
                  foreground=[("disabled", "#94a3b8")])
                  
        style.configure("Secondary.TButton", background=panel_color, foreground=text_color, bordercolor=border_color)
        style.map("Secondary.TButton", 
                  background=[("active", "#f1f5f9"), ("pressed", "#e2e8f0"), ("disabled", panel_color)])

        style.configure("TEntry", bordercolor=border_color, lightcolor=border_color, darkcolor=border_color, background="#ffffff", fieldbackground="#ffffff")
        style.configure("TCombobox", bordercolor=border_color, lightcolor=border_color, darkcolor=border_color, background="#ffffff", fieldbackground="#ffffff")
        style.configure("TCheckbutton", background=bg_color, focuscolor="")
        style.configure("Horizontal.TScale", background=bg_color, bordercolor=border_color)

        # Treeview styling
        style.configure("Treeview", 
                        font=(font_name, 9), 
                        background="#ffffff", 
                        fieldbackground="#ffffff", 
                        foreground=text_color,
                        rowheight=26,
                        borderwidth=1,
                        relief="flat")
        style.configure("Treeview.Heading", font=(font_name, 9, "bold"), background="#f1f5f9", foreground=text_color, borderwidth=1, relief="flat")
        style.map("Treeview", 
                  background=[("selected", "#e0e7ff")],
                  foreground=[("selected", text_color)])

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Header
        header = ttk.Frame(self.root, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="사진 포맷 변환기", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="로컬에서 초고속으로 사진을 일괄 변환합니다. 외부 서버 전송이 없어 안전합니다.", style="Subheader.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Body
        body = ttk.Frame(self.root, padding=(16, 4, 16, 10))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        # File list area (Left)
        file_area = ttk.Frame(body)
        file_area.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        file_area.columnconfigure(0, weight=1)
        file_area.rowconfigure(1, weight=1)

        file_buttons = ttk.Frame(file_area)
        file_buttons.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(file_buttons, text="사진 파일 추가", command=self.add_files, style="Secondary.TButton").pack(side="left")
        ttk.Button(file_buttons, text="목록 비우기", command=self.clear_files, style="Secondary.TButton").pack(side="left", padx=(8, 0))

        # Table showing file conversion details
        self.file_list = ttk.Treeview(
            file_area, 
            columns=("name", "format", "orig_size", "new_name", "new_size", "ratio", "status"), 
            show="headings", 
            selectmode="extended"
        )
        self.file_list.heading("name", text="원본 파일명")
        self.file_list.heading("format", text="원래 형식")
        self.file_list.heading("orig_size", text="원본 크기")
        self.file_list.heading("new_name", text="변환 파일명")
        self.file_list.heading("new_size", text="변환 크기")
        self.file_list.heading("ratio", text="압축률")
        self.file_list.heading("status", text="상태")

        self.file_list.column("name", width=180, anchor="w")
        self.file_list.column("format", width=70, anchor="center")
        self.file_list.column("orig_size", width=80, anchor="e")
        self.file_list.column("new_name", width=180, anchor="w")
        self.file_list.column("new_size", width=80, anchor="e")
        self.file_list.column("ratio", width=70, anchor="center")
        self.file_list.column("status", width=75, anchor="center")

        self.file_list.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(file_area, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        # Options panel (Right)
        options_container = ttk.Frame(body)
        options_container.grid(row=0, column=1, sticky="ns")
        options_container.columnconfigure(0, weight=1)

        # Group 1: 저장 및 파일 설정
        save_group = ttk.LabelFrame(options_container, text=" 저장 및 파일 설정 ", padding=10)
        save_group.pack(fill="x", pady=(0, 10))
        save_group.columnconfigure(0, weight=1)
        save_group.columnconfigure(1, weight=1)

        # Format
        fmt_frame = ttk.Frame(save_group)
        fmt_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Label(fmt_frame, text="출력 포맷").pack(anchor="w")
        format_box = ttk.Combobox(fmt_frame, textvariable=self.output_format, values=self.formats, state="readonly", width=10)
        format_box.pack(fill="x", pady=(4, 0))
        format_box.bind("<<ComboboxSelected>>", lambda _event: self._update_notice())

        # Quality
        qual_frame = ttk.Frame(save_group)
        qual_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        qual_label_row = ttk.Frame(qual_frame)
        qual_label_row.pack(fill="x")
        ttk.Label(qual_label_row, text="품질").pack(side="left")
        ttk.Label(qual_label_row, textvariable=self.quality, font=("Malgun Gothic", 9, "bold")).pack(side="right")
        self.qual_scale = ttk.Scale(qual_frame, from_=40, to=100, variable=self.quality, orient="horizontal")
        self.qual_scale.pack(fill="x", pady=(4, 0))

        # Notice Label
        self.notice_label = ttk.Label(save_group, wraplength=290, style="Notice.TLabel", justify="left", padding=6)
        self.notice_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        # Prefix & Suffix
        prefix_frame = ttk.Frame(save_group)
        prefix_frame.grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        ttk.Label(prefix_frame, text="파일명 접두사").pack(anchor="w")
        ttk.Entry(prefix_frame, textvariable=self.filename_prefix).pack(fill="x", pady=(4, 0))

        suffix_frame = ttk.Frame(save_group)
        suffix_frame.grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(0, 6))
        ttk.Label(suffix_frame, text="파일명 접미사").pack(anchor="w")
        ttk.Entry(suffix_frame, textvariable=self.filename_suffix).pack(fill="x", pady=(4, 0))

        # Checkboxes
        chk_frame = ttk.Frame(save_group)
        chk_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Checkbutton(chk_frame, text="EXIF 메타데이터 보존", variable=self.keep_exif).pack(side="left")
        ttk.Checkbutton(chk_frame, text="흑백 필터", variable=self.grayscale).pack(side="left", padx=(14, 0))

        # Output Folder selector
        folder_frame = ttk.Frame(save_group)
        folder_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(folder_frame, text="저장 폴더").pack(anchor="w")
        folder_row = ttk.Frame(folder_frame)
        folder_row.pack(fill="x", pady=(4, 0))
        ttk.Entry(folder_row, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="선택", command=self.choose_output_dir, style="Secondary.TButton", width=5).pack(side="right", padx=(6, 0))

        # Group 2: 이미지 변형 및 크기 조절
        edit_group = ttk.LabelFrame(options_container, text=" 이미지 변형 및 크기 조절 ", padding=10)
        edit_group.pack(fill="x", pady=(0, 10))
        edit_group.columnconfigure(0, weight=1)
        edit_group.columnconfigure(1, weight=1)

        # Resize modes combobox
        resize_mode_frame = ttk.Frame(edit_group)
        resize_mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(resize_mode_frame, text="크기 조절 모드").pack(anchor="w")
        resize_modes = ["원본 크기", "비율 축소 (%)", "너비 고정 (px)", "높이 고정 (px)", "가로/세로 최대 제한"]
        self.resize_combo = ttk.Combobox(resize_mode_frame, textvariable=self.resize_mode, values=resize_modes, state="readonly")
        self.resize_combo.pack(fill="x", pady=(4, 0))
        self.resize_combo.bind("<<ComboboxSelected>>", self._toggle_resize)

        # Dynamic parameter frames
        self.resize_param_frame = ttk.Frame(edit_group)
        self.resize_param_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        
        # 1. Percentage Frame
        self.pct_frame = ttk.Frame(self.resize_param_frame)
        pct_lbl_row = ttk.Frame(self.pct_frame)
        pct_lbl_row.pack(fill="x")
        ttk.Label(pct_lbl_row, text="축소 비율").pack(side="left")
        ttk.Label(pct_lbl_row, textvariable=self.resize_pct, font=("Malgun Gothic", 9, "bold")).pack(side="right")
        self.pct_scale = ttk.Scale(self.pct_frame, from_=5, to=99, variable=self.resize_pct, orient="horizontal")
        self.pct_scale.pack(fill="x", pady=(4, 0))
        
        # 2. Dimensions Frame
        self.dim_frame = ttk.Frame(self.resize_param_frame)
        self.width_lbl = ttk.Label(self.dim_frame, text="가로 (px)")
        self.width_lbl.grid(row=0, column=0, sticky="w")
        self.width_entry = ttk.Entry(self.dim_frame, textvariable=self.max_width, width=8)
        self.width_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        
        self.height_lbl = ttk.Label(self.dim_frame, text="세로 (px)")
        self.height_lbl.grid(row=0, column=1, sticky="w")
        self.height_entry = ttk.Entry(self.dim_frame, textvariable=self.max_height, width=8)
        self.height_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        self.dim_frame.columnconfigure(0, weight=1)
        self.dim_frame.columnconfigure(1, weight=1)

        # Rotate & Flips
        # Rotate Combobox
        rot_frame = ttk.Frame(edit_group)
        rot_frame.grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(4, 0))
        ttk.Label(rot_frame, text="회전 각도").pack(anchor="w")
        rotate_options = ["회전 없음", "우측으로 90°", "180° 회전", "좌측으로 90°"]
        self.rot_combo = ttk.Combobox(rot_frame, textvariable=self.rotate_angle_label, values=rotate_options, state="readonly", width=10)
        self.rot_combo.pack(fill="x", pady=(4, 0))
        self.rot_combo.bind("<<ComboboxSelected>>", self._on_rotate_change)

        # Flip Checkboxes
        flip_frame = ttk.Frame(edit_group)
        flip_frame.grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(4, 0))
        ttk.Label(flip_frame, text="반전").pack(anchor="w")
        flip_check_frame = ttk.Frame(flip_frame)
        flip_check_frame.pack(anchor="w", pady=(4, 0))
        ttk.Checkbutton(flip_check_frame, text="좌우", variable=self.flip_horizontal).pack(side="left")
        ttk.Checkbutton(flip_check_frame, text="상하", variable=self.flip_vertical).pack(side="left", padx=(8, 0))

        # Convert Button
        self.convert_btn = ttk.Button(options_container, text="변환 시작", command=self.convert, style="Primary.TButton")
        self.convert_btn.pack(fill="x", pady=(10, 0), ipady=6)

        # Footer
        footer = ttk.Frame(self.root, padding=(16, 6, 16, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(footer, textvariable=self.status, font=("Malgun Gothic", 10, "bold")).grid(row=0, column=1, sticky="e")

    def _toggle_resize(self, *args) -> None:
        mode = self.resize_mode.get()
        self.pct_frame.pack_forget()
        self.dim_frame.pack_forget()
        
        if mode == "비율 축소 (%)":
            self.pct_frame.pack(fill="x", pady=(4, 0))
        elif mode == "너비 고정 (px)":
            self.dim_frame.pack(fill="x", pady=(4, 0))
            self.width_lbl.configure(text="고정 너비 (px)")
            self.width_lbl.grid(row=0, column=0, sticky="w", columnspan=2)
            self.width_entry.grid(row=1, column=0, columnspan=2, sticky="ew")
            self.height_lbl.grid_forget()
            self.height_entry.grid_forget()
        elif mode == "높이 고정 (px)":
            self.dim_frame.pack(fill="x", pady=(4, 0))
            self.height_lbl.configure(text="고정 높이 (px)")
            self.height_lbl.grid(row=0, column=0, sticky="w", columnspan=2)
            self.height_entry.grid(row=1, column=0, columnspan=2, sticky="ew")
            self.width_lbl.grid_forget()
            self.width_entry.grid_forget()
        elif mode == "가로/세로 최대 제한":
            self.dim_frame.pack(fill="x", pady=(4, 0))
            
            self.width_lbl.configure(text="가로 제한 (px)")
            self.width_lbl.grid(row=0, column=0, sticky="w")
            self.width_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6))
            
            self.height_lbl.configure(text="세로 제한 (px)")
            self.height_lbl.grid(row=0, column=1, sticky="w")
            self.height_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0))

    def _on_rotate_change(self, *args) -> None:
        lbl = self.rotate_angle_label.get()
        if lbl == "회전 없음":
            self.rotate_angle.set("0")
        elif lbl == "우측으로 90°":
            self.rotate_angle.set("90")
        elif lbl == "180° 회전":
            self.rotate_angle.set("180")
        elif lbl == "좌측으로 90°":
            self.rotate_angle.set("270")

    def _update_notice(self) -> None:
        fmt = self.output_format.get()
        if OUTPUT_FORMATS[fmt]["lossy"]:
            text = f"{fmt}는 손실 압축 형식입니다. 품질 설정에 따라 파일 화질과 용량이 변경됩니다."
            self.qual_scale.configure(state="normal")
        else:
            text = f"{fmt} 저장은 무손실입니다. 원본 화질을 보존하며 품질 설정은 무시됩니다."
            self.qual_scale.configure(state="disabled")
            
        if fmt in {"ICO", "GIF"}:
            text += " 색상 수나 규격 제약이 있어 원본과 표현 방식이 달라질 수 있습니다."
        self.notice_label.configure(text=text)

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="사진 선택", filetypes=INPUT_TYPES)
        for name in selected:
            path = Path(name)
            if not any(entry["path"] == path for entry in self.entries):
                size = path.stat().st_size if path.exists() else 0
                self.entries.append({
                    "path": path,
                    "orig_size": size,
                    "new_name": None,
                    "new_size": None,
                    "ratio": None,
                    "status": "대기"
                })
        self.refresh_file_list()

    def clear_files(self) -> None:
        self.entries.clear()
        self.refresh_file_list()

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="출력 폴더 선택", initialdir=self.output_dir.get())
        if selected:
            self.output_dir.set(selected)

    def refresh_file_list(self) -> None:
        self.file_list.delete(*self.file_list.get_children())
        for idx, entry in enumerate(self.entries):
            path = entry["path"]
            orig_size_str = self._format_bytes(entry["orig_size"])
            new_name_str = entry["new_name"] if entry["new_name"] else "-"
            new_size_str = self._format_bytes(entry["new_size"]) if entry["new_size"] is not None else "-"
            ratio_str = entry["ratio"] if entry["ratio"] else "-"
            status_str = entry["status"]

            self.file_list.insert(
                "", 
                "end", 
                iid=str(idx), 
                values=(
                    path.name, 
                    path.suffix.lower() or "unknown", 
                    orig_size_str, 
                    new_name_str,
                    new_size_str, 
                    ratio_str, 
                    status_str
                )
            )
        self.status.set(f"{len(self.entries)}개 파일 선택됨" if self.entries else "파일을 추가하세요.")

    def convert(self) -> None:
        if not self.entries:
            messagebox.showwarning("파일 없음", "변환할 사진을 먼저 추가하세요.")
            return

        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        self.progress.configure(maximum=len(self.entries), value=0)
        failures: list[str] = []

        for index, entry in enumerate(self.entries):
            source = entry["path"]
            entry["status"] = "변환 중"
            self.refresh_file_list()
            self.status.set(f"변환 중: {source.name}")
            self.root.update_idletasks()

            try:
                target = self._convert_one(source, output_path)
                new_size = target.stat().st_size
                entry["new_size"] = new_size
                entry["new_name"] = target.name
                entry["status"] = "완료"
                
                # Calculate compression ratio
                orig_size = entry["orig_size"]
                if orig_size > 0:
                    pct_diff = ((new_size - orig_size) / orig_size) * 100
                    if pct_diff < 0:
                        entry["ratio"] = f"{pct_diff:.1f}%"
                    elif pct_diff > 0:
                        entry["ratio"] = f"+{pct_diff:.1f}%"
                    else:
                        entry["ratio"] = "0.0%"
                else:
                    entry["ratio"] = "0.0%"
            except Exception as exc:
                failures.append(f"{source.name}: {exc}")
                entry["status"] = "실패"
                entry["ratio"] = "-"

            self.progress.configure(value=index + 1)
            self.refresh_file_list()
            self.root.update_idletasks()

        if failures:
            messagebox.showwarning("일부 실패", "\n".join(failures[:8]))
            self.status.set(f"완료, 실패 {len(failures)}개")
        else:
            messagebox.showinfo("완료", f"{len(self.entries)}개 파일을 변환했습니다.")
            self.status.set("변환 완료")

        if os.name == "nt":
            os.startfile(output_path)

    def _convert_one(self, source: Path, output_dir: Path) -> Path:
        fmt_name = self.output_format.get()
        fmt = OUTPUT_FORMATS[fmt_name]
        
        # Apply Custom Naming Pattern (Prefix & Suffix)
        prefix = self.filename_prefix.get()
        suffix = self.filename_suffix.get()
        target_name = f"{prefix}{source.stem}{suffix}{fmt['ext']}"
        target = self._unique_target(output_dir / target_name)

        with self._open_image(source) as image:
            exif = image.info.get("exif") if self.keep_exif.get() else None
            image = ImageOps.exif_transpose(image)

            # 1. Grayscale Filter
            if self.grayscale.get():
                image = ImageOps.grayscale(image)

            # 2. Rotation & Flip
            angle = int(self.rotate_angle.get())
            if angle != 0:
                # Rotate clockwise (Pillow's rotate is CCW, so rotate by -angle)
                image = image.rotate(-angle, expand=True)

            if self.flip_horizontal.get():
                image = ImageOps.mirror(image)
            if self.flip_vertical.get():
                image = ImageOps.flip(image)

            # 3. Resize Modes
            mode = self.resize_mode.get()
            width, height = image.size
            if mode == "비율 축소 (%)":
                pct = self.resize_pct.get()
                if pct != 100:
                    new_w = max(1, int(width * pct / 100))
                    new_h = max(1, int(height * pct / 100))
                    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            elif mode == "너비 고정 (px)":
                target_w = self.max_width.get()
                if target_w != width:
                    scale = target_w / width
                    new_h = max(1, int(height * scale))
                    image = image.resize((target_w, new_h), Image.Resampling.LANCZOS)
            elif mode == "높이 고정 (px)":
                target_h = self.max_height.get()
                if target_h != height:
                    scale = target_h / height
                    new_w = max(1, int(width * scale))
                    image = image.resize((new_w, target_h), Image.Resampling.LANCZOS)
            elif mode == "가로/세로 최대 제한":
                image.thumbnail((self.max_width.get(), self.max_height.get()), Image.Resampling.LANCZOS)

            # 4. Save Settings
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
            return target

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
        root.call("tk", "scaling", 1.25)
    except Exception:
        pass
    PhotoConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
