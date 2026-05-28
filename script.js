const fileInput = document.querySelector("#fileInput");
const dropzone = document.querySelector("#dropzone");
const formatSelect = document.querySelector("#formatSelect");
const formatNotice = document.querySelector("#formatNotice");
const qualityControl = document.querySelector("#qualityControl");
const qualityRange = document.querySelector("#qualityRange");
const qualityValue = document.querySelector("#qualityValue");
const resizeToggle = document.querySelector("#resizeToggle");
const maxWidthInput = document.querySelector("#maxWidth");
const maxHeightInput = document.querySelector("#maxHeight");
const convertButton = document.querySelector("#convertButton");
const clearButton = document.querySelector("#clearButton");
const fileList = document.querySelector("#fileList");
const statusText = document.querySelector("#statusText");
const cardTemplate = document.querySelector("#fileCardTemplate");

const outputFormats = [
  {
    type: "image/png",
    label: "PNG",
    extension: "png",
    quality: false,
    notice: "PNG는 무손실 저장입니다. 단, 크기 변경을 켜면 리샘플링으로 픽셀은 바뀝니다.",
  },
  {
    type: "image/jpeg",
    label: "JPEG",
    extension: "jpg",
    quality: true,
    notice: "JPEG는 손실 압축입니다. 품질 100%도 원본과 완전히 같지는 않고 투명 배경은 흰색으로 합쳐집니다.",
  },
  {
    type: "image/webp",
    label: "WebP",
    extension: "webp",
    quality: true,
    notice: "WebP는 보통 손실 압축으로 저장됩니다. 품질을 높이면 열화는 줄지만 파일이 커집니다.",
  },
  {
    type: "image/avif",
    label: "AVIF",
    extension: "avif",
    quality: true,
    notice: "AVIF는 브라우저가 인코딩을 지원할 때만 표시됩니다. 압축 효율은 좋지만 변환이 느릴 수 있습니다.",
  },
];

let entries = [];
let supportedFormats = [];

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
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function baseName(name) {
  return name.replace(/\.[^.]+$/, "") || "converted-image";
}

function updateFormatControls() {
  const format = currentFormat();
  qualityControl.hidden = !format.quality;
  formatNotice.textContent = format.notice;
}

function updateStatus() {
  const total = entries.length;
  const done = entries.filter((entry) => entry.downloadUrl).length;
  statusText.textContent = total
    ? `${total}개 파일 선택됨, ${done}개 변환 완료`
    : "아직 선택된 사진이 없습니다.";
  convertButton.disabled = total === 0;
}

function revokeEntry(entry) {
  if (entry.previewUrl) URL.revokeObjectURL(entry.previewUrl);
  if (entry.downloadUrl) URL.revokeObjectURL(entry.downloadUrl);
}

function renderEntries() {
  fileList.textContent = "";

  for (const entry of entries) {
    const card = cardTemplate.content.firstElementChild.cloneNode(true);
    const preview = card.querySelector(".preview");
    const title = card.querySelector("h3");
    const meta = card.querySelector("p");
    const badge = card.querySelector(".badge");
    const link = card.querySelector(".download-link");

    preview.src = entry.previewUrl;
    preview.alt = `${entry.file.name} 미리보기`;
    title.textContent = entry.file.name;
    meta.textContent = `${entry.file.type || "알 수 없는 형식"} · ${formatBytes(entry.file.size)}`;
    badge.textContent = entry.status;
    badge.className = `badge ${entry.statusClass || ""}`.trim();

    if (entry.downloadUrl) {
      link.href = entry.downloadUrl;
      link.download = entry.outputName;
      link.hidden = false;
    }

    fileList.append(card);
  }

  updateStatus();
}

function addFiles(files) {
  const imageFiles = [...files].filter((file) => file.type.startsWith("image/") || /\.(heic|heif|tif|tiff)$/i.test(file.name));

  for (const file of imageFiles) {
    entries.push({
      file,
      previewUrl: URL.createObjectURL(file),
      downloadUrl: "",
      outputName: "",
      status: "대기",
      statusClass: "",
    });
  }

  renderEntries();
}

function imageFromFile(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);

    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("이 브라우저에서 읽을 수 없는 입력 형식입니다."));
    };
    image.src = url;
  });
}

function getTargetSize(width, height) {
  if (!resizeToggle.checked) return { width, height };

  const maxWidth = Math.max(1, Number(maxWidthInput.value) || width);
  const maxHeight = Math.max(1, Number(maxHeightInput.value) || height);
  const scale = Math.min(1, maxWidth / width, maxHeight / height);

  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}

async function convertEntry(entry) {
  const format = currentFormat();
  entry.status = "변환 중";
  entry.statusClass = "working";
  renderEntries();

  try {
    const image = await imageFromFile(entry.file);
    const size = getTargetSize(image.naturalWidth, image.naturalHeight);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d", { alpha: format.type !== "image/jpeg" });

    canvas.width = size.width;
    canvas.height = size.height;

    if (format.type === "image/jpeg") {
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, canvas.width, canvas.height);
    }

    context.drawImage(image, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (result) => (result ? resolve(result) : reject(new Error("이 브라우저가 선택한 출력 형식을 지원하지 않습니다."))),
        format.type,
        format.quality ? Number(qualityRange.value) / 100 : undefined,
      );
    });

    if (entry.downloadUrl) URL.revokeObjectURL(entry.downloadUrl);
    entry.downloadUrl = URL.createObjectURL(blob);
    entry.outputName = `${baseName(entry.file.name)}.${format.extension}`;
    entry.status = "완료";
    entry.statusClass = "done";
  } catch (error) {
    entry.status = error.message;
    entry.statusClass = "error";
  }

  renderEntries();
}

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

resizeToggle.addEventListener("change", () => {
  maxWidthInput.disabled = !resizeToggle.checked;
  maxHeightInput.disabled = !resizeToggle.checked;
});

clearButton.addEventListener("click", () => {
  entries.forEach(revokeEntry);
  entries = [];
  renderEntries();
});

convertButton.addEventListener("click", async () => {
  convertButton.disabled = true;
  for (const entry of entries) {
    await convertEntry(entry);
  }
  updateStatus();
});

initializeFormats();
renderEntries();
