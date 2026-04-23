chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message?.type) {
    return false;
  }

  if (message.type === "DOWNLOAD_SELECTED") {
    void handleDownloadSelected(message.payload)
      .then((result) => sendResponse({ ok: true, ...result }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));

    return true;
  }

  if (message.type === "SHOW_DOWNLOADS_FOLDER") {
    try {
      chrome.downloads.showDefaultFolder();
      sendResponse({ ok: true });
    } catch (error) {
      sendResponse({ ok: false, error: error.message || "Không thể mở thư mục Downloads." });
    }

    return false;
  }

  return false;
});

chrome.sidePanel?.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

chrome.runtime.onStartup.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

async function handleDownloadSelected(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  const options = payload?.options || {};
  const downloadSubfolder = sanitizeRelativeFolder(options.downloadSubfolder);
  const preferredExtension = normalizePreferredExtension(options.preferredExtension);
  const saveAs = Boolean(options.saveAs);

  if (items.length === 0) {
    throw new Error("Không có ảnh nào được truyền sang service worker để tải.");
  }

  const downloadIds = [];
  const errors = [];
  const folderStamp = createFolderStamp();

  for (let index = 0; index < items.length; index += 1) {
    const item = items[index];

    try {
      const extension = normalizeExtension(item.preferredExtension || preferredExtension || inferExtension(item.imageUrl));
      const filename = buildFilename(item, folderStamp, extension, index, downloadSubfolder);
      const downloadId = await chrome.downloads.download({
        url: item.imageUrl,
        filename,
        conflictAction: "uniquify",
        saveAs
      });

      downloadIds.push(downloadId);
    } catch (error) {
      errors.push({
        itemId: item.id,
        imageUrl: item.imageUrl,
        message: error.message || "Download thất bại."
      });
    }
  }

  return {
    downloadIds,
    errors
  };
}

function buildFilename(item, folderStamp, extension, fallbackIndex, downloadSubfolder) {
  const promptSegment = sanitizeFilenameSegment(item.prompt || `prompt-${fallbackIndex + 1}`).slice(0, 60);
  const batchSegment = String(item.batchIndex || fallbackIndex + 1).padStart(3, "0");
  const imageSegment = String(item.imageIndex || 1).padStart(2, "0");
  const baseFolder = downloadSubfolder ? `${downloadSubfolder}/${folderStamp}` : `flow-batch/${folderStamp}`;

  return `${baseFolder}/prompt-${batchSegment}-image-${imageSegment}-${promptSegment}${extension}`;
}

function createFolderStamp() {
  const now = new Date();
  const parts = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0")
  ];
  const time = [
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0")
  ].join("");

  return `${parts.join("")}-${time}`;
}

function sanitizeFilenameSegment(value) {
  return String(value || "image")
    .normalize("NFKD")
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^\.+/, "")
    .replace(/^-+|-+$/g, "")
    .toLowerCase() || "image";
}

function inferExtension(url) {
  try {
    const parsedUrl = new URL(url);
    const match = parsedUrl.pathname.match(/\.(png|jpg|jpeg|jfif|webp|gif|bmp)$/i);

    if (match) {
      return normalizeExtension(match[1]);
    }
  } catch (error) {
    console.warn("Không parse được URL ảnh, fallback sang .png", error);
  }

  return ".jpg";
}

function normalizePreferredExtension(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/^\./, "");
  if (["jpg", "jpeg", "jfif", "png", "webp"].includes(normalized)) {
    return normalized;
  }

  return "";
}

function normalizeExtension(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/^\./, "");
  if (normalized === "jpeg" || normalized === "jfif" || normalized === "jpg") {
    return ".jpg";
  }

  if (normalized === "png" || normalized === "webp" || normalized === "gif" || normalized === "bmp") {
    return `.${normalized}`;
  }

  return ".jpg";
}

function sanitizeRelativeFolder(value) {
  return String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .replace(/\.\.+/g, "")
    .replace(/^\/+|\/+$/g, "")
    .replace(/\/{2,}/g, "/")
    .replace(/[<>:"|?*\x00-\x1F]/g, "");
}
