const STORAGE_KEYS = {
  config: "flowBatchConfig",
  results: "flowBatchResults"
};

const DEFAULT_CONFIG = {
  rawPrompts: "",
  galleryFilter: "",
  selectedPromptIndex: -1,
  lastFilledPromptIndex: -1
};

let ui = {};
let cache = {
  config: { ...DEFAULT_CONFIG },
  results: []
};
let currentMessage = {
  text: "Mở đúng tab Flow, bấm “Nhận diện ảnh hiện có”, sau đó chọn ảnh cần tải.",
  tone: "default"
};

function debounce(fn, waitMs) {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => fn(...args), waitMs);
  };
}

const persistConfigDebounced = debounce(async () => {
  await storageSet({
    [STORAGE_KEYS.config]: cache.config
  });
}, 180);

document.addEventListener("DOMContentLoaded", async () => {
  ui = {
    promptsInput: document.getElementById("promptsInput"),
    galleryFilterInput: document.getElementById("galleryFilterInput"),
    promptPreviewCount: document.getElementById("promptPreviewCount"),
    promptPreviewContainer: document.getElementById("promptPreviewContainer"),
    fillSelectedPromptButton: document.getElementById("fillSelectedPromptButton"),
    fillNextPromptButton: document.getElementById("fillNextPromptButton"),
    runAllPromptsButton: document.getElementById("runAllPromptsButton"),
    stopPromptRunButton: document.getElementById("stopPromptRunButton"),
    resetAllButton: document.getElementById("resetAllButton"),
    scannedCountValue: document.getElementById("scannedCountValue"),
    selectedCountValue: document.getElementById("selectedCountValue"),
    messageBox: document.getElementById("messageBox"),
    scanSessionButton: document.getElementById("scanSessionButton"),
    downloadFromFlowButton: document.getElementById("downloadFromFlowButton"),
    clearGalleryButton: document.getElementById("clearGalleryButton"),
    galleryCount: document.getElementById("galleryCount"),
    galleryContainer: document.getElementById("galleryContainer")
  };

  ui.promptsInput.addEventListener("input", handlePromptsChanged);
  ui.galleryFilterInput.addEventListener("input", handleGalleryFilterChanged);
  ui.fillSelectedPromptButton.addEventListener("click", handleFillSelectedPrompt);
  ui.fillNextPromptButton.addEventListener("click", handleFillNextPrompt);
  ui.runAllPromptsButton.addEventListener("click", handleRunAllPrompts);
  ui.stopPromptRunButton.addEventListener("click", handleStopPromptRun);
  ui.resetAllButton.addEventListener("click", handleResetAll);
  ui.scanSessionButton.addEventListener("click", handleScanSessionImages);
  ui.downloadFromFlowButton.addEventListener("click", handleDownloadFromFlow);
  ui.clearGalleryButton.addEventListener("click", handleClearGallery);
  ui.galleryContainer.addEventListener("change", handleGalleryToggle);
  chrome.storage.onChanged.addListener(handleStorageChanged);

  await hydrateFromStorage();
  renderAll();
  void autoSyncSessionImages();
});

function handleStorageChanged(changes, areaName) {
  if (areaName !== "local") {
    return;
  }

  if (changes[STORAGE_KEYS.config]) {
    cache.config = normalizeConfig(changes[STORAGE_KEYS.config].newValue);
    applyConfigToForm(cache.config);
  }

  if (changes[STORAGE_KEYS.results]) {
    cache.results = Array.isArray(changes[STORAGE_KEYS.results].newValue)
      ? changes[STORAGE_KEYS.results].newValue
      : [];
  }

  renderAll();
}

async function hydrateFromStorage() {
  const stored = await storageGet([STORAGE_KEYS.config, STORAGE_KEYS.results]);
  cache.config = normalizeConfig(stored[STORAGE_KEYS.config]);
  cache.results = Array.isArray(stored[STORAGE_KEYS.results]) ? stored[STORAGE_KEYS.results] : [];
  applyConfigToForm(cache.config);
}

function normalizeConfig(config) {
  return {
    rawPrompts: String(config?.rawPrompts || ""),
    galleryFilter: String(config?.galleryFilter || ""),
    selectedPromptIndex: Number.isFinite(Number(config?.selectedPromptIndex)) ? Number(config.selectedPromptIndex) : -1,
    lastFilledPromptIndex: Number.isFinite(Number(config?.lastFilledPromptIndex)) ? Number(config.lastFilledPromptIndex) : -1
  };
}

function applyConfigToForm(config) {
  ui.promptsInput.value = config.rawPrompts || "";
  ui.galleryFilterInput.value = config.galleryFilter || "";
}

function handlePromptsChanged() {
  cache.config.rawPrompts = ui.promptsInput.value;
  cache.config.selectedPromptIndex = -1;
  cache.config.lastFilledPromptIndex = -1;
  persistConfigDebounced();
  renderPromptPreview();
  renderGallery();
}

function handleGalleryFilterChanged() {
  cache.config.galleryFilter = ui.galleryFilterInput.value;
  persistConfigDebounced();
  renderPromptPreview();
  renderGallery();
}

async function handleScanSessionImages() {
  try {
    const tab = await getActiveTab();
    assertTabIsScriptable(tab);
    await ensureContentScript(tab.id);

    const { items: importedItems, diagnostics } = await collectSessionImagesFromTab(tab.id);
    const mergedResults = dedupeResultsByUrl([...importedItems, ...cache.results]);
    const newCount = Math.max(0, mergedResults.length - cache.results.length);

    cache.results = mergedResults;
    await storageSet({ [STORAGE_KEYS.results]: mergedResults });
    renderAll();

    if (newCount > 0) {
      setMessage(`Đã nhận diện thêm ${newCount} ảnh từ session Flow hiện tại.`, "success");
      return;
    }

    const diagnosticsText = diagnostics
      ? `\nChẩn đoán: img=${diagnostics.imgCount}, videoPoster=${diagnostics.videoPosterCount}, canvas=${diagnostics.canvasCount}, background=${diagnostics.backgroundCandidateCount}, collected=${diagnostics.collectedCount}.${formatImageSampleDiagnostics(diagnostics.sampleImages)}`
      : "";
    setMessage(`Không thấy ảnh session mới nào để thêm vào gallery.${diagnosticsText}`, "default");
  } catch (error) {
    setMessage(error.message || "Không thể quét ảnh từ session Flow hiện tại.", "error");
  }
}

async function handleFillSelectedPrompt() {
  try {
    const entries = getPromptEntriesSafe();
    if (entries.length === 0) {
      throw new Error("Chưa có prompt hợp lệ để điền vào Flow.");
    }

    if (!hasSelectedPrompt(entries.length)) {
      throw new Error("Hãy chọn một prompt trong danh sách trước khi điền.");
    }

    const targetIndex = clampPromptIndex(cache.config.selectedPromptIndex, entries.length);
    const targetEntry = entries[targetIndex];
    await fillPromptToFlow(targetEntry, entries.length);
    cache.config.selectedPromptIndex = targetIndex;
    cache.config.lastFilledPromptIndex = targetIndex;
    await storageSet({ [STORAGE_KEYS.config]: cache.config });
    renderPromptPreview();
  } catch (error) {
    setMessage(error.message || "Không thể điền prompt đã chọn vào Flow.", "error");
  }
}

async function handleFillNextPrompt() {
  try {
    const entries = getPromptEntriesSafe();
    if (entries.length === 0) {
      throw new Error("Chưa có prompt hợp lệ để điền vào Flow.");
    }

    const nextIndex = resolveNextPromptIndex(entries.length);
    const targetEntry = entries[nextIndex];
    await fillPromptToFlow(targetEntry, entries.length);
    cache.config.selectedPromptIndex = nextIndex;
    cache.config.lastFilledPromptIndex = nextIndex;
    await storageSet({ [STORAGE_KEYS.config]: cache.config });
    renderPromptPreview();
  } catch (error) {
    setMessage(error.message || "Không thể điền prompt kế tiếp vào Flow.", "error");
  }
}

async function handleRunAllPrompts() {
  try {
    const entries = getPromptEntriesSafe();
    if (entries.length === 0) {
      throw new Error("Chưa có prompt hợp lệ để chạy tự động.");
    }

    const tab = await getActiveTab();
    assertTabIsScriptable(tab);
    await ensureContentScript(tab.id);

    const startIndex = hasSelectedPrompt(entries.length)
      ? clampPromptIndex(cache.config.selectedPromptIndex, entries.length)
      : 0;
    const prompts = entries.slice(startIndex).map((entry) => entry.prompt);
    if (prompts.length === 0) {
      throw new Error("Không còn prompt nào để chạy từ vị trí hiện tại.");
    }

      const response = await tabsSendMessage(tab.id, {
        type: "FLOW_AUTOFILL_PROMPTS",
        payload: {
          prompts,
          startIndex,
          delayMs: 10000,
          longPauseEvery: 5,
          longPauseMs: 20000
        }
      });

    if (!response?.ok) {
      throw new Error(response?.error || "Flow không nhận lệnh chạy tự động prompt.");
    }

      cache.config.lastFilledPromptIndex = startIndex - 1;
      await storageSet({ [STORAGE_KEYS.config]: cache.config });
      setMessage(`Đã bắt đầu chạy ${prompts.length} prompt. Mỗi prompt nghỉ 10 giây, cứ 5 prompt nghỉ 20 giây.`, "success");
    } catch (error) {
      setMessage(error.message || "Không thể chạy tự động toàn bộ prompt.", "error");
    }
  }

async function handleStopPromptRun() {
  try {
    const tab = await getActiveTab();
    assertTabIsScriptable(tab);
    await ensureContentScript(tab.id);

    const response = await tabsSendMessage(tab.id, {
      type: "FLOW_AUTOFILL_STOP"
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Flow không nhận lệnh dừng chạy prompt.");
    }

    setMessage("Đã gửi lệnh dừng chạy prompt.", "success");
  } catch (error) {
    setMessage(error.message || "Không thể dừng chạy prompt.", "error");
  }
}

async function handleResetAll() {
  cache.config = { ...DEFAULT_CONFIG };
  cache.results = [];
  applyConfigToForm(cache.config);
  await storageSet({
    [STORAGE_KEYS.config]: cache.config,
    [STORAGE_KEYS.results]: []
  });
  renderAll();
  setMessage("Đã reset toàn bộ prompt, bộ lọc, gallery và trạng thái chọn.", "success");
}

async function handleDownloadFromFlow() {
  try {
    const selectedItems = cache.results.filter((item) => item.selected);
    if (selectedItems.length === 0) {
      throw new Error("Hãy chọn ít nhất một ảnh trong gallery trước khi tải.");
    }

    const tab = await getActiveTab();
    assertTabIsScriptable(tab);
    await ensureContentScript(tab.id);

    const response = await tabsSendMessage(tab.id, {
      type: "FLOW_DOWNLOAD_SELECTED_FROM_FLOW",
      payload: { items: selectedItems }
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Flow không trả về kết quả tải ảnh.");
    }

    setMessage(
      `Đã kích hoạt tải ${response.downloadedCount || 0}/${selectedItems.length} ảnh trực tiếp từ Flow.`,
      "success"
    );
  } catch (error) {
    setMessage(error.message || "Không thể tải ảnh đã chọn từ Flow.", "error");
  }
}

async function handleClearGallery() {
  cache.results = [];
  await storageSet({ [STORAGE_KEYS.results]: [] });
  renderAll();
  setMessage("Đã xóa gallery hiện tại trong extension.", "success");
}

async function handleGalleryToggle(event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || target.type !== "checkbox") {
    return;
  }

  const itemId = target.dataset.itemId;
  if (!itemId) {
    return;
  }

  cache.results = cache.results.map((item) =>
    item.id === itemId ? { ...item, selected: target.checked } : item
  );

  await storageSet({ [STORAGE_KEYS.results]: cache.results });
  renderAll();
}

function renderAll() {
  renderPromptPreview();
  renderGallery();
  renderStatus();
  syncActionState();
}

function renderStatus() {
  const selectedCount = cache.results.filter((item) => item.selected).length;
  ui.scannedCountValue.textContent = String(cache.results.length);
  ui.selectedCountValue.textContent = String(selectedCount);
  ui.messageBox.textContent = currentMessage.text;
  ui.messageBox.className = "message-box";

  if (currentMessage.tone === "error") {
    ui.messageBox.classList.add("error");
  }

  if (currentMessage.tone === "success") {
    ui.messageBox.classList.add("success");
  }
}

function renderPromptPreview() {
  const rawValue = ui.promptsInput.value || "";
  const filterText = normalizeText(ui.galleryFilterInput.value || "");
  ui.promptPreviewContainer.replaceChildren();

  if (!rawValue.trim()) {
    ui.promptPreviewCount.textContent = "0 prompt";
    const empty = document.createElement("div");
    empty.className = "prompt-preview-empty";
    empty.textContent = "Dán prompt vào đây để rà soát. Bạn có thể lọc theo từ khóa bằng ô phía trên.";
    ui.promptPreviewContainer.appendChild(empty);
    return;
  }

  let entries;
  try {
    entries = parsePromptEntries(rawValue);
  } catch (error) {
    ui.promptPreviewCount.textContent = "Lỗi parse";
    const errorBox = document.createElement("div");
    errorBox.className = "prompt-preview-error";
    errorBox.textContent = error.message || "Không parse được danh sách prompt.";
    ui.promptPreviewContainer.appendChild(errorBox);
    return;
  }

  const visibleEntries = filterText
    ? entries.filter((entry) => normalizeText(`${entry.label} ${entry.prompt}`).includes(filterText))
    : entries;

  ui.promptPreviewCount.textContent = `${visibleEntries.length}/${entries.length} prompt`;

  if (visibleEntries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "prompt-preview-empty";
    empty.textContent = "Không có prompt nào khớp với bộ lọc hiện tại.";
    ui.promptPreviewContainer.appendChild(empty);
    return;
  }

  for (const entry of visibleEntries) {
    const item = document.createElement("div");
    item.className = "prompt-preview-item";
    if (entry.index === cache.config.selectedPromptIndex) {
      item.classList.add("selected");
    }
    item.dataset.promptIndex = String(entry.index);
    item.addEventListener("click", () => {
      cache.config.selectedPromptIndex = cache.config.selectedPromptIndex === entry.index ? -1 : entry.index;
      void storageSet({ [STORAGE_KEYS.config]: cache.config });
      renderPromptPreview();
      syncActionState();
    });

    const header = document.createElement("div");
    header.className = "prompt-preview-item-header";

    const left = document.createElement("span");
    left.textContent = entry.label;

    const right = document.createElement("span");
    right.textContent = `Prompt ${entry.index + 1}`;

    const text = document.createElement("div");
    text.className = "prompt-preview-item-text";
    text.textContent = entry.prompt;

    header.appendChild(left);
    header.appendChild(right);
    item.appendChild(header);
    item.appendChild(text);
    ui.promptPreviewContainer.appendChild(item);
  }
}

function renderGallery() {
  const visibleResults = getVisibleResults();
  const selectedCount = cache.results.filter((item) => item.selected).length;
  ui.galleryCount.textContent = `${visibleResults.length}/${cache.results.length} ảnh | ${selectedCount} đã chọn`;
  ui.galleryContainer.replaceChildren();

  if (visibleResults.length === 0) {
    const empty = document.createElement("div");
    empty.className = "gallery-empty";
    empty.textContent = cache.results.length === 0
      ? "Chưa có ảnh nào trong gallery. Hãy bấm “Nhận diện ảnh hiện có” để quét ảnh trên tab Flow."
      : "Không có ảnh nào khớp với bộ lọc hiện tại.";
    ui.galleryContainer.appendChild(empty);
    return;
  }

  for (const item of visibleResults) {
    const card = document.createElement("article");
    card.className = "gallery-item";

    const image = document.createElement("img");
    image.className = "thumb";
    image.src = item.imageUrl;
    image.alt = item.prompt || "Ảnh Flow";
    image.loading = "lazy";
    card.appendChild(image);

    const body = document.createElement("div");
    body.className = "gallery-body";

    const checkboxLabel = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = Boolean(item.selected);
    checkbox.dataset.itemId = item.id;
    checkboxLabel.appendChild(checkbox);
    checkboxLabel.append(item.promptLabel || `Giữ ảnh #${item.imageIndex || "?"}`);

    const promptPreview = document.createElement("div");
    promptPreview.className = "prompt-preview";
    promptPreview.textContent = item.prompt || "Không có caption gần card ảnh.";

    const meta = document.createElement("div");
    meta.className = "gallery-meta";
    meta.textContent = new Date(item.generatedAt).toLocaleString("vi-VN");

    body.appendChild(checkboxLabel);
    body.appendChild(promptPreview);
    body.appendChild(meta);
    card.appendChild(body);
    ui.galleryContainer.appendChild(card);
  }
}

function getVisibleResults() {
  const filterText = normalizeText(ui.galleryFilterInput.value || "");
  if (!filterText) {
    return cache.results;
  }

  return cache.results.filter((item) => normalizeText(`${item.promptLabel || ""} ${item.prompt || ""}`).includes(filterText));
}

function syncActionState() {
  const selectedCount = cache.results.filter((item) => item.selected).length;
  ui.downloadFromFlowButton.disabled = selectedCount === 0;
  ui.clearGalleryButton.disabled = cache.results.length === 0;

  const entries = getPromptEntriesSafe();
  const hasPrompts = entries.length > 0;
  ui.fillSelectedPromptButton.disabled = !hasPrompts || !hasSelectedPrompt(entries.length);
  ui.fillNextPromptButton.disabled = !hasPrompts;
  ui.runAllPromptsButton.disabled = !hasPrompts;
  ui.stopPromptRunButton.disabled = false;
  ui.resetAllButton.disabled = !cache.config.rawPrompts.trim() && !cache.config.galleryFilter.trim() && cache.results.length === 0;
}

function getPromptEntriesSafe() {
  const rawValue = String(cache.config.rawPrompts || "");
  if (!rawValue.trim()) {
    return [];
  }

  try {
    return parsePromptEntries(rawValue);
  } catch (error) {
    return [];
  }
}

function clampPromptIndex(index, total) {
  if (!Number.isFinite(Number(index))) {
    return 0;
  }

  const normalized = Number(index);
  return Math.max(0, Math.min(total - 1, normalized));
}

function hasSelectedPrompt(totalPrompts) {
  const selectedIndex = Number(cache.config.selectedPromptIndex);
  return Number.isFinite(selectedIndex) && selectedIndex >= 0 && selectedIndex < totalPrompts;
}

function resolveNextPromptIndex(totalPrompts) {
  const last = Number(cache.config.lastFilledPromptIndex);
  if (!Number.isFinite(last) || last < 0) {
    return clampPromptIndex(cache.config.selectedPromptIndex, totalPrompts);
  }

  if (last >= totalPrompts - 1) {
    return 0;
  }

  return last + 1;
}

async function fillPromptToFlow(entry, totalPrompts) {
  const tab = await getActiveTab();
  assertTabIsScriptable(tab);
  await ensureContentScript(tab.id);

  const response = await tabsSendMessage(tab.id, {
    type: "FLOW_FILL_PROMPT",
    payload: {
      prompt: entry.prompt,
      promptIndex: entry.index
    }
  });

  if (!response?.ok) {
    throw new Error(response?.error || "Flow không xác nhận thao tác điền prompt.");
  }

  setMessage(
    `Đã điền prompt ${entry.index + 1}/${totalPrompts} vào ô nhập của Flow.`,
    "success"
  );
}

function setMessage(message, tone = "default") {
  currentMessage = {
    text: message,
    tone
  };
  renderStatus();
}

function parsePromptEntries(rawValue) {
  const value = rawValue.trim();

  if (!value) {
    return [];
  }

  if (value.startsWith("[")) {
    let parsed;
    try {
      parsed = JSON.parse(value);
    } catch (error) {
      throw new Error(`JSON không hợp lệ: ${error.message}`);
    }

    if (!Array.isArray(parsed)) {
      throw new Error("JSON phải là mảng chuỗi hoặc mảng object chứa prompt.");
    }

    const normalized = parsed
      .map((item, index) => normalizeJsonPromptItem(item, index))
      .filter(Boolean);

    if (normalized.length === 0) {
      throw new Error("JSON array không chứa prompt hợp lệ nào.");
    }

    return normalized;
  }

  const promptBlocks = value
    .split(/\r?\n\s*\r?\n/g)
    .map((block, index) => createPromptEntry({ prompt: block.trim(), index }))
    .filter(Boolean);

  if (promptBlocks.length > 1) {
    return promptBlocks;
  }

  return value
    .split(/\r?\n/)
    .map((line, index) => createPromptEntry({ prompt: line.trim(), index }))
    .filter(Boolean);
}

function normalizeJsonPromptItem(item, index) {
  if (typeof item === "string") {
    return createPromptEntry({ prompt: item.trim(), index });
  }

  if (!item || typeof item !== "object" || Array.isArray(item)) {
    throw new Error(`Phần tử JSON ở vị trí ${index + 1} không hợp lệ.`);
  }

  const candidateFields = [
    "full_prompt",
    "prompt",
    "fullPrompt",
    "text",
    "content",
    "description",
    "details"
  ];

  for (const fieldName of candidateFields) {
    const value = item[fieldName];
    if (typeof value === "string" && value.trim()) {
      return createPromptEntry({
        prompt: value.trim(),
        index,
        id: item.id,
        theme: item.theme
      });
    }
  }

  throw new Error(`Object ở vị trí ${index + 1} chưa có trường prompt hợp lệ.`);
}

function createPromptEntry(options) {
  const prompt = String(options?.prompt || "").trim();
  if (!prompt) {
    return null;
  }

  const index = Number(options?.index) || 0;
  const theme = typeof options?.theme === "string" ? options.theme.trim() : "";
  const sourceId = options?.id;
  const labelParts = [`#${index + 1}`];

  if (sourceId !== undefined && sourceId !== null && String(sourceId).trim() !== "") {
    labelParts.push(`ID ${sourceId}`);
  }

  if (theme) {
    labelParts.push(theme);
  }

  return {
    prompt,
    index,
    id: sourceId ?? null,
    theme,
    label: labelParts.join(" • ")
  };
}

async function autoSyncSessionImages() {
  try {
    const tab = await getFlowTargetTab();
    if (!tab?.id || !isUsableWebTab(tab) || !isFlowTab(tab)) {
      return;
    }

    await ensureContentScript(tab.id);
    const { items: importedItems } = await collectSessionImagesFromTab(tab.id);
    if (importedItems.length === 0) {
      return;
    }

    const mergedResults = dedupeResultsByUrl([...importedItems, ...cache.results]);
    if (mergedResults.length === cache.results.length) {
      return;
    }

    cache.results = mergedResults;
    await storageSet({ [STORAGE_KEYS.results]: mergedResults });
    renderAll();
  } catch (error) {
    console.warn("Không auto-sync được ảnh session:", error);
  }
}

async function getActiveTab() {
  const flowTab = await getFlowTargetTab();
  if (flowTab?.id) {
    return flowTab;
  }

  const tabs = await chrome.tabs.query({ currentWindow: true });
  return tabs.find((tab) => tab.active && isUsableWebTab(tab)) || tabs.find((tab) => isUsableWebTab(tab)) || tabs[0];
}

async function getFlowTargetTab() {
  const tabs = await chrome.tabs.query({ currentWindow: true });
  const activeFlowTab = tabs.find((tab) => tab.active && isFlowTab(tab));
  if (activeFlowTab) {
    return activeFlowTab;
  }

  return tabs.find((tab) => isFlowTab(tab)) || null;
}

function assertTabIsScriptable(tab) {
  if (!tab?.id) {
    throw new Error("Không tìm thấy tab Flow hợp lệ.");
  }

  const url = tab.url || "";
  if (!/^https?:\/\//i.test(url)) {
    throw new Error("Tab hiện tại không phải trang web HTTP/HTTPS nên extension không thể inject script.");
  }
}

function isUsableWebTab(tab) {
  const url = tab?.url || "";
  return /^https?:\/\//i.test(url);
}

function isFlowTab(tab) {
  const url = tab?.url || "";
  return /^https?:\/\/labs\.google\/fx\//i.test(url) && url.includes("/tools/flow/");
}

async function ensureContentScript(tabId) {
  try {
    await tabsSendMessage(tabId, { type: "FLOW_BATCH_PING" });
    return;
  } catch (error) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"]
    });
  }

  await tabsSendMessage(tabId, { type: "FLOW_BATCH_PING" });
}

async function collectSessionImagesFromTab(tabId) {
  const response = await tabsSendMessage(tabId, { type: "FLOW_SYNC_SESSION_IMAGES" });
  if (!response?.ok) {
    throw new Error(response?.error || "Content script không trả về được danh sách ảnh session.");
  }

  return {
    items: Array.isArray(response.items) ? response.items : [],
    diagnostics: response.diagnostics || null
  };
}

function dedupeResultsByUrl(items) {
  const map = new Map();

  for (const item of items) {
    const key = String(item?.imageUrl || "").trim();
    if (!key) {
      continue;
    }

    const previous = map.get(key);
    if (!previous) {
      map.set(key, item);
      continue;
    }

    const previousPrompt = String(previous.prompt || "").trim();
    const nextPrompt = String(item.prompt || "").trim();
    const shouldReplace = nextPrompt.length > previousPrompt.length;
    map.set(key, shouldReplace ? item : previous);
  }

  return Array.from(map.values());
}

function formatImageSampleDiagnostics(sampleImages) {
  if (!Array.isArray(sampleImages) || sampleImages.length === 0) {
    return "";
  }

  const lines = sampleImages.map((item) =>
    `\n- img#${item.index}: ${item.width}x${item.height}, natural=${item.naturalWidth}x${item.naturalHeight}, visible=${item.visible}, accepted=${item.accepted}, alt="${item.alt}", src="${item.src}"`
  );

  return `\nMẫu ảnh:\n${lines.join("")}`;
}

function normalizeText(value) {
  return String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
}

function tabsSendMessage(tabId, message) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      const lastError = chrome.runtime.lastError;
      if (lastError) {
        reject(new Error(lastError.message));
        return;
      }

      resolve(response);
    });
  });
}

function storageGet(keys) {
  return chrome.storage.local.get(keys);
}

function storageSet(values) {
  return chrome.storage.local.set(values);
}

