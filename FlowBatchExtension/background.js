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

  if (message.type === "FLOW_DEBUGGER_TYPE") {
    void handleDebuggerType(sender, message.payload)
      .then((result) => sendResponse({ ok: true, ...result }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));

    return true;
  }

  if (message.type === "FLOW_DEBUGGER_CLICK_AT") {
    void handleDebuggerClick(sender, message.payload)
      .then((result) => sendResponse({ ok: true, ...result }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));

    return true;
  }

  if (message.type === "FLOW_DEBUGGER_HOVER_AT") {
    void handleDebuggerHover(sender, message.payload)
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

async function handleDebuggerHover(sender, payload) {
  const tabId = sender?.tab?.id;
  const x = Number(payload?.x);
  const y = Number(payload?.y);

  if (!tabId) {
    throw new Error("Không xác định được tab để gửi hover debugger.");
  }

  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    throw new Error("Tọa độ hover debugger không hợp lệ.");
  }

  const debuggee = { tabId };
  let attached = false;

  try {
    await attachDebugger(debuggee);
    attached = true;

    await sendDebuggerCommand(debuggee, "Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x,
      y,
      button: "none",
      buttons: 0,
      clickCount: 0
    });

    return { hovered: true };
  } finally {
    if (attached) {
      await detachDebugger(debuggee).catch(() => {});
    }
  }
}

async function handleDebuggerClick(sender, payload) {
  const tabId = sender?.tab?.id;
  const x = Number(payload?.x);
  const y = Number(payload?.y);

  if (!tabId) {
    throw new Error("Không xác định được tab để gửi click debugger.");
  }

  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    throw new Error("Tọa độ click debugger không hợp lệ.");
  }

  const debuggee = { tabId };
  let attached = false;

  try {
    await attachDebugger(debuggee);
    attached = true;

    await sendDebuggerCommand(debuggee, "Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x,
      y,
      button: "left",
      buttons: 1,
      clickCount: 0
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchMouseEvent", {
      type: "mousePressed",
      x,
      y,
      button: "left",
      buttons: 1,
      clickCount: 1
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchMouseEvent", {
      type: "mouseReleased",
      x,
      y,
      button: "left",
      buttons: 1,
      clickCount: 1
    });

    return { clicked: true };
  } finally {
    if (attached) {
      await detachDebugger(debuggee).catch(() => {});
    }
  }
}

async function handleDebuggerType(sender, payload) {
  const tabId = sender?.tab?.id;
  const text = String(payload?.text || "");

  if (!tabId) {
    throw new Error("Không xác định được tab để gửi lệnh gõ phím.");
  }

  const debuggee = { tabId };
  let attached = false;

  try {
    await attachDebugger(debuggee);
    attached = true;

    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "rawKeyDown",
      key: "Control",
      code: "ControlLeft",
      windowsVirtualKeyCode: 17
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "keyDown",
      key: "a",
      code: "KeyA",
      text: "a",
      unmodifiedText: "a",
      windowsVirtualKeyCode: 65,
      modifiers: 2
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "a",
      code: "KeyA",
      windowsVirtualKeyCode: 65,
      modifiers: 2
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "Control",
      code: "ControlLeft",
      windowsVirtualKeyCode: 17
    });

    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "keyDown",
      key: "Backspace",
      code: "Backspace",
      windowsVirtualKeyCode: 8
    });
    await sendDebuggerCommand(debuggee, "Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "Backspace",
      code: "Backspace",
      windowsVirtualKeyCode: 8
    });

    await sendDebuggerCommand(debuggee, "Input.insertText", { text });
    return { typed: true };
  } finally {
    if (attached) {
      await detachDebugger(debuggee).catch(() => {});
    }
  }
}

async function handleDownloadSelected(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  const options = payload?.options || {};
  const downloadSubfolder = sanitizeRelativeFolder(options.downloadSubfolder);
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
      const extension = inferExtension(item.imageUrl);
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
    const match = parsedUrl.pathname.match(/\.(png|jpg|jpeg|webp|gif|bmp)$/i);

    if (match) {
      const raw = match[1].toLowerCase();
      return raw === "jpeg" ? ".jpg" : `.${raw}`;
    }
  } catch (error) {
    console.warn("Không parse được URL ảnh, fallback sang .png", error);
  }

  return ".png";
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

function attachDebugger(debuggee) {
  return new Promise((resolve, reject) => {
    chrome.debugger.attach(debuggee, "1.3", () => {
      const lastError = chrome.runtime.lastError;
      if (lastError && !lastError.message.includes("Another debugger is already attached")) {
        reject(new Error(lastError.message));
        return;
      }

      resolve();
    });
  });
}

function detachDebugger(debuggee) {
  return new Promise((resolve, reject) => {
    chrome.debugger.detach(debuggee, () => {
      const lastError = chrome.runtime.lastError;
      if (lastError) {
        reject(new Error(lastError.message));
        return;
      }

      resolve();
    });
  });
}

function sendDebuggerCommand(debuggee, method, params) {
  return new Promise((resolve, reject) => {
    chrome.debugger.sendCommand(debuggee, method, params, (result) => {
      const lastError = chrome.runtime.lastError;
      if (lastError) {
        reject(new Error(lastError.message));
        return;
      }

      resolve(result);
    });
  });
}

async function ensureFlowContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: "FLOW_BATCH_PING" });
    return;
  } catch (error) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"]
    });
  }

  await chrome.tabs.sendMessage(tabId, { type: "FLOW_BATCH_PING" });
}


