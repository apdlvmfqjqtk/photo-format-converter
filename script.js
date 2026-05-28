const fileInput = document.querySelector("#fileInput");
const dropzone = document.querySelector("#dropzone");
const formatSelect = document.querySelector("#formatSelect");
const formatNotice = document.querySelector("#formatNotice");
const qualityControl = document.querySelector("#qualityControl");
const qualityRange = document.querySelector("#qualityRange");
const qualityValue = document.querySelector("#qualityValue");
const convertButton = document.querySelector("#convertButton");
const clearButton = document.querySelector("#clearButton");
const fileList = document.querySelector("#fileList");
const statusText = document.querySelector("#statusText");
const cardTemplate = document.querySelector("#fileCardTemplate");

// New UI Controls
const resizeModeSelect = document.querySelector("#resizeModeSelect");
const resizePercentageControl = document.querySelector("#resizePercentageControl");
const resizePercentageInput = document.querySelector("#resizePercentage");
const resizePercentageValue = document.querySelector("#resizePercentageValue");
const resizeDimensionsControl = document.querySelector("#resizeDimensionsControl");
const widthLabel = document.querySelector("#widthLabel");
const heightLabel = document.querySelector("#heightLabel");
const maxWidthInput = document.querySelector("#maxWidth");
const maxHeightInput = document.querySelector("#maxHeight");
const rotateSelect = document.querySelector("#rotateSelect");
const flipHToggle = document.querySelector("#flipHToggle");
const flipVToggle = document.querySelector("#flipVToggle");
const grayscaleToggle = document.querySelector("#grayscaleToggle");
const filenamePrefix = document.querySelector("#filenamePrefix");
const filenameSuffix = document.querySelector("#filenameSuffix");
const downloadAllZipButton = document.querySelector("#downloadAllZipButton");

// Advanced Slider Controls
const brightnessRange = document.querySelector("#brightnessRange");
const brightnessValue = document.querySelector("#brightnessValue");
const contrastRange = document.querySelector("#contrastRange");
const contrastValue = document.querySelector("#contrastValue");
const saturationRange = document.querySelector("#saturationRange");
const saturationValue = document.querySelector("#saturationValue");
const blurRange = document.querySelector("#blurRange");
const blurValue = document.querySelector("#blurValue");
const autoDownloadToggle = document.querySelector("#autoDownloadToggle");

// Modal Elements
const previewModal = document.querySelector("#previewModal");
const modalImage = document.querySelector("#modalImage");
const modalFileName = document.querySelector("#modalFileName");
const modalFileStats = document.querySelector("#modalFileStats");
const modalDownloadLink = document.querySelector("#modalDownloadLink");
const modalCloseButton = document.querySelector("#modalCloseButton");
const modalOverlay = document.querySelector("#modalOverlay");

const outputFormats = [
  {
    type: "image/png",
    label: "PNG",
    extension: "png",
    quality: false,
    notice: "PNG는 무손실 저장입니다. 투명 배경이 유지되며 품질 조절이 비활성화됩니다.",
  },
  {
    type: "image/jpeg",
    label: "JPEG",
    extension: "jpg",
    quality: true,
    notice: "JPEG는 손실 압축입니다. 투명 배경은 흰색으로 채워지며 용량 관리에 유리합니다.",
  },
  {
    type: "image/webp",
    label: "WebP",
    extension: "webp",
    quality: true,
    notice: "WebP는 뛰어난 압축 효율을 보여줍니다. 투명 배경을 지원하며 현대 웹 환경에 권장됩니다.",
  },
  {
    type: "image/avif",
    label: "AVIF",
    extension: "avif",
    quality: true,
    notice: "AVIF는 최고 수준의 차세대 압축률을 자랑하지만 브라우저 인코딩 속도가 다소 느릴 수 있습니다.",
  },
];

let entries = [];
let supportedFormats = [];
let jszipLoaded = false;
let heic2anyLoaded = false;

function canvasSupports(type) {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  return canvas.toDataURL(type).startsWith(`data:${type}`);
}

function initializeFormats() {
  supportedFormats = outputFormats.filter((format) => canvasSupports(format.type));
  formatSelect.textContent = "";

  for (const format of supportedFormats) {
    const option = document.createElement("option");
    option.value = format.type;
    option.textContent = format.label;
    formatSelect.append(option);
  }

  updateFormatControls();
}

function currentFormat() {
  return supportedFormats.find((format) => format.type === formatSelect.value) || supportedFormats[0];
}

function formatBytes(bytes) {
  if (bytes === undefined || bytes === null) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function baseName(name) {
  return name.replace(/\.[^.]+$/, "") || "converted-image";
}

function updateFormatControls() {
  const format = currentFormat();
  qualityControl.style.display = format.quality ? "block" : "none";
  formatNotice.textContent = format.notice;
}

function updateStatus() {
  const total = entries.length;
  const done = entries.filter((entry) => entry.status === "완료").length;
  statusText.textContent = total
    ? `${total}개 파일 선택됨, ${done}개 변환 완료`
    : "아직 선택된 사진이 없습니다.";
  convertButton.disabled = total === 0;

  if (done > 0) {
    downloadAllZipButton.style.display = "inline-flex";
  } else {
    downloadAllZipButton.style.display = "none";
  }
}

function revokeEntry(entry) {
  if (entry.previewUrl) URL.revokeObjectURL(entry.previewUrl);
  if (entry.downloadUrl) URL.revokeObjectURL(entry.downloadUrl);
}

function renderEntries() {
  fileList.textContent = "";

  for (const entry of entries) {
    const card = cardTemplate.content.firstElementChild.cloneNode(true);
    const previewContainer = card.querySelector(".preview-container");
    const preview = card.querySelector(".preview");
    const title = card.querySelector("h3");
    const origMeta = card.querySelector(".orig-meta");
    const newMeta = card.querySelector(".new-meta");
    const badge = card.querySelector(".badge");
    const link = card.querySelector(".download-link");

    preview.src = entry.previewUrl;
    preview.alt = `${entry.file.name} 미리보기`;
    title.textContent = entry.file.name;
    
    const ext = entry.file.name.split(".").pop().toUpperCase();
    origMeta.textContent = `${ext} · ${formatBytes(entry.file.size)}`;
    
    if (entry.status === "완료" && entry.newSizeStr && entry.ratioStr) {
      newMeta.textContent = `➡ ${entry.newSizeStr} (${entry.ratioStr})`;
      newMeta.style.display = "block";
    } else {
      newMeta.style.display = "none";
    }

    badge.textContent = entry.status;
    badge.className = `badge ${entry.statusClass || ""}`.trim();

    if (entry.downloadUrl) {
      link.href = entry.downloadUrl;
      link.download = entry.outputName;
      link.hidden = false;
    }

    // Attach preview event to thumbnail click
    previewContainer.addEventListener("click", () => openModal(entry));

    fileList.append(card);
  }

  updateStatus();
}

function addFiles(files) {
  const imageFiles = [...files].filter((file) => file.type.startsWith("image/") || /\.(heic|heif|tif|tiff)$/i.test(file.name));

  for (const file of imageFiles) {
    // Avoid duplicate additions based on name & size
    if (entries.some((entry) => entry.file.name === file.name && entry.file.size === file.size)) continue;
    
    // For HEIC, create a placeholder image url or let it show default
    let previewUrl = "";
    if (/\.(heic|heif)$/i.test(file.name)) {
      previewUrl = "data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D'http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg' width%3D'100' height%3D'100' viewBox%3D'0 0 100 100'%3E%3Crect width%3D'100' height%3D'100' fill%3D'%231e293b'%2F%3E%3Ctext x%3D'50%25' y%3D'55%25' dominant-baseline%3D'middle' text-anchor%3D'middle' fill%3D'%2394a3b8' font-size%3D'12' font-family%3D'sans-serif'%3EHEIC%3C%2Ftext%3E%3C%2Fsvg%3E";
    } else {
      previewUrl = URL.createObjectURL(file);
    }

    entries.push({
      file,
      previewUrl,
      downloadUrl: "",
      blob: null,
      outputName: "",
      status: "대기",
      statusClass: "",
      newSizeStr: "",
      ratioStr: "",
    });
  }

  renderEntries();
}

function imageFromBlob(blob) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(blob);

    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("이 브라우저에서 읽을 수 없는 이미지 형식입니다."));
    };
    image.src = url;
  });
}

function getTargetSize(width, height) {
  const mode = resizeModeSelect.value;
  if (mode === "none") {
    return { width, height };
  }
  if (mode === "percentage") {
    const pct = Math.max(5, Math.min(99, Number(resizePercentageInput.value) || 80)) / 100;
    return {
      width: Math.max(1, Math.round(width * pct)),
      height: Math.max(1, Math.round(height * pct)),
    };
  }
  if (mode === "width") {
    const targetW = Math.max(1, Number(maxWidthInput.value) || width);
    const scale = targetW / width;
    return {
      width: targetW,
      height: Math.max(1, Math.round(height * scale)),
    };
  }
  if (mode === "height") {
    const targetH = Math.max(1, Number(maxHeightInput.value) || height);
    const scale = targetH / height;
    return {
      width: Math.max(1, Math.round(width * scale)),
      height: targetH,
    };
  }
  if (mode === "fit") {
    const maxW = Math.max(1, Number(maxWidthInput.value) || width);
    const maxH = Math.max(1, Number(maxHeightInput.value) || height);
    const scale = Math.min(1, maxW / width, maxH / height);
    return {
      width: Math.max(1, Math.round(width * scale)),
      height: Math.max(1, Math.round(height * scale)),
    };
  }
  return { width, height };
}

function loadHeic2Any() {
  return new Promise((resolve, reject) => {
    if (window.heic2any) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/heic2any/0.0.4/heic2any.min.js";
    script.onload = () => {
      heic2anyLoaded = true;
      resolve();
    };
    script.onerror = () => {
      reject(new Error("HEIC 디코더 라이브러리를 로드할 수 없습니다. 오프라인이거나 CDN 오류일 수 있습니다."));
    };
    document.head.appendChild(script);
  });
}

async function convertEntry(entry) {
  const format = currentFormat();
  entry.status = "변환 중";
  entry.statusClass = "working";
  renderEntries();

  try {
    let sourceBlob = entry.file;

    // HEIC decoding logic client-side
    const isHeic = /\.(heic|heif)$/i.test(entry.file.name);
    if (isHeic) {
      entry.status = "HEIC 디코딩";
      renderEntries();
      await loadHeic2Any();
      
      const converted = await heic2any({
        blob: entry.file,
        toType: "image/png"
      });
      sourceBlob = Array.isArray(converted) ? converted[0] : converted;

      // Update preview to converted one
      if (entry.previewUrl.startsWith("data:")) {
        entry.previewUrl = URL.createObjectURL(sourceBlob);
      }
    }

    entry.status = "렌더링 중";
    renderEntries();

    const image = await imageFromBlob(sourceBlob);
    const size = getTargetSize(image.naturalWidth, image.naturalHeight);
    
    // Rotate checks
    const rotation = Number(rotateSelect.value);
    const isSwapped = rotation === 90 || rotation === 270;
    
    // Canvas sizing based on rotation
    const canvasW = isSwapped ? size.height : size.width;
    const canvasH = isSwapped ? size.width : size.height;

    const canvas = document.createElement("canvas");
    canvas.width = canvasW;
    canvas.height = canvasH;
    
    const context = canvas.getContext("2d", { alpha: format.type !== "image/jpeg" });

    // Handle white background for transparent to JPG
    if (format.type === "image/jpeg") {
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Advanced Synthesis Filters
    const filters = [];
    if (grayscaleToggle.checked) {
      filters.push("grayscale(100%)");
    }
    if (brightnessRange.value !== "100") {
      filters.push(`brightness(${brightnessRange.value}%)`);
    }
    if (contrastRange.value !== "100") {
      filters.push(`contrast(${contrastRange.value}%)`);
    }
    if (saturationRange.value !== "100") {
      filters.push(`saturate(${saturationRange.value}%)`);
    }
    if (blurRange.value !== "0") {
      filters.push(`blur(${blurRange.value}px)`);
    }
    
    if (filters.length > 0) {
      context.filter = filters.join(" ");
    } else {
      context.filter = "none";
    }

    // Centered Transforms
    context.save();
    context.translate(canvasW / 2, canvasH / 2);
    
    if (rotation !== 0) {
      context.rotate((rotation * Math.PI) / 180);
    }

    const scaleX = flipHToggle.checked ? -1 : 1;
    const scaleY = flipVToggle.checked ? -1 : 1;
    context.scale(scaleX, scaleY);

    context.drawImage(image, -size.width / 2, -size.height / 2, size.width, size.height);
    context.restore();

    // Export Blob
    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (result) => (result ? resolve(result) : reject(new Error("포맷 내보내기를 지원하지 않습니다."))),
        format.type,
        format.quality ? Number(qualityRange.value) / 100 : undefined,
      );
    });

    if (entry.downloadUrl) URL.revokeObjectURL(entry.downloadUrl);
    entry.blob = blob;
    entry.downloadUrl = URL.createObjectURL(blob);
    
    // Customize target naming pattern
    const prefix = filenamePrefix.value || "";
    const suffix = filenameSuffix.value || "";
    entry.outputName = `${prefix}${baseName(entry.file.name)}${suffix}.${format.extension}`;
    
    entry.status = "완료";
    entry.statusClass = "done";
    
    // Update sizing details
    entry.newSizeStr = formatBytes(blob.size);
    const pctDiff = ((blob.size - entry.file.size) / entry.file.size) * 100;
    entry.ratioStr = pctDiff < 0 ? `${pctDiff.toFixed(1)}%` : `+${pctDiff.toFixed(1)}%`;

    // Auto download if toggle is checked
    if (autoDownloadToggle.checked && entry.downloadUrl) {
      const a = document.createElement("a");
      a.href = entry.downloadUrl;
      a.download = entry.outputName;
      a.click();
    }
    
  } catch (error) {
    entry.status = error.message;
    entry.statusClass = "error";
    entry.blob = null;
    entry.downloadUrl = "";
    entry.newSizeStr = "";
    entry.ratioStr = "";
  }

  renderEntries();
}

function openModal(entry) {
  const displayUrl = entry.downloadUrl || entry.previewUrl;
  if (!displayUrl) return;

  modalImage.src = displayUrl;
  modalFileName.textContent = entry.outputName || entry.file.name;
  
  if (entry.status === "완료" && entry.newSizeStr && entry.ratioStr) {
    modalFileStats.textContent = `${formatBytes(entry.file.size)} ➡ ${entry.newSizeStr} (${entry.ratioStr})`;
  } else {
    modalFileStats.textContent = `${formatBytes(entry.file.size)} (변환 대기 중)`;
  }

  if (entry.downloadUrl) {
    modalDownloadLink.href = entry.downloadUrl;
    modalDownloadLink.download = entry.outputName;
    modalDownloadLink.style.display = "inline-flex";
  } else {
    modalDownloadLink.style.display = "none";
  }

  previewModal.style.display = "flex";
}

function closeModal() {
  previewModal.style.display = "none";
  modalImage.src = "";
}

function loadJSZip() {
  return new Promise((resolve, reject) => {
    if (window.JSZip) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js";
    script.onload = () => {
      jszipLoaded = true;
      resolve();
    };
    script.onerror = () => {
      reject(new Error("JSZip 라이브러리를 CDN에서 로딩할 수 없습니다. 오프라인 상태이거나 차단되었을 수 있습니다."));
    };
    document.head.appendChild(script);
  });
}

async function downloadAllZip() {
  const completed = entries.filter((e) => e.blob && e.status === "완료");
  if (completed.length === 0) return;

  downloadAllZipButton.disabled = true;
  const originalText = downloadAllZipButton.innerHTML;
  downloadAllZipButton.textContent = "ZIP 생성 중...";

  try {
    await loadJSZip();
    const zip = new JSZip();
    const nameTracker = {};

    for (const entry of completed) {
      let uniqueName = entry.outputName;
      if (nameTracker[uniqueName]) {
        const parts = uniqueName.split(".");
        const ext = parts.pop();
        const base = parts.join(".");
        nameTracker[uniqueName]++;
        uniqueName = `${base}_${nameTracker[uniqueName]}.${ext}`;
      } else {
        nameTracker[uniqueName] = 1;
      }
      zip.file(uniqueName, entry.blob);
    }

    const content = await zip.generateAsync({ type: "blob" });
    const zipUrl = URL.createObjectURL(content);

    const a = document.createElement("a");
    a.href = zipUrl;
    a.download = `converted_images_${Date.now()}.zip`;
    a.click();

    setTimeout(() => URL.revokeObjectURL(zipUrl), 60000);
  } catch (error) {
    alert(error.message + "\n\n개별 이미지 다운로드를 이용해 주세요.");
  } finally {
    downloadAllZipButton.disabled = false;
    downloadAllZipButton.innerHTML = originalText;
  }
}

// Clipboard Paste support
window.addEventListener("paste", (event) => {
  const items = (event.clipboardData || event.originalEvent.clipboardData).items;
  const files = [];
  for (const item of items) {
    if (item.kind === "file") {
      const file = item.getAsFile();
      if (file) files.push(file);
    }
  }
  if (files.length > 0) {
    addFiles(files);
  }
});

// Events
fileInput.addEventListener("change", (event) => {
  addFiles(event.target.files);
  fileInput.value = "";
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("is-dragging");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("is-dragging");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("is-dragging");
  addFiles(event.dataTransfer.files);
});

formatSelect.addEventListener("change", updateFormatControls);

qualityRange.addEventListener("input", () => {
  qualityValue.value = `${qualityRange.value}%`;
});

// Advanced Sliders update outputs
brightnessRange.addEventListener("input", () => {
  brightnessValue.value = `${brightnessRange.value}%`;
});

contrastRange.addEventListener("input", () => {
  contrastValue.value = `${contrastRange.value}%`;
});

saturationRange.addEventListener("input", () => {
  saturationValue.value = `${saturationRange.value}%`;
});

blurRange.addEventListener("input", () => {
  blurValue.value = `${blurRange.value}px`;
});

// Resize mode UI toggles
resizeModeSelect.addEventListener("change", () => {
  const val = resizeModeSelect.value;
  
  if (val === "none") {
    resizePercentageControl.style.display = "none";
    resizeDimensionsControl.style.display = "none";
  } else if (val === "percentage") {
    resizePercentageControl.style.display = "block";
    resizeDimensionsControl.style.display = "none";
  } else {
    // Fixed width, Fixed height, or Fit
    resizePercentageControl.style.display = "none";
    resizeDimensionsControl.style.display = "grid";

    if (val === "width") {
      widthLabel.textContent = "고정 너비 (px)";
      maxWidthInput.style.display = "block";
      widthLabel.style.display = "block";
      maxHeightInput.style.display = "none";
      heightLabel.style.display = "none";
    } else if (val === "height") {
      heightLabel.textContent = "고정 높이 (px)";
      maxWidthInput.style.display = "none";
      widthLabel.style.display = "none";
      maxHeightInput.style.display = "block";
      heightLabel.style.display = "block";
    } else if (val === "fit") {
      widthLabel.textContent = "가로 제한 (px)";
      heightLabel.textContent = "세로 제한 (px)";
      maxWidthInput.style.display = "block";
      widthLabel.style.display = "block";
      maxHeightInput.style.display = "block";
      heightLabel.style.display = "block";
    }
  }
});

resizePercentageInput.addEventListener("input", () => {
  resizePercentageValue.value = `${resizePercentageInput.value}%`;
});

clearButton.addEventListener("click", () => {
  entries.forEach(revokeEntry);
  entries = [];
  renderEntries();
});

convertButton.addEventListener("click", async () => {
  convertButton.disabled = true;
  for (const entry of entries) {
    if (entry.status !== "변환 중" && entry.status !== "완료" && entry.status !== "HEIC 디코딩" && entry.status !== "렌더링 중") {
      await convertEntry(entry);
    }
  }
  updateStatus();
});

downloadAllZipButton.addEventListener("click", downloadAllZip);

modalCloseButton.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", closeModal);
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

// Init
initializeFormats();
renderEntries();
