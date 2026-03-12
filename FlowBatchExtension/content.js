(function initializeFlowBatchContentScript() {
  if (window.__flowBatchExtensionInitialized) {
    return;
  }

  window.__flowBatchExtensionInitialized = true;

  const STORAGE_KEYS = {
    state: "flowBatchState",
    results: "flowBatchResults",
    sidebar: "flowSidebarState"
  };

  const FLOW_HINTS = {
    // TODO(User): Nếu Flow đổi UI, ưu tiên thêm selector thật của bạn lên đầu các mảng này.
    // Bản hiện tại đã tối ưu theo UI trong ảnh: composer ở đáy màn hình, gallery dạng card lớn.
    promptInput: [
      'div[role="textbox"]',
      '[role="textbox"]',
      'div[aria-label="Bạn muốn tạo gì?"]',
      'div[aria-label*="Bạn muốn tạo gì"]',
      'input[aria-label="Văn bản có thể chỉnh sửa"]',
      'input[aria-label*="Văn bản có thể chỉnh sửa"]',
      'textarea[aria-label="Bạn muốn tạo gì?"]',
      'textarea[placeholder="Bạn muốn tạo gì?"]',
      'textarea[placeholder*="Mô tả ý tưởng của bạn"]',
      'textarea[aria-label*="Câu lệnh"]',
      'textarea[placeholder*="Bạn muốn tạo gì"]',
      'textarea[aria-label*="Bạn muốn tạo gì"]',
      'textarea[placeholder*="What do you want"]',
      'textarea[aria-label*="What do you want"]',
      'div[contenteditable="true"][aria-label*="Bạn muốn tạo gì"]',
      'div[contenteditable="true"][aria-label*="What do you want"]',
      'textarea',
      '[role="textbox"][contenteditable="true"]',
      '[contenteditable="true"]'
    ],
    generateButton: [
      'button[aria-label="Tạo hình ảnh"]',
      'button[title="Tạo hình ảnh"]',
      'button[aria-label*="Generate image"]',
      'button[aria-label*="Generate"]',
      'button[title*="Generate"]',
      'button[type="submit"]'
    ],
    loadingIndicators: [
      '[aria-busy="true"]',
      '[role="progressbar"]',
      '[data-state="loading"]',
      '[data-loading="true"]',
      'svg.animate-spin',
      '.loading',
      '.spinner'
    ],
    resultImages: [
      'main img',
      'img[alt*="Hình ảnh được tạo"]',
      'img[aria-label*="Hình ảnh được tạo"]',
      'img[alt*="Generated image"]',
      'img[aria-label*="Generated image"]',
      'picture img',
      'img[data-nimg]',
      'img[src*="googleusercontent"]',
      'img[srcset]',
      'img[src*="gstatic"]',
      'img[src^="blob:"]',
      'video[poster]',
      'canvas'
    ],
    settingsTriggers: [
      'button[aria-label*="settings_2"]',
      'button[title*="settings_2"]',
      'button[aria-label*="cài đặt"]',
      'button[title*="cài đặt"]',
      'button[aria-label*="Xem chế độ cài đặt"]',
      'button[title*="Xem chế độ cài đặt"]'
    ],
    generationTypeTriggers: [
      'button[aria-label*="Image"]',
      'button[aria-label*="Video"]',
      'button[title*="Image"]',
      'button[title*="Video"]'
    ],
    modelTriggers: [
      'button[aria-label*="Mô hình"]',
      'button[title*="Mô hình"]',
      'button[aria-label*="Model"]',
      'button[title*="Model"]',
      'button[aria-label*="Nano Banana"]',
      'button[title*="Nano Banana"]',
      'button[aria-label*="Imagen"]',
      'button[title*="Imagen"]'
    ],
    quantityTriggers: [
      'button[aria-label="x1"]',
      'button[aria-label="x2"]',
      'button[aria-label="x3"]',
      'button[aria-label="x4"]',
      'button[aria-label*="hình ảnh"]',
      'button[title*="hình ảnh"]',
      'button[aria-label*="Quantity"]',
      'button[title*="Quantity"]'
    ],
    aspectTriggers: [
      'button[aria-label*="Ngang"]',
      'button[aria-label*="Dọc"]',
      'button[title*="Ngang"]',
      'button[title*="Dọc"]',
      'button[aria-label*="Tỷ lệ khung hình"]',
      'button[title*="Tỷ lệ khung hình"]',
      'button[aria-label*="Aspect"]',
      'button[title*="Aspect"]'
    ]
  };

  const FLOW_TIMING = {
    interactionDelayMs: 350,
    directDownloadActionDelayMs: 500,
    pollIntervalMs: 1200,
    settleTimeMs: 2200,
    generationTimeoutMs: 90000,
    readyCooldownMs: 4200,
    stableCountMs: 7000,
    noGrowthMs: 5000,
    minimumGenerationMs: 12000
  };

  const FLOW_ERROR_TEXTS = [
    "prompt must be provided",
    "nhập một câu lệnh trước khi gửi",
    "bạn không được để trống câu lệnh",
    "please write a prompt",
    "empty prompt"
  ];

  const FLOW_APP_CRASH_TEXTS = [
    "application error: a client-side exception has occurred",
    "a client-side exception has occurred while loading labs.google"
  ];

  const runtimeState = {
    isRunning: false,
    stopRequested: false,
    sidebarMounted: false
  };

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message?.type) {
      return false;
    }

    if (message.type === "FLOW_BATCH_PING") {
      sendResponse({ ok: true, ready: true });
      return false;
    }

    if (message.type === "FLOW_TOGGLE_SIDEBAR") {
      void toggleSidebar()
        .then((result) => sendResponse({ ok: true, ...result }))
        .catch((error) => sendResponse({ ok: false, error: error.message || "Không thể toggle sidebar." }));
      return true;
    }

    if (message.type === "FLOW_BATCH_START") {
      void validateStartRequest(message.payload)
        .then(() => {
          runtimeState.isRunning = true;
          void runBatchSafely(message.payload);
          sendResponse({ ok: true, started: true });
        })
        .catch((error) => {
          sendResponse({ ok: false, error: buildDiagnosticError(error.message) });
        });
      return true;
    }

    if (message.type === "FLOW_BATCH_STOP") {
      runtimeState.stopRequested = true;
      sendResponse({ ok: true, stopping: true });
      return false;
    }

    if (message.type === "FLOW_FILL_PROMPT") {
      void fillPromptOnDemand(message.payload)
        .then((result) => sendResponse({ ok: true, ...result }))
        .catch((error) => sendResponse({ ok: false, error: error.message || "Không thể điền prompt vào Flow." }));
      return true;
    }

    if (message.type === "FLOW_AUTOFILL_PROMPTS") {
      void validateAutofillRequest(message.payload)
        .then(() => {
          runtimeState.isRunning = true;
          runtimeState.stopRequested = false;
          void runAutofillSequenceSafely(message.payload);
          sendResponse({ ok: true, started: true });
        })
        .catch((error) => sendResponse({ ok: false, error: error.message || "Không thể chạy tự động prompt." }));
      return true;
    }

    if (message.type === "FLOW_AUTOFILL_STOP") {
      runtimeState.stopRequested = true;
      sendResponse({ ok: true, stopping: true });
      return false;
    }

    if (message.type === "FLOW_SYNC_SESSION_IMAGES") {
      try {
        validatePageContext();
        const items = collectSessionResultItems();
        sendResponse({ ok: true, items, diagnostics: buildImageDiagnostics() });
      } catch (error) {
        sendResponse({ ok: false, error: error.message || "Không thể quét ảnh session hiện tại." });
      }
      return false;
    }

    if (message.type === "FLOW_DOWNLOAD_SELECTED_FROM_FLOW" || message.type === "FLOW_CROP_SQUARE_AND_DOWNLOAD_CURRENT") {
      void automateDownloadSelectedItemsFromFlow(message.payload?.items)
        .then((result) => sendResponse({ ok: true, ...result }))
        .catch((error) => sendResponse({ ok: false, error: error.message || "Không thể tải ảnh đã chọn trực tiếp từ Flow." }));
      return true;
    }

    return false;
  });

  removeLegacySidebarHost();

  async function validateStartRequest(payload) {
    if (runtimeState.isRunning) {
      throw new Error("Content script đang chạy một batch khác.");
    }

    const config = payload?.config;
    const prompts = payload?.prompts;

    if (!config || !Array.isArray(prompts) || prompts.length === 0) {
      throw new Error("Payload batch không hợp lệ.");
    }

    validatePageContext();
    await ensureComposerReady();

    if (!findPromptInput()) {
      throw new Error(
        "Không tìm thấy ô nhập prompt của Flow. Hãy mở đúng project Flow và nếu cần thì bổ sung selector vào FLOW_HINTS.promptInput trong content.js."
      );
    }

    if (!findGenerateButton()) {
      throw new Error(
        "Không tìm thấy nút generate của Flow. Hãy bổ sung selector vào FLOW_HINTS.generateButton hoặc kiểm tra xem composer đã hiện đầy đủ chưa."
      );
    }
  }

  async function fillPromptOnDemand(payload) {
    if (runtimeState.isRunning) {
      throw new Error("Batch đang chạy. Hãy dừng batch trước khi điền prompt thủ công.");
    }

    const prompt = String(payload?.prompt || "").trim();
    if (!prompt) {
      throw new Error("Prompt rỗng, không thể điền vào Flow.");
    }

    validatePageContext();
    await ensureComposerReady();
    const promptInput = await populatePromptEditor(prompt);
    if (!promptInput) {
      throw new Error("Không thể điền prompt vào composer của Flow. Hãy kiểm tra lại UI hiện tại của Flow.");
    }

    return {
      filled: true,
      promptIndex: Number(payload?.promptIndex) || 0
    };
  }

  async function validateAutofillRequest(payload) {
    if (runtimeState.isRunning) {
      throw new Error("Đang có một luồng automation khác chạy trên Flow.");
    }

    const prompts = Array.isArray(payload?.prompts) ? payload.prompts.map((item) => String(item || "").trim()).filter(Boolean) : [];
    if (prompts.length === 0) {
      throw new Error("Danh sách prompt để chạy tự động đang rỗng.");
    }

    validatePageContext();
    await ensureComposerReady();

    if (!findPromptInput()) {
      throw new Error("Không tìm thấy ô nhập prompt của Flow.");
    }

    if (!findGenerateButton()) {
      throw new Error("Không tìm thấy nút Generate trên composer của Flow.");
    }
  }

  async function runAutofillSequenceSafely(payload) {
    try {
      await runAutofillSequence(payload);
    } catch (error) {
      console.error("Flow autofill bị lỗi:", error);
    } finally {
      runtimeState.isRunning = false;
      runtimeState.stopRequested = false;
    }
  }

  async function runAutofillSequence(payload) {
    const prompts = Array.isArray(payload?.prompts) ? payload.prompts.map((item) => String(item || "").trim()).filter(Boolean) : [];
    const delayMs = Math.max(10000, Number(payload?.delayMs) || 10000);
    const longPauseEvery = Math.max(1, Number(payload?.longPauseEvery) || 5);
    const longPauseMs = Math.max(delayMs, Number(payload?.longPauseMs) || 20000);

    for (let index = 0; index < prompts.length; index += 1) {
      throwIfStopRequested();
      const prompt = prompts[index];

      await ensureComposerReady();
      const promptInput = await populatePromptEditor(prompt);
      if (!promptInput) {
        throw new Error(`Không thể điền prompt #${index + 1} vào Flow.`);
      }

      await wait(FLOW_TIMING.interactionDelayMs);
      await submitPromptOnce();
      await wait(500);
      await clearPromptComposerForAutofill();

      if (index >= prompts.length - 1) {
        continue;
      }

      const completedCount = index + 1;
      const pauseMs = completedCount % longPauseEvery === 0 ? longPauseMs : delayMs;
      await wait(pauseMs);
    }
  }

  async function clearPromptComposerForAutofill() {
    try {
      await clearPromptComposer();
      return;
    } catch (error) {
      console.warn("Xóa prompt theo nhánh chuẩn bị lỗi, chuyển sang xóa cưỡng bức:", error);
    }

    const candidates = getPromptCandidates();
    let touchedAny = false;

    for (const candidate of candidates) {
      try {
        const target = resolvePromptEditingTarget(candidate);
        if (!target) {
          continue;
        }

        touchedAny = true;
        await forceClearPromptTarget(target);
      } catch (error) {
        console.warn("Không thể xóa cưỡng bức prompt ở candidate:", candidate, error);
      }
    }

    if (!touchedAny) {
      throw new Error("Không tìm thấy editor hợp lệ để chuẩn bị prompt kế tiếp.");
    }
  }

  function buildDiagnosticError(message) {
    const promptCandidates = describeElements(
      Array.from(document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"], [role="textbox"]'))
        .filter((element) => isVisible(element))
        .slice(0, 6)
    );

    const buttonCandidates = describeElements(
      Array.from(document.querySelectorAll("button, [role='button']"))
        .filter((element) => isVisible(element))
        .slice(0, 12)
    );

    return [
      message,
      "",
      "Ứng viên prompt đang thấy trên trang:",
      promptCandidates || "- Không thấy textarea/input/contenteditable nào đủ điều kiện.",
      "",
      "Ứng viên button đang thấy trên trang:",
      buttonCandidates || "- Không thấy button hiển thị nào đủ điều kiện."
    ].join("\n");
  }

  function validatePageContext() {
    if (!/^https?:$/i.test(window.location.protocol)) {
      throw new Error("Tab hiện tại không phải trang web hợp lệ để chạy automation.");
    }

    if (!window.location.href.includes("/tools/flow/")) {
      throw new Error("Tab hiện tại không phải trang Flow. Hãy mở đúng project Flow rồi chạy extension.");
    }
  }

  function removeLegacySidebarHost() {
    document.getElementById("flow-batch-sidebar-host")?.remove();
  }

  async function ensureComposerReady() {
    if (findPromptInput() && !isEmptyScenePage()) {
      return;
    }

    if (!isEmptyScenePage()) {
      return;
    }

    const backButton = findBackToProjectButton();
    if (!(backButton instanceof HTMLElement)) {
      throw new Error("Trang hiện tại đang ở scene rỗng và không tìm thấy nút Back to project để quay về composer.");
    }

    backButton.click();
    await waitForComposer(12000);
  }

  function isEmptyScenePage() {
    const pageText = normalizeText(document.body.innerText || "");
    return pageText.includes("add clips from your project to create a scene")
      || pageText.includes("back to project");
  }

  function findBackToProjectButton() {
    return findActionButtonByLabels(["back to project", "quay lại project", "back to project arrow_back"]) || null;
  }

  async function waitForComposer(timeoutMs) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      if (findPromptInput() && !isEmptyScenePage()) {
        return;
      }

      await wait(250);
    }

    throw new Error("Đã quay lại project nhưng composer tạo ảnh chưa xuất hiện.");
  }

  async function toggleSidebar() {
    validatePageContext();

    const existing = document.getElementById("flow-batch-sidebar-host");
    if (existing) {
      const collapsed = existing.dataset.collapsed === "true";
      if (collapsed) {
        await setSidebarCollapsed(false);
        return { visible: true, collapsed: false };
      }

      await unmountSidebar({ preservePinnedState: false });
      return { visible: false, collapsed: false };
    }

    const stored = await storageGet(STORAGE_KEYS.sidebar);
    const sidebarState = stored[STORAGE_KEYS.sidebar] || {};
    await mountSidebar({
      pinned: Boolean(sidebarState?.pinned),
      collapsed: false
    });
    return { visible: true, collapsed: false };
  }

  async function mountSidebar(options = {}) {
    if (document.getElementById("flow-batch-sidebar-host")) {
      return;
    }

    const host = document.createElement("aside");
    host.id = "flow-batch-sidebar-host";
    host.dataset.collapsed = options.collapsed ? "true" : "false";
    host.dataset.pinned = options.pinned ? "true" : "false";

    Object.assign(host.style, {
      position: "fixed",
      top: "16px",
      right: "16px",
      width: options.collapsed ? "56px" : "460px",
      height: "calc(100vh - 32px)",
      maxHeight: "980px",
      zIndex: "2147483646",
      borderRadius: "24px",
      overflow: "hidden",
      background: "rgba(16, 16, 18, 0.82)",
      boxShadow: "0 20px 48px rgba(0,0,0,0.32)",
      backdropFilter: "blur(16px)",
      border: "1px solid rgba(255,255,255,0.14)",
      transition: "width 180ms ease, transform 180ms ease, opacity 180ms ease"
    });

    const header = document.createElement("div");
    Object.assign(header.style, {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "8px",
      padding: "12px 12px 10px 14px",
      background: "linear-gradient(180deg, rgba(27,27,31,0.96), rgba(27,27,31,0.78))",
      borderBottom: "1px solid rgba(255,255,255,0.08)"
    });

    const title = document.createElement("div");
    title.textContent = "Flow Batch Sidebar";
    Object.assign(title.style, {
      color: "#f7efe4",
      font: "600 13px/1.2 'Segoe UI', sans-serif",
      letterSpacing: "0.02em"
    });

    const controls = document.createElement("div");
    Object.assign(controls.style, {
      display: "flex",
      gap: "8px"
    });

    const pinButton = createSidebarControlButton(options.pinned ? "Bỏ ghim" : "Ghim");
    const collapseButton = createSidebarControlButton(options.collapsed ? "Mở" : "Thu");
    const closeButton = createSidebarControlButton("Đóng");

    pinButton.addEventListener("click", async () => {
      const nextPinned = host.dataset.pinned !== "true";
      host.dataset.pinned = nextPinned ? "true" : "false";
      pinButton.textContent = nextPinned ? "Bỏ ghim" : "Ghim";
      await persistSidebarState({
        pinned: nextPinned,
        collapsed: host.dataset.collapsed === "true"
      });
    });

    collapseButton.addEventListener("click", async () => {
      const nextCollapsed = host.dataset.collapsed !== "true";
      await setSidebarCollapsed(nextCollapsed);
      collapseButton.textContent = nextCollapsed ? "Mở" : "Thu";
    });

    closeButton.addEventListener("click", async () => {
      await unmountSidebar({ preservePinnedState: host.dataset.pinned === "true" });
    });

    controls.append(pinButton, collapseButton, closeButton);
    header.append(title, controls);

    const frame = document.createElement("iframe");
    frame.src = chrome.runtime.getURL("popup.html") + "?sidebar=1";
    frame.title = "Flow Batch Sidebar";
    frame.allow = "clipboard-read; clipboard-write";
    Object.assign(frame.style, {
      width: "100%",
      height: "calc(100% - 52px)",
      border: "0",
      background: "transparent"
    });

    host.append(header, frame);
    document.documentElement.appendChild(host);
    runtimeState.sidebarMounted = true;

    await persistSidebarState({
      pinned: Boolean(options.pinned),
      collapsed: Boolean(options.collapsed)
    });
  }

  function createSidebarControlButton(label) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    Object.assign(button.style, {
      appearance: "none",
      border: "1px solid rgba(255,255,255,0.14)",
      background: "rgba(255,255,255,0.08)",
      color: "#f7efe4",
      borderRadius: "999px",
      padding: "8px 12px",
      cursor: "pointer",
      font: "600 12px/1 'Segoe UI', sans-serif"
    });
    return button;
  }

  async function setSidebarCollapsed(collapsed) {
    const host = document.getElementById("flow-batch-sidebar-host");
    if (!host) {
      return;
    }

    host.dataset.collapsed = collapsed ? "true" : "false";
    host.style.width = collapsed ? "56px" : "460px";

    const frame = host.querySelector("iframe");
    const header = host.firstElementChild;
    if (frame instanceof HTMLIFrameElement) {
      frame.style.display = collapsed ? "none" : "block";
    }
    if (header instanceof HTMLElement) {
      header.style.paddingRight = collapsed ? "6px" : "12px";
    }

    await persistSidebarState({
      pinned: host.dataset.pinned === "true",
      collapsed
    });
  }

  async function unmountSidebar(options = {}) {
    const host = document.getElementById("flow-batch-sidebar-host");
    if (!host) {
      return;
    }

    const preservePinnedState = Boolean(options.preservePinnedState);
    host.remove();
    runtimeState.sidebarMounted = false;

    await persistSidebarState({
      pinned: preservePinnedState,
      collapsed: false
    });
  }

  async function persistSidebarState(state) {
    await storageSet({
      [STORAGE_KEYS.sidebar]: {
        pinned: Boolean(state?.pinned),
        collapsed: Boolean(state?.collapsed)
      }
    });
  }

  async function runBatchSafely(payload) {
    try {
      await runBatch(payload.config, payload.prompts, Number(payload.startIndex) || 0);
    } catch (error) {
      console.error("Flow batch bị lỗi:", error);
    } finally {
      runtimeState.isRunning = false;
      runtimeState.stopRequested = false;
    }
  }

  async function runBatch(config, prompts, startIndex = 0) {
    const normalizedStartIndex = Math.max(0, Math.min(startIndex, Math.max(0, prompts.length - 1)));
    await ensureComposerReady();

    await updateBatchState({
      status: "running",
      totalPrompts: prompts.length,
      currentPromptIndex: normalizedStartIndex,
      currentPrompt: "",
      lastError: "",
      startedAt: new Date().toISOString(),
      completedAt: null,
      stopRequested: false,
      resumeStartIndex: normalizedStartIndex + 1
    });

    let accumulatedResults = dedupeResults(mergeByUrl(await getStoredResults(), collectSessionResultItems()));
    await storageSet({
      [STORAGE_KEYS.results]: accumulatedResults
    });

    try {
      for (let index = normalizedStartIndex; index < prompts.length; index += 1) {
        throwIfStopRequested();

        const prompt = prompts[index];

        await updateBatchState({
          status: "running",
          totalPrompts: prompts.length,
          currentPromptIndex: index + 1,
          currentPrompt: prompt,
          lastError: ""
        });

        const beforeSnapshot = snapshotResultImages();

        await applyGenerationSettings(config, prompt);
        await wait(FLOW_TIMING.interactionDelayMs);
        await submitPromptWithRetry(prompt);

        const newUrls = await waitForGenerationCompletion(beforeSnapshot, Number(config.quantity) || 1);

        const newItems = newUrls.map((imageUrl, imageIndex) => ({
          id: createResultId(index + 1, imageIndex + 1),
          prompt,
          imageUrl,
          selected: true,
          generatedAt: new Date().toISOString(),
          batchIndex: index + 1,
          imageIndex: imageIndex + 1
        }));

        if (newItems.length > 0) {
          accumulatedResults = dedupeResults([...accumulatedResults, ...newItems]);
          await storageSet({
            [STORAGE_KEYS.results]: accumulatedResults
          });
        } else {
          console.warn(`Không trích xuất được URL ảnh mới cho prompt #${index + 1}, nhưng Flow đã ổn định nên sẽ chuyển sang prompt tiếp theo.`);
        }

        await clearPromptComposer();
      }

      await updateBatchState({
        status: "completed",
        currentPromptIndex: prompts.length,
        currentPrompt: "",
        lastError: "",
        completedAt: new Date().toISOString(),
        stopRequested: false
      });
    } catch (error) {
      if (isStoppedError(error)) {
        await updateBatchState({
          status: "stopped",
          currentPrompt: "",
          lastError: "Batch đã được dừng theo yêu cầu.",
          completedAt: new Date().toISOString(),
          stopRequested: false
        });
        return;
      }

      await updateBatchState({
        status: "error",
        lastError: error.message || "Batch bị lỗi.",
        completedAt: new Date().toISOString(),
        stopRequested: false
      });
      throw error;
    }
  }

  async function applyGenerationSettings(config, prompt) {
    await ensureComposerReady();
    const promptInput = await populatePromptEditor(prompt);
    if (!promptInput) {
      throw new Error("Không thể ghi prompt vào editor của Flow. Composer hiện tại có thể là editor động chưa được map đúng.");
    }
    await wait(FLOW_TIMING.interactionDelayMs);

    await ensureSettingsPanelOpen();

    await bestEffortSelectValue({
      label: "Generation Type",
      desiredValue: config.generationType || "Image",
      desiredAliases: buildGenerationTypeAliases(config.generationType || "Image"),
      directTriggerCandidates: FLOW_HINTS.generationTypeTriggers,
      genericTextPatterns: ["image", "video", "ảnh", "hình ảnh"],
      quietWhenMissing: true
    });

    await bestEffortSelectValue({
      label: "Orientation",
      desiredValue: config.aspectRatio,
      desiredAliases: buildOrientationAliases(config.aspectRatio),
      directTriggerCandidates: FLOW_HINTS.aspectTriggers,
      genericTextPatterns: ["ngang", "dọc", "landscape", "portrait", "orientation", "hướng"],
      quietWhenMissing: true
    });

    await bestEffortSelectValue({
      label: "Quantity",
      desiredValue: `x${config.quantity}`,
      desiredAliases: [String(config.quantity), `${config.quantity} ảnh`, `${config.quantity} hình ảnh`, `${config.quantity} images`],
      directTriggerCandidates: FLOW_HINTS.quantityTriggers,
      genericTextPatterns: ["quantity", "số lượng", "x1", "x2", "x3", "x4"]
    });

    await bestEffortSelectValue({
      label: "Model",
      desiredValue: config.model,
      directTriggerCandidates: FLOW_HINTS.modelTriggers,
      genericTextPatterns: ["model", "mô hình", "nano banana", "imagen"]
    });
  }

  async function populatePromptEditor(prompt) {
    const candidates = getPromptCandidates();

    for (const candidate of candidates) {
      try {
        const target = resolvePromptEditingTarget(candidate);
        if (!target) {
          continue;
        }

        await typePromptWithDebugger(target, prompt);
        await wait(180);

        if (promptLooksApplied(readPromptValue(target), prompt)) {
          return target;
        }
      } catch (error) {
        console.warn("Không ghi được prompt vào candidate:", candidate, error);
      }
    }

    return null;
  }

  async function reinforcePromptState(prompt) {
    const candidates = getPromptCandidates().slice(0, 5);

    for (const candidate of candidates) {
      try {
        const target = resolvePromptEditingTarget(candidate);
        if (!target) {
          continue;
        }

        await typePromptWithDebugger(target, prompt);
        await wait(120);
      } catch (error) {
        console.warn("Không reinforce được prompt cho candidate:", candidate, error);
      }
    }
  }

  async function submitPromptWithRetry(prompt) {
    await clickGenerateButton();
    await wait(650);

    let submissionError = detectSubmissionError();
    if (!submissionError) {
      return;
    }

    if (!isPromptMissingError(submissionError)) {
      throw new Error(submissionError);
    }

    await reinforcePromptState(prompt);
    await wait(320);
    await clickGenerateButton();
    await wait(650);

    submissionError = detectSubmissionError();
    if (submissionError) {
      throw new Error(buildPromptSubmissionError(submissionError));
    }
  }

  async function submitPromptOnce() {
    await clickGenerateButton();
    await wait(700);

    const submissionError = detectSubmissionError();
    if (submissionError) {
      throw new Error(submissionError);
    }
  }

  function resolvePromptEditingTarget(candidate) {
    if (!(candidate instanceof HTMLElement)) {
      return null;
    }

    candidate.click();
    candidate.focus?.();

    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement && isPromptLikeElement(activeElement)) {
      return activeElement;
    }

    const nestedEditable = candidate.matches("input, textarea, [contenteditable='true'], [role='textbox']")
      ? candidate
      : candidate.querySelector("input, textarea, [contenteditable='true'], [role='textbox']");

    if (nestedEditable instanceof HTMLElement) {
      nestedEditable.click?.();
      nestedEditable.focus?.();
      return nestedEditable;
    }

    return null;
  }

  async function typePromptWithDebugger(element, value) {
    element.click?.();
    element.focus?.();
    await wait(80);

    const response = await runtimeSendMessage({
      type: "FLOW_DEBUGGER_TYPE",
      payload: { text: value }
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Không thể gõ prompt bằng chrome.debugger.");
    }
  }

  async function bestEffortSelectValue(options) {
    const {
      label,
      desiredValue,
      desiredAliases = [],
      directTriggerCandidates,
      genericTextPatterns,
      quietWhenMissing = false
    } = options;

    if (!desiredValue) {
      return;
    }

    const normalizedTargets = [desiredValue, ...desiredAliases].map(normalizeText);
    const settingsPanel = findSettingsPanel();
    const searchRoot = settingsPanel || document.body;
    const alreadyVisible = findClickableByExactText([desiredValue, ...desiredAliases], searchRoot);
    if (alreadyVisible) {
      alreadyVisible.click();
      await wait(220);
      return;
    }

    const trigger = findControlTrigger(
      directTriggerCandidates,
      genericTextPatterns,
      normalizedTargets,
      searchRoot
    );
    if (!trigger) {
      if (quietWhenMissing || settingValueAlreadyVisible([desiredValue, ...desiredAliases], searchRoot)) {
        return;
      }

      console.warn(`Không tìm thấy trigger cho ${label}. Giữ nguyên giá trị hiện tại trên Flow.`);
      return;
    }

    trigger.click();
    await wait(320);

    const optionScope = findSettingsPanel() || searchRoot;
    const option = findVisibleOptionByText([desiredValue, ...desiredAliases], optionScope);
    if (!option) {
      if (!elementTextMatches(trigger, normalizedTargets)) {
        console.warn(`Không tìm được option ${label}="${desiredValue}". Giữ nguyên giá trị hiện tại.`);
      }

      dismissOverlay();
      return;
    }

    option.click();
    option.dispatchEvent(new Event("change", { bubbles: true }));
    await wait(240);
  }

  function settingValueAlreadyVisible(values, scopeRoot = document.body) {
    const normalizedTargets = values.map(normalizeText).filter(Boolean);
    if (normalizedTargets.length === 0) {
      return false;
    }

    const text = normalizeText(scopeRoot.innerText || scopeRoot.textContent || "");
    return normalizedTargets.some((target) => text.includes(target));
  }

  function findPromptInput() {
    return getPromptCandidates()[0] || null;
  }

  function getPromptCandidates() {
    return findVisibleElements(FLOW_HINTS.promptInput)
      .filter((element) => element instanceof HTMLElement)
      .sort((a, b) => scorePromptCandidate(b) - scorePromptCandidate(a));
  }

  function scorePromptCandidate(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    let score = 0;

    if (element instanceof HTMLTextAreaElement) {
      score += 20;
    }

    if (element instanceof HTMLInputElement) {
      score += 18;
    }

    if (element.getAttribute("role") === "textbox") {
      score += 22;
    }

    if (element.isContentEditable) {
      score += 20;
    }

    if (text.includes("bạn muốn tạo gì")) {
      score += 16;
    }

    if (text.includes("mô tả ý tưởng")) {
      score += 12;
    }

    if (text.includes("văn bản có thể chỉnh sửa")) {
      score -= 6;
    }

    if (rect.width >= 220) {
      score += 8;
    }

    if (rect.bottom > window.innerHeight * 0.6) {
      score += 8;
    }

    return score;
  }

  function findGenerateButton() {
    const promptInput = findPromptInput();
    const composerRoot = findComposerRoot(promptInput);
    const exactComposerButton = findExactComposerGenerateButton(promptInput, composerRoot);
    if (exactComposerButton) {
      return exactComposerButton;
    }
    const promptNeighbor = findGenerateButtonNearPrompt(promptInput, composerRoot);

    if (promptNeighbor) {
      return promptNeighbor;
    }

    if (composerRoot) {
      const composerButtons = Array.from(composerRoot.querySelectorAll("button, [role='button']"))
        .filter((button) => isVisible(button))
        .filter((button) => !isDisallowedGenerateCandidate(button))
        .sort((a, b) => scoreGenerateButton(b, promptInput, composerRoot) - scoreGenerateButton(a, promptInput, composerRoot));

      const bestComposerButton = composerButtons[0];
      if (bestComposerButton && scoreGenerateButton(bestComposerButton, promptInput, composerRoot) >= 24) {
        return bestComposerButton;
      }
    }

    return null;
  }

  function findExactComposerGenerateButton(promptInput, composerRoot) {
    if (!(promptInput instanceof HTMLElement) || !(composerRoot instanceof HTMLElement)) {
      return null;
    }

    const promptRect = promptInput.getBoundingClientRect();
    const composerRect = composerRoot.getBoundingClientRect();
    const buttons = Array.from(composerRoot.querySelectorAll("button, [role='button']"))
      .filter((button) => isVisible(button))
      .filter((button) => !isDisallowedGenerateCandidate(button))
      .map((button) => {
        const rect = button.getBoundingClientRect();
        const text = normalizeText(getElementText(button));
        const iconText = normalizeText(button.querySelector("i, .material-icons, [class*='material']")?.textContent || "");
        let score = 0;

        if (iconText.includes("arrow_forward")) {
          score += 40;
        }

        if (text.includes("arrow_forward") || text.includes("tạo") || text.includes("generate") || text.includes("send")) {
          score += 20;
        }

        const horizontalGap = Math.abs(rect.left - promptRect.right);
        const verticalGap = Math.abs((rect.top + rect.height / 2) - (promptRect.top + promptRect.height / 2));
        score += Math.max(0, 24 - horizontalGap / 6);
        score += Math.max(0, 18 - verticalGap / 8);

        if (rect.left >= promptRect.right - 20) {
          score += 12;
        }

        if (rect.right <= composerRect.right + 4) {
          score += 8;
        }

        if (rect.width >= 28 && rect.width <= 72 && rect.height >= 28 && rect.height <= 72) {
          score += 10;
        }

        if (rect.bottom > window.innerHeight * 0.72) {
          score += 10;
        }

        return { button, score };
      })
      .sort((a, b) => b.score - a.score);

    return buttons[0]?.score >= 42 ? buttons[0].button : null;
  }

  function findGenerateButtonNearPrompt(promptInput, composerRoot) {
    if (!(promptInput instanceof HTMLElement)) {
      return null;
    }

    const promptRect = promptInput.getBoundingClientRect();
    const scopes = uniqueElements([
      composerRoot instanceof HTMLElement ? composerRoot : null,
      ...collectAncestorCandidates(promptInput, 6)
    ].filter(Boolean));
    const buttonPool = scopes.flatMap((scope) => Array.from(scope.querySelectorAll("button, [role='button']")));
    const candidates = uniqueElements(buttonPool)
      .filter((button) => isVisible(button))
      .filter((button) => !isDisallowedGenerateCandidate(button))
      .filter((button) => {
        const rect = button.getBoundingClientRect();
        const isSmall = rect.width >= 28 && rect.width <= 72 && rect.height >= 28 && rect.height <= 72;
        const toRight = rect.left >= promptRect.right - 24;
        const sameBand = Math.abs((rect.top + rect.height / 2) - (promptRect.top + promptRect.height / 2)) <= 90;
        const bottomComposerZone = rect.bottom > window.innerHeight * 0.72;
        return isSmall && toRight && sameBand && bottomComposerZone;
      })
      .map((button) => ({
        button,
        score: scoreNeighborGenerateButton(button, promptRect)
      }));

    candidates.sort((a, b) => b.score - a.score);
    return candidates[0]?.score >= 26 ? candidates[0].button : null;
  }

  function isDisallowedGenerateCandidate(button) {
    const text = normalizeText(getElementText(button));
    const ariaLabel = normalizeText(button.getAttribute("aria-label"));
    const blockedTokens = [
      "play_movies",
      "trình tạo cảnh",
      "search",
      "tìm kiếm",
      "filter",
      "sắp xếp",
      "settings",
      "cài đặt",
      "more_vert",
      "tùy chọn",
      "add",
      "thêm nội dung",
      "quay lại",
      "arrow_back",
      "gallery",
      "home"
    ];

    return blockedTokens.some((token) => text.includes(token) || ariaLabel.includes(token));
  }

  function scoreNeighborGenerateButton(button, promptRect) {
    const rect = button.getBoundingClientRect();
    const text = normalizeText(getElementText(button));
    const ariaLabel = normalizeText(button.getAttribute("aria-label"));
    let score = 0;

    const positiveTokens = ["arrow_forward", "arrow_upward", "send", "generate", "tạo"];
    const negativeTokens = ["play_movies", "trình tạo cảnh", "settings", "filter", "search", "add", "more_vert"];

    if (positiveTokens.some((token) => text.includes(token) || ariaLabel.includes(token))) {
      score += 16;
    }

    if (negativeTokens.some((token) => text.includes(token) || ariaLabel.includes(token))) {
      score -= 30;
    }

    const horizontalGap = Math.abs(rect.left - promptRect.right);
    const verticalGap = Math.abs((rect.top + rect.height / 2) - (promptRect.top + promptRect.height / 2));

    score += Math.max(0, 18 - horizontalGap / 8);
    score += Math.max(0, 12 - verticalGap / 10);

    if (rect.width <= 56 && rect.height <= 56) {
      score += 8;
    }

    if (rect.bottom > window.innerHeight * 0.78) {
      score += 10;
    }

    return score;
  }

  function scoreGenerateButton(button, promptInput, composerRoot) {
    const text = normalizeText(getElementText(button));
    const rect = button.getBoundingClientRect();
    let score = 0;
    const negativeTokens = [
      "search",
      "tìm kiếm",
      "filter",
      "sắp xếp",
      "settings",
      "cài đặt",
      "more_vert",
      "tùy chọn",
      "add",
      "thêm nội dung",
      "play_movies",
      "trình tạo cảnh",
      "quay lại",
      "arrow_back",
      "tạo thêm"
    ];
    const positiveTokens = [
      "generate",
      "tạo hình ảnh",
      "tạo",
      "send",
      "arrow_forward",
      "arrow_upward",
      "north_east",
      "subdirectory_arrow_right"
    ];

    if (positiveTokens.some((token) => text.includes(token))) {
      score += 14;
    }

    if (negativeTokens.some((token) => text.includes(token))) {
      score -= 26;
    }

    if (button.getAttribute("type") === "submit") {
      score += 8;
    }

    const ariaLabel = normalizeText(button.getAttribute("aria-label"));
    if (ariaLabel.includes("generate") || ariaLabel.includes("tạo")) {
      score += 10;
    }

    if ((text.includes("arrow") || text.includes("send")) && rect.width <= 72 && rect.height <= 72) {
      score += 10;
    }

    if (!text && rect.width <= 64 && rect.height <= 64) {
      score += 5;
    }

    if (rect.bottom > window.innerHeight * 0.72) {
      score += 8;
    }

    if (rect.top < window.innerHeight * 0.45) {
      score -= 8;
    }

    if (rect.width >= 32 && rect.width <= 72 && rect.height >= 32 && rect.height <= 72) {
      score += 6;
    }

    if (composerRoot instanceof HTMLElement && composerRoot.contains(button)) {
      score += 18;

      const composerRect = composerRoot.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      if (centerX >= composerRect.right - Math.max(72, composerRect.width * 0.2)) {
        score += 14;
      }

      if (centerY >= composerRect.top && centerY <= composerRect.bottom) {
        score += 8;
      }
    }

    if (promptInput instanceof HTMLElement) {
      const inputRect = promptInput.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const inputCenterY = inputRect.top + inputRect.height / 2;
      const verticalDistance = Math.abs(centerY - inputCenterY);
      const horizontalDistance = Math.abs(rect.left - inputRect.right);

      if (verticalDistance < 110) {
        score += 9;
      }

      if (horizontalDistance < 180) {
        score += 8;
      }

      if (centerX >= inputRect.right - 24) {
        score += 6;
      }

      if (rect.bottom > window.innerHeight * 0.72) {
        score += 6;
      }
    }

    return score;
  }

  function findComposerRoot(promptInput) {
    if (!(promptInput instanceof HTMLElement)) {
      return null;
    }

    let current = promptInput;
    let best = null;
    let bestScore = -Infinity;

    for (let depth = 0; current && depth < 7; depth += 1) {
      const parent = current.parentElement;
      if (!(parent instanceof HTMLElement)) {
        break;
      }

      const rect = parent.getBoundingClientRect();
      const buttons = Array.from(parent.querySelectorAll("button, [role='button']"))
        .filter((button) => isVisible(button));

      let score = 0;
      if (rect.width >= 320) {
        score += 8;
      }
      if (rect.bottom > window.innerHeight * 0.68) {
        score += 10;
      }
      if (buttons.length > 0) {
        score += 10;
      }

      const rightSideButton = buttons.find((button) => {
        const buttonRect = button.getBoundingClientRect();
        return buttonRect.left >= rect.right - Math.max(96, rect.width * 0.22);
      });

      if (rightSideButton) {
        score += 16;
      }

      if (score > bestScore) {
        best = parent;
        bestScore = score;
      }

      current = parent;
    }

    return bestScore >= 18 ? best : null;
  }

  async function clickGenerateButton() {
    const crashMessage = detectClientCrash();
    if (crashMessage) {
      throw new Error(crashMessage);
    }

    const promptInput = findPromptInput();
    const button = findGenerateButton();

    if (!(button instanceof HTMLElement)) {
      throw new Error("Không tìm thấy nút Generate.");
    }

    const composerRoot = findComposerRoot(promptInput);
    if (composerRoot instanceof HTMLElement && !composerRoot.contains(button)) {
      throw new Error("Nút Generate tìm thấy không nằm trong composer hiện tại.");
    }

    await clickGenerateActionButton(button);
    await wait(FLOW_TIMING.interactionDelayMs);
  }

  async function clickGenerateActionButton(button) {
    if (!(button instanceof HTMLElement)) {
      throw new Error("Nút Generate không hợp lệ.");
    }

    button.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });
    const rect = button.getBoundingClientRect();
    const clientX = rect.left + rect.width / 2;
    const clientY = rect.top + rect.height / 2;
    const topElement = document.elementFromPoint(clientX, clientY);
    if (topElement instanceof Element && !button.contains(topElement) && !topElement.contains(button)) {
      throw new Error("Tọa độ tâm của nút Generate hiện không trỏ đúng vào nút. Dừng để tránh click nhầm.");
    }

    button.focus?.();

    const response = await runtimeSendMessage({
      type: "FLOW_DEBUGGER_CLICK_AT",
      payload: { x: clientX, y: clientY }
    });

    if (response?.ok) {
      await wait(320);
      return;
    }

    button.click();
    await wait(320);
  }

  async function ensureSettingsPanelOpen() {
    if (hasVisibleSettingsPanel()) {
      return;
    }

    const trigger = findSettingsTrigger();
    if (!(trigger instanceof HTMLElement)) {
      return;
    }

    trigger.click();
    await waitForVisibleSettingsPanel(1800);
  }

  function hasVisibleSettingsPanel() {
    return Boolean(findSettingsPanel());
  }

  function findSettingsTrigger() {
    const buttons = Array.from(document.querySelectorAll("button, [role='button']"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreSettingsTrigger(element)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return buttons[0]?.score >= 20 ? buttons[0].element : null;
  }

  function scoreSettingsTrigger(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    const ariaLabel = normalizeText(element.getAttribute("aria-label"));
    let score = 0;

    if (
      text.includes("settings_2")
      || ariaLabel.includes("settings_2")
      || text.includes("xem chế độ cài đặt")
      || ariaLabel.includes("xem chế độ cài đặt")
    ) {
      score += 24;
    }

    if (text.includes("cài đặt") || ariaLabel.includes("cài đặt")) {
      score += 12;
    }

    if (rect.top < window.innerHeight * 0.22) {
      score += 10;
    }

    if (rect.left > window.innerWidth * 0.65) {
      score += 8;
    }

    if (rect.width >= 24 && rect.width <= 72 && rect.height >= 24 && rect.height <= 72) {
      score += 6;
    }

    if (text.includes("play_movies") || ariaLabel.includes("play_movies")) {
      score -= 30;
    }

    if (text.includes("trình tạo cảnh") || ariaLabel.includes("trình tạo cảnh")) {
      score -= 30;
    }

    return score;
  }

  async function waitForVisibleSettingsPanel(timeoutMs) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      if (hasVisibleSettingsPanel()) {
        return;
      }

      await wait(120);
    }
  }

  function findSettingsPanel() {
    const scopeSeeds = Array.from(
      document.querySelectorAll("button, [role='button'], [role='option'], [role='menuitem'], [role='dialog'], div, section")
    )
      .filter((element) => isVisible(element))
      .filter((element) => {
        const text = normalizeText(getElementText(element));
        return (
          text.includes("image")
          || text.includes("video")
          || text.includes("ngang")
          || text.includes("dọc")
          || text.includes("x1")
          || text.includes("x2")
          || text.includes("x3")
          || text.includes("x4")
          || text.includes("nano banana")
          || text.includes("imagen 4")
        );
      });

    let best = null;
    let bestScore = -Infinity;

    for (const seed of scopeSeeds) {
      const candidates = [seed, ...collectAncestorCandidates(seed, 4)];

      for (const candidate of candidates) {
        if (!(candidate instanceof HTMLElement) || candidate === document.body || candidate === document.documentElement) {
          continue;
        }

        const score = scoreSettingsPanel(candidate);
        if (score > bestScore) {
          best = candidate;
          bestScore = score;
        }
      }
    }

    return bestScore >= 30 ? best : null;
  }

  function collectAncestorCandidates(element, depthLimit) {
    const results = [];
    let current = element.parentElement;

    for (let depth = 0; current && depth < depthLimit; depth += 1) {
      results.push(current);
      current = current.parentElement;
    }

    return results;
  }

  function scoreSettingsPanel(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    const buttons = Array.from(element.querySelectorAll("button, [role='button'], [role='option'], [role='menuitem']"))
      .filter((child) => isVisible(child));
    let score = 0;

    if (rect.width >= 180 && rect.width <= 420) {
      score += 10;
    }

    if (rect.height >= 140 && rect.height <= 420) {
      score += 8;
    }

    if (rect.right > window.innerWidth * 0.45) {
      score += 6;
    }

    if (rect.bottom > window.innerHeight * 0.55) {
      score += 6;
    }

    if (buttons.length >= 6) {
      score += 12;
    }

    if (text.includes("image") && text.includes("video")) {
      score += 12;
    }

    if (text.includes("x1") && text.includes("x2") && text.includes("x4")) {
      score += 14;
    }

    if ((text.includes("nano banana") || text.includes("imagen 4")) && !text.includes("trình tạo cảnh")) {
      score += 14;
    }

    if (text.includes("play_movies") || text.includes("trình tạo cảnh")) {
      score -= 24;
    }

    return score;
  }

  async function waitForGenerationCompletion(beforeSnapshot, expectedNewCount = 1) {
    const knownUrls = new Set(beforeSnapshot.urls);
    const observedRoot = beforeSnapshot.galleryRoot || document.body;
    const baselineCount = beforeSnapshot.urls.length;

    return new Promise((resolve, reject) => {
      let settled = false;
      let observer;
      let lastMutationAt = Date.now();
      const startedAt = Date.now();
      let lastGrowthAt = Date.now();
      let previousNewCount = 0;
      let previousImageCount = baselineCount;
      let lastCountChangeAt = Date.now();
      let sawGenerationSignal = isGenerationInProgress();
      let readySince = null;

      const finish = (callback) => {
        if (settled) {
          return;
        }

        settled = true;
        if (observer) {
          observer.disconnect();
        }
        clearInterval(intervalId);
        callback();
      };

      observer = new MutationObserver(() => {
        lastMutationAt = Date.now();
      });

      observer.observe(observedRoot, {
        subtree: true,
        childList: true,
        attributes: true
      });

      const intervalId = window.setInterval(() => {
        if (runtimeState.stopRequested) {
          finish(() => reject(createStoppedError()));
          return;
        }

        const crashMessage = detectClientCrash();
        if (crashMessage) {
          finish(() => reject(new Error(crashMessage)));
          return;
        }

        const submissionError = detectSubmissionError();
        if (submissionError) {
          finish(() => reject(new Error(submissionError)));
          return;
        }

        const currentSnapshot = snapshotResultImages();
        const newUrls = currentSnapshot.urls.filter((url) => !knownUrls.has(url));
        const hasSettled = Date.now() - lastMutationAt >= FLOW_TIMING.settleTimeMs;
        const stillGenerating = isGenerationInProgress();
        const reachedExpectedCount = newUrls.length >= expectedNewCount;
        const currentImageCount = currentSnapshot.urls.length;

        if (stillGenerating || currentImageCount > baselineCount || newUrls.length > 0) {
          sawGenerationSignal = true;
        }

        if (newUrls.length > previousNewCount) {
          previousNewCount = newUrls.length;
          lastGrowthAt = Date.now();
        }

        if (currentImageCount !== previousImageCount) {
          previousImageCount = currentImageCount;
          lastCountChangeAt = Date.now();
        }

        if (!stillGenerating && sawGenerationSignal) {
          readySince = readySince || Date.now();
        } else {
          readySince = null;
        }

        const noGrowthLongEnough = Date.now() - lastGrowthAt >= FLOW_TIMING.noGrowthMs;
        const stableImageCountLongEnough = Date.now() - lastCountChangeAt >= FLOW_TIMING.stableCountMs;
        const minWaitElapsed = Date.now() - startedAt >= FLOW_TIMING.minimumGenerationMs;
        const readyLongEnough = readySince && Date.now() - readySince >= FLOW_TIMING.readyCooldownMs;

        if (reachedExpectedCount && hasSettled) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (newUrls.length > 0 && hasSettled && !stillGenerating) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (newUrls.length > 0 && noGrowthLongEnough) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (readyLongEnough && hasSettled) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (minWaitElapsed && stableImageCountLongEnough && !stillGenerating) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (minWaitElapsed && stableImageCountLongEnough) {
          finish(() => resolve(uniqueStrings(newUrls)));
          return;
        }

        if (Date.now() - startedAt >= FLOW_TIMING.generationTimeoutMs) {
          finish(() => {
            resolve(uniqueStrings(newUrls));
          });
        }
      }, FLOW_TIMING.pollIntervalMs);
    });
  }

  function detectSubmissionError() {
    const alertCandidates = Array.from(
      document.querySelectorAll('[role="alert"], [aria-live="assertive"], [data-sonner-toast], .toast, .Toastify__toast')
    ).filter((element) => isVisible(element));

    for (const element of alertCandidates) {
      const text = normalizeText(getElementText(element));
      if (!text) {
        continue;
      }

      const matched = FLOW_ERROR_TEXTS.find((token) => text.includes(token));
      if (matched) {
        return element.innerText?.trim() || text;
      }
    }

    return null;
  }

  function detectClientCrash() {
    const pageText = normalizeText(document.body.innerText || "");
    const matched = FLOW_APP_CRASH_TEXTS.find((token) => pageText.includes(token));
    return matched ? "Flow đã bị lỗi client-side sau khi extension thao tác vào editor. Batch đã dừng để tránh làm hỏng thêm trạng thái trang." : null;
  }

  function isPromptMissingError(message) {
    const normalized = normalizeText(message);
    return FLOW_ERROR_TEXTS.some((token) => normalized.includes(token));
  }

  function buildPromptSubmissionError(message) {
    const promptCandidates = describeElements(
      getPromptCandidates().slice(0, 5)
    );

    return [
      message,
      "",
      "Không đồng bộ được prompt vào state nội bộ của Flow sau 2 lần submit.",
      "Ứng viên prompt hiện tại:",
      promptCandidates || "- Không có ứng viên prompt nào."
    ].join("\n");
  }

  function isGenerationInProgress() {
    const loadingVisible = FLOW_HINTS.loadingIndicators.some((selector) => {
      try {
        const element = document.querySelector(selector);
        return Boolean(element && isVisible(element));
      } catch (error) {
        return false;
      }
    });

    const generateButton = findGenerateButton();
    const buttonDisabled = Boolean(
      generateButton
      && ((generateButton instanceof HTMLButtonElement && generateButton.disabled)
        || generateButton.getAttribute("aria-disabled") === "true")
    );

    const pageText = normalizeText(document.body.innerText || "");
    const textSignals = [
      "generating",
      "đang tạo",
      "creating",
      "rendering",
      "processing"
    ];
    const hasGeneratingText = textSignals.some((signal) => pageText.includes(signal));

    return loadingVisible || buttonDisabled || hasGeneratingText;
  }

  function snapshotResultImages() {
    const images = collectResultImages();
    const galleryRoot = findCommonGalleryRoot(images);
    return {
      urls: uniqueStrings(images.map((item) => item.url)),
      galleryRoot
    };
  }

  async function clearPromptComposer() {
    const candidates = getPromptCandidates();
    let clearedAny = false;

    for (const candidate of candidates) {
      try {
        const target = resolvePromptEditingTarget(candidate);
        if (!target) {
          continue;
        }

        clearedAny = true;
        const cleared = await clearPromptTarget(target);
        if (cleared) {
          await wait(80);
        }
      } catch (error) {
        console.warn("Không xóa được prompt hiện tại:", candidate, error);
      }
    }

    if (!clearedAny) {
      throw new Error("Không tìm thấy editor hợp lệ để xóa prompt hiện tại.");
    }

    if (!isComposerPromptCleared()) {
      throw new Error("Không thể xóa sạch prompt hiện tại khỏi composer của Flow.");
    }
  }

  async function clearPromptTarget(target) {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      await typePromptWithDebugger(target, "");
      await wait(180);

      const currentValue = normalizeText(readPromptValue(target));
      if (isPromptEffectivelyEmpty(currentValue)) {
        return true;
      }
    }

    return false;
  }

  async function forceClearPromptTarget(target) {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      await typePromptWithDebugger(target, "");
      dispatchPromptEvents(target, "");
      await wait(220);

      const currentValue = normalizeText(readPromptValue(target));
      if (isPromptEffectivelyEmpty(currentValue)) {
        return true;
      }
    }

    return false;
  }

  function isComposerPromptCleared() {
    const candidates = getPromptCandidates();
    for (const candidate of candidates) {
      try {
        const target = resolvePromptEditingTarget(candidate);
        if (!target) {
          continue;
        }

        const currentValue = normalizeText(readPromptValue(target));
        if (!isPromptEffectivelyEmpty(currentValue)) {
          return false;
        }
      } catch (error) {
        console.warn("Không kiểm tra được trạng thái prompt sau khi xóa:", candidate, error);
      }
    }

    return true;
  }

  function isPromptEffectivelyEmpty(currentValue) {
    return !currentValue
      || currentValue === "bạn muốn tạo gì?"
      || currentValue.includes("mô tả ý tưởng của bạn")
      || currentValue.includes("what do you want");
  }

  function collectResultImages() {
    const assets = [];
    const elements = [];

    for (const selector of FLOW_HINTS.resultImages) {
      try {
        elements.push(...document.querySelectorAll(selector));
      } catch (error) {
        console.warn("Selector ảnh lỗi:", selector, error);
      }
    }

    for (const element of uniqueElements(elements)) {
      const mapped = mapVisualAssetElement(element);
      if (mapped && isLikelyGeneratedVisual(mapped)) {
        assets.push(mapped);
      }
    }

    for (const mapped of collectBackgroundImageAssets()) {
      if (mapped && isLikelyGeneratedVisual(mapped)) {
        assets.push(mapped);
      }
    }

    return dedupeAssetCandidates(assets);
  }

  function collectSessionResultItems() {
    const images = collectResultImages();

    return images.map((item, index) => {
      const prompt = extractSessionPromptFromElement(item.element);
      return {
        id: `session-${normalizeSessionImageKey(item.url)}-${index + 1}`,
        prompt,
        promptLabel: `Ảnh session #${index + 1}`,
        imageUrl: item.url,
        selected: false,
        generatedAt: new Date().toISOString(),
        batchIndex: 0,
        imageIndex: index + 1,
        sourceType: item.kind || "session"
      };
    });
  }

  async function automateDownloadSelectedItemsFromFlow(items = []) {
    validatePageContext();

    const selectedItems = Array.isArray(items) ? items.filter(Boolean) : [];
    if (selectedItems.length === 0) {
      throw new Error("Chưa có ảnh nào được chọn để tải.");
    }

    let downloadedCount = 0;

    for (const item of selectedItems) {
      await triggerDirectDownloadForItem(item);
      downloadedCount += 1;
      await wait(650);
    }

    return {
      downloaded: downloadedCount > 0,
      downloadedCount,
      processedCount: downloadedCount
    };
  }

  async function triggerDirectDownloadForItem(item) {
    const target = findGalleryTargetForItem(item);
    if (!(target instanceof HTMLElement)) {
      throw new Error(`Không tìm thấy card ảnh trên Flow cho mục: ${item.promptLabel || item.prompt || item.imageUrl}`);
    }

    const cardRoot = findInteractiveCard(target) || findMediaCardRoot(target) || target;
    revealCardActionLayer(cardRoot);
    await wait(FLOW_TIMING.directDownloadActionDelayMs);

    const menuButton = await waitForElement(
      () => findCardMenuButton(cardRoot),
      4000,
      "Không tìm thấy nút Tạo thêm trên card ảnh đã chọn."
    );
    await clickElementRobustly(menuButton);
    await waitForElement(
      () => findOpenCardMenu(menuButton),
      4000,
      "Đã hover vào card nhưng chưa mở được menu Tạo thêm."
    );

    const downloadEntry = await waitForElement(
      () => findDirectDownloadMenuItem(),
      5000,
      "Không tìm thấy mục Tải xuống trong menu của card ảnh."
    );
    await hoverElementRobustly(downloadEntry);

    const qualityOption = await waitForElement(
      () => findDownloadQualityOption(downloadEntry),
      5000,
      "Đã mở menu Tải xuống nhưng chưa thấy đúng nút 2K Upscaled."
    );

    await clickExactMenuItem(qualityOption);
    await wait(FLOW_TIMING.directDownloadActionDelayMs);
  }

  function extractSessionPromptFromElement(element) {
    const cardRoot = findMediaCardRoot(element);
    const rawText = collectCardTexts(cardRoot || element)
      .join(" ")
      .replace(/more_vert|tạo thêm|gắn cờ cho đầu ra|đổi tên|cắt|sao chép|xóa|xoá|tải xuống|download|upscaled|original size/gi, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (rawText) {
      return rawText.slice(0, 220);
    }

    return "Ảnh đã có sẵn trong session Flow";
  }

  function collectCardTexts(element) {
    if (!(element instanceof HTMLElement)) {
      return [];
    }

    const texts = [];
    const altText = element.getAttribute("aria-label") || "";
    if (altText.trim()) {
      texts.push(altText.trim());
    }

    const descendants = [element, ...element.querySelectorAll("img, [aria-label], figcaption, span, div, p")];
    for (const node of descendants) {
      const text = (node.getAttribute?.("aria-label") || node.textContent || "").replace(/\s+/g, " ").trim();
      if (text && text.length >= 4 && text.length <= 180) {
        texts.push(text);
      }
    }

    return uniqueStrings(texts);
  }

  function findMediaCardRoot(element) {
    if (!(element instanceof HTMLElement)) {
      return null;
    }

    const candidates = [element, ...element.parents || []];
    let current = element;
    while (current) {
      candidates.push(current);
      current = current.parentElement;
    }

    const scored = uniqueElements(candidates)
      .filter((candidate) => candidate instanceof HTMLElement && isVisible(candidate))
      .map((candidate) => ({
        element: candidate,
        score: scoreMediaCardRoot(candidate)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return scored[0]?.element || element;
  }

  function scoreMediaCardRoot(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(element.innerText || element.textContent || "");
    let score = 0;

    if (rect.width >= 160 && rect.height >= 140) {
      score += 8;
    }

    if (element.querySelector("img")) {
      score += 10;
    }

    if (text.includes("tạo thêm") || text.includes("more_vert")) {
      score += 12;
    }

    if (text.includes("dog doin") || text.includes("corgi")) {
      score += 6;
    }

    if (element.querySelector("button, [role='button']")) {
      score += 6;
    }

    return score;
  }

  function findInteractiveCard(element) {
    if (!(element instanceof HTMLElement)) {
      return null;
    }

    return element.closest("button[aria-label*='Hình ảnh được tạo'], button[aria-label*='Generated image'], button, [role='button']");
  }

  function revealCardActionLayer(cardRoot) {
    if (!(cardRoot instanceof HTMLElement)) {
      return;
    }

    cardRoot.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });
    const targets = [cardRoot, cardRoot.querySelector("img")].filter(Boolean);
    const events = ["pointerenter", "mouseenter", "mouseover", "pointermove", "mousemove"];

    for (const target of targets) {
      for (const eventName of events) {
        target.dispatchEvent(new MouseEvent(eventName, { bubbles: true, cancelable: true, view: window }));
      }
    }
  }

  function findCardMenuButton(cardRoot) {
    const explicitMenuButtons = Array.from(
      cardRoot.querySelectorAll("button[aria-haspopup='menu'], [role='button'][aria-haspopup='menu']")
    )
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreCardMenuButton(element, cardRoot) + 20
      }))
      .sort((a, b) => b.score - a.score);

    if (explicitMenuButtons[0]?.score >= 20) {
      return explicitMenuButtons[0].element;
    }

    const buttons = Array.from(cardRoot.querySelectorAll("button, [role='button']"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreCardMenuButton(element, cardRoot)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return buttons[0]?.score >= 18 ? buttons[0].element : null;
  }

  function scoreCardMenuButton(element, cardRoot) {
    const rect = element.getBoundingClientRect();
    const cardRect = cardRoot.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    let score = 0;

    if (text.includes("tạo thêm") || text.includes("more_vert") || text.includes("more")) {
      score += 24;
    }

    if (element.getAttribute("aria-haspopup") === "menu") {
      score += 8;
    }

    if (rect.top <= cardRect.top + 80) {
      score += 8;
    }

    if (rect.left >= cardRect.left + cardRect.width * 0.72) {
      score += 12;
    }

    if (rect.width >= 24 && rect.width <= 60 && rect.height >= 24 && rect.height <= 60) {
      score += 6;
    }

    if (text.includes("yêu thích") || text.includes("favorite") || text.includes("like")) {
      score -= 14;
    }

    if (text.includes("sử dụng lại") || text.includes("redo") || text.includes("undo")) {
      score -= 14;
    }

    return score;
  }

  function findOpenCardMenu(menuButton) {
    const expandedId = menuButton?.getAttribute?.("aria-controls");
    if (expandedId) {
      const controlled = document.getElementById(expandedId);
      if (controlled && isVisible(controlled)) {
        return controlled;
      }
    }

    const menus = Array.from(document.querySelectorAll("[role='menu']"))
      .filter((element) => isVisible(element))
      .sort((a, b) => {
        const aRect = a.getBoundingClientRect();
        const bRect = b.getBoundingClientRect();
        return (bRect.width * bRect.height) - (aRect.width * aRect.height);
      });

    return menus[0] || null;
  }

  async function waitForOptionalElement(getter, timeoutMs) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      const element = getter();
      if (element) {
        return element;
      }

      await wait(120);
    }

    return null;
  }

  async function hoverElementRobustly(element) {
    if (!(element instanceof HTMLElement)) {
      throw new Error("Không hover được phần tử menu vì phần tử không hợp lệ.");
    }

    element.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });
    const rect = element.getBoundingClientRect();
    const clientX = rect.left + rect.width / 2;
    const clientY = rect.top + rect.height / 2;
    const mouseEventOptions = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX,
      clientY,
      button: 0
    };

    const sequence = ["pointerenter", "mouseenter", "mouseover", "pointermove", "mousemove"];
    element.focus?.();
    for (const eventName of sequence) {
      const EventCtor = eventName.startsWith("pointer") ? PointerEvent : MouseEvent;
      element.dispatchEvent(new EventCtor(eventName, mouseEventOptions));
    }

    try {
      await runtimeSendMessage({
        type: "FLOW_DEBUGGER_HOVER_AT",
        payload: { x: clientX, y: clientY }
      });
    } catch (error) {
      console.warn("Debugger hover fallback thất bại:", error);
    }

    await wait(FLOW_TIMING.directDownloadActionDelayMs);
  }

  async function clickExactMenuItem(element) {
    if (!(element instanceof HTMLElement)) {
      throw new Error("Không click được menuitem 2K vì phần tử không hợp lệ.");
    }

    const rect = element.getBoundingClientRect();
    const clientX = rect.left + rect.width / 2;
    const clientY = rect.top + rect.height / 2;

    try {
      await runtimeSendMessage({
        type: "FLOW_DEBUGGER_CLICK_AT",
        payload: { x: clientX, y: clientY }
      });
      await wait(FLOW_TIMING.directDownloadActionDelayMs);
      return;
    } catch (error) {
      console.warn("Debugger click chính xác cho menuitem 2K thất bại, chuyển sang fallback:", error);
    }

    const mouseEventOptions = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX,
      clientY,
      button: 0
    };

    for (const eventName of ["pointerdown", "mousedown", "pointerup", "mouseup", "click"]) {
      const EventCtor = eventName.startsWith("pointer") ? PointerEvent : MouseEvent;
      element.dispatchEvent(new EventCtor(eventName, mouseEventOptions));
    }

    element.click();
    await wait(FLOW_TIMING.directDownloadActionDelayMs);
  }

  async function clickElementRobustly(element) {
    if (!(element instanceof HTMLElement)) {
      throw new Error("Không click được phần tử menu vì phần tử không hợp lệ.");
    }

    element.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });
    const rect = element.getBoundingClientRect();
    const clientX = rect.left + rect.width / 2;
    const clientY = rect.top + rect.height / 2;
    const mouseEventOptions = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX,
      clientY,
      button: 0
    };

    const sequence = ["pointerdown", "mousedown", "pointerup", "mouseup", "click"];
    element.focus?.();
    for (const eventName of sequence) {
      const EventCtor = eventName.startsWith("pointer") ? PointerEvent : MouseEvent;
      element.dispatchEvent(new EventCtor(eventName, mouseEventOptions));
    }

      element.click();
      await wait(FLOW_TIMING.directDownloadActionDelayMs);

      if (element.getAttribute("aria-expanded") === "true") {
        return;
      }

    try {
        await runtimeSendMessage({
          type: "FLOW_DEBUGGER_CLICK_AT",
          payload: { x: clientX, y: clientY }
        });
        await wait(FLOW_TIMING.directDownloadActionDelayMs);
        if (element.getAttribute("aria-expanded") === "true") {
          return;
        }
    } catch (error) {
      console.warn("Debugger click fallback thất bại:", error);
    }

      element.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Enter" }));
      element.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Enter" }));
      await wait(FLOW_TIMING.directDownloadActionDelayMs);
    }

  function findDirectDownloadMenuItem() {
    const openMenu = findOpenCardMenu();
    const searchRoot = openMenu || document.body;
    const exactMenuItem = Array.from(searchRoot.querySelectorAll("[role='menuitem'], button, [role='button'], div[tabindex], li"))
      .filter((element) => isVisible(element))
      .find((element) => {
        const text = normalizeText(getElementText(element));
        return text.includes("tải xuống") || text.includes("download tải xuống") || text === "download";
      });

    if (exactMenuItem) {
      const text = normalizeText(getElementText(exactMenuItem));
      if (!text.includes("original size") && !text.includes("upscaled")) {
        return exactMenuItem;
      }
    }

    const direct = findActionButtonByLabels(["tải xuống", "download tải xuống", "download"], searchRoot);
    if (direct) {
      const text = normalizeText(getElementText(direct));
      if (!text.includes("original size") && !text.includes("upscaled")) {
        return direct;
      }
    }

    const candidates = Array.from(searchRoot.querySelectorAll("button, [role='menuitem'], [role='button'], div[tabindex], li"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreDirectDownloadMenuItem(element)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return candidates[0]?.score >= 14 ? candidates[0].element : null;
  }

  function scoreDirectDownloadMenuItem(element) {
    const text = normalizeText(getElementText(element));
    const rect = element.getBoundingClientRect();
    let score = 0;

    if (text.includes("tải xuống") || text.includes("download")) {
      score += 26;
    }

    if (text.includes("đổi tên") || text.includes("cắt") || text.includes("sao chép") || text.includes("xóa") || text.includes("xoá")) {
      score -= 20;
    }

    if (text.includes("original size") || text.includes("upscaled") || text === "1k" || text === "2k" || text === "4k") {
      score -= 18;
    }

    if (rect.width >= 70 && rect.height >= 28) {
      score += 4;
    }

    return score;
  }

  function findDownloadQualityOption(downloadEntry) {
    const downloadRect = downloadEntry instanceof HTMLElement ? downloadEntry.getBoundingClientRect() : null;
    const visibleMenuItems = Array.from(document.body.querySelectorAll("button[role='menuitem'], [role='menuitem']"))
      .filter((element) => isVisible(element))
      .filter((element) => element.getAttribute("aria-disabled") !== "true")
      .filter((element) => {
        const orientation = element.getAttribute("data-orientation") || "";
        return !orientation || orientation === "vertical";
      })
      .filter((element) => {
        const hasRadixMarker = element.hasAttribute("data-radix-collection-item");
        return hasRadixMarker || element.getAttribute("role") === "menuitem";
      });

    const buttonBySpan2k = findQualityButtonParentBySpan(downloadRect, "2k");
    if (buttonBySpan2k) {
      return buttonBySpan2k;
    }

    const groupedMiddleButton = findMiddleQualityButtonFromTriplet(visibleMenuItems, downloadRect);
    if (groupedMiddleButton) {
      return groupedMiddleButton;
    }

    const exactCandidates = visibleMenuItems.filter((element) => {
      const text = normalizeText(getElementText(element));
      return text.includes("2k upscaled") || text === "2k";
    });

    if (exactCandidates.length > 0) {
      return exactCandidates.sort((a, b) => {
        const aRect = a.getBoundingClientRect();
        const bRect = b.getBoundingClientRect();
        const aScore = scoreDownloadQualityOption(a, aRect, downloadRect);
        const bScore = scoreDownloadQualityOption(b, bRect, downloadRect);
        return bScore - aScore;
      })[0];
    }

    return null;
  }

  function findQualityButtonParentBySpan(downloadRect, needle) {
    const spanEntries = Array.from(document.body.querySelectorAll("[role='menu'] span"))
      .map((span) => ({
        span,
        text: normalizeText(span.textContent || ""),
        button: span.closest("button[role='menuitem'], [role='menuitem']")
      }))
      .filter((entry) => entry.button instanceof HTMLElement)
      .filter((entry) => isVisible(entry.button))
      .filter((entry) => entry.button.getAttribute("aria-disabled") !== "true")
      .filter((entry) => entry.text === needle || entry.text.includes(needle));

    if (spanEntries.length === 0) {
      return null;
    }

    const filtered = spanEntries.filter((entry) => {
      const menu = entry.button.closest?.("[role='menu']");
      if (!(menu instanceof HTMLElement) || !downloadRect) {
        return true;
      }

      const menuRect = menu.getBoundingClientRect();
      return menuRect.left < downloadRect.left && Math.abs(menuRect.top - downloadRect.top) < 220;
    });

    const ranked = (filtered.length > 0 ? filtered : spanEntries).sort((a, b) => {
      const aRect = a.button.getBoundingClientRect();
      const bRect = b.button.getBoundingClientRect();
      const aScore = scoreDownloadQualityOption(a.button, aRect, downloadRect);
      const bScore = scoreDownloadQualityOption(b.button, bRect, downloadRect);
      return bScore - aScore;
    });

    return ranked[0]?.button || null;
  }

  function findMiddleQualityButtonFromTriplet(menuItems, downloadRect) {
    const candidates = menuItems
      .map((element) => {
        const spans = Array.from(element.querySelectorAll("span")).map((span) => normalizeText(span.textContent || ""));
        const text = normalizeText(getElementText(element));
        const qualityToken = spans.find((value) => value === "1k" || value === "2k" || value === "4k")
          || (text.includes("1k") ? "1k" : text.includes("2k") ? "2k" : text.includes("4k") ? "4k" : "");

        return {
          element,
          text,
          qualityToken,
          rect: element.getBoundingClientRect(),
          menu: element.closest?.("[role='menu']")
        };
      })
      .filter((entry) => entry.menu instanceof HTMLElement)
      .filter((entry) => {
        if (!downloadRect) {
          return true;
        }

        const menuRect = entry.menu.getBoundingClientRect();
        return menuRect.left < downloadRect.left && Math.abs(menuRect.top - downloadRect.top) < 220;
      });

    const groupedByMenu = new Map();
    for (const entry of candidates) {
      const group = groupedByMenu.get(entry.menu) || [];
      group.push(entry);
      groupedByMenu.set(entry.menu, group);
    }

    for (const entries of groupedByMenu.values()) {
      const has1k = entries.some((entry) => entry.text.includes("1k"));
      const has2k = entries.some((entry) => entry.text.includes("2k"));
      const has4k = entries.some((entry) => entry.text.includes("4k"));
      if (!has1k || !has2k || !has4k) {
        continue;
      }

      const ordered = entries
        .filter((entry) => entry.qualityToken === "1k" || entry.qualityToken === "2k" || entry.qualityToken === "4k")
        .sort((a, b) => a.rect.top - b.rect.top);

      if (ordered.length < 3) {
        continue;
      }

      const triplet = ordered.slice(0, 3);
      const topText = triplet[0].qualityToken;
      const middleText = triplet[1].qualityToken;
      const bottomText = triplet[2].qualityToken;

      if (topText === "1k" && middleText === "2k" && bottomText === "4k") {
        return triplet[1].element;
      }
    }

    return null;
  }

  function scoreDownloadQualityOption(element, rect, downloadRect) {
    let score = 0;
    const text = normalizeText(getElementText(element));
    const menu = element.closest?.("[role='menu']");

    if (text.includes("2k upscaled")) {
      score += 60;
    } else if (text === "2k") {
      score += 25;
    }

    if (element.getAttribute("tabindex") === "0") {
      score += 18;
    }

    if (element.hasAttribute("data-radix-collection-item")) {
      score += 15;
    }

    if (menu instanceof HTMLElement) {
      if (menu.getAttribute("data-side") === "left") {
        score += 16;
      }

      if (menu.getAttribute("data-state") === "open") {
        score += 12;
      }
    }

    if (downloadRect) {
      const verticalDistance = Math.abs((rect.top + rect.height / 2) - (downloadRect.top + downloadRect.height / 2));
      score += Math.max(0, 20 - Math.min(20, verticalDistance / 6));

      if (rect.right <= downloadRect.left + 40) {
        score += 20;
      }

      if (rect.left < downloadRect.left) {
        score += 8;
      }
    }

    score += Math.min(20, (rect.width * rect.height) / 600);
    return score;
  }

  function findGalleryTargetForItem(item) {
    const targetUrl = normalizeAssetUrl(item?.imageUrl);
    const targetTokens = buildPromptMatchTokens(item?.prompt);
    const assets = collectResultImages();

    const directAsset = assets.find((asset) => {
      const assetUrl = normalizeAssetUrl(asset?.url);
      return Boolean(targetUrl && assetUrl && assetUrl === targetUrl);
    });

    if (directAsset?.element instanceof HTMLElement) {
      return findClickableMediaCard(directAsset.element);
    }

    const promptCard = findCardByPromptTokens(targetTokens);
    if (promptCard) {
      return promptCard;
    }

    return null;
  }

  function findCardByPromptTokens(tokens) {
    if (!tokens.length) {
      return null;
    }

    const candidates = Array.from(document.querySelectorAll("article, section, div, button, a"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        text: normalizeText(element.innerText || element.textContent || "")
      }))
      .filter((entry) => entry.text)
      .map((entry) => ({
        element: entry.element,
        score: tokens.filter((token) => entry.text.includes(token)).length
      }))
      .filter((entry) => entry.score >= Math.min(2, tokens.length))
      .sort((a, b) => b.score - a.score);

    return candidates[0] ? findClickableMediaCard(candidates[0].element) : null;
  }

  function buildPromptMatchTokens(prompt) {
    return normalizeText(prompt)
      .split(" ")
      .filter((word) => word.length >= 4)
      .slice(0, 10);
  }

  function findClickableMediaCard(element) {
    const clickable = element.closest("button, a, [role='button'], article, section, div");
    if (!(clickable instanceof HTMLElement)) {
      return element instanceof HTMLElement ? element : null;
    }

    return clickable;
  }
  function mapVisualAssetElement(element) {
    if (element instanceof HTMLImageElement) {
      const url = pickFirstValidUrl([
        element.currentSrc,
        element.src,
        element.getAttribute("src"),
        extractUrlFromSrcset(element.srcset),
        extractUrlFromSrcset(element.getAttribute("srcset"))
      ]);

      if (!url) {
        return null;
      }

      return { element, url, kind: "img" };
    }

    if (element instanceof HTMLVideoElement) {
      const url = pickFirstValidUrl([
        element.poster,
        element.getAttribute("poster"),
        element.currentSrc,
        element.src
      ]);

      if (!url) {
        return null;
      }

      return { element, url, kind: "video-poster" };
    }

    if (element instanceof HTMLCanvasElement) {
      const url = extractCanvasDataUrl(element);
      if (!url) {
        return null;
      }

      return { element, url, kind: "canvas" };
    }

    return null;
  }

  function isLikelyGeneratedVisual(item) {
    const element = item?.element;
    if (!(element instanceof Element)) {
      return false;
    }

    const rect = element.getBoundingClientRect();
    const src = String(item?.url || "");
    const alt = normalizeText(element.getAttribute?.("alt") || "");
    const text = normalizeText(getElementText(element));
    const naturalWidth = Number(element.naturalWidth || element.videoWidth || element.width || 0);
    const naturalHeight = Number(element.naturalHeight || element.videoHeight || element.height || 0);
    const visibleEnough = isVisible(element);
    const sizeLooksReal =
      rect.width >= 72
      || rect.height >= 72
      || naturalWidth >= 128
      || naturalHeight >= 128;
    const livesInMediaArea = Boolean(
      element.closest("main, article, section, [role='dialog'], [aria-modal='true']")
    );
    const insideControl = Boolean(element.closest("button, nav, header, [role='button']"));

    if (!visibleEnough && !sizeLooksReal) {
      return false;
    }

    if (!sizeLooksReal) {
      return false;
    }

    if ((rect.width > 0 && rect.height > 0 && rect.width * rect.height < 5000)
      && naturalWidth < 128
      && naturalHeight < 128) {
      return false;
    }

    if (alt.includes("avatar") || alt.includes("icon") || alt.includes("logo")) {
      return false;
    }

    if (alt.includes("hình ảnh được tạo") || alt.includes("generated image")) {
      return true;
    }

    if (text.includes("google logo") || text.includes("instagram logo") || text.includes("discord logo")) {
      return false;
    }

    if (insideControl && !livesInMediaArea) {
      return false;
    }

    if (src.startsWith("data:")) {
      return src.startsWith("data:image/");
    }

    return /^https?:|^blob:/i.test(src);
  }

  function findCommonGalleryRoot(items) {
    if (!items.length) {
      return document.body;
    }

    const roots = items
      .map((item) => item.element.closest("main, section, div"))
      .filter(Boolean);

    return roots[0] || document.body;
  }

  function collectBackgroundImageAssets() {
    const assets = [];
    const candidates = Array.from(document.querySelectorAll("div, article, section, button, a, span"))
      .filter((element) => isVisible(element));

    for (const element of candidates) {
      const rect = element.getBoundingClientRect();
      if (rect.width < 80 || rect.height < 80 || rect.width * rect.height < 10000) {
        continue;
      }

      const style = window.getComputedStyle(element);
      const rawBackground = style.backgroundImage || element.style?.backgroundImage || "";
      const url = extractUrlFromCssImage(rawBackground);
      if (!url) {
        continue;
      }

      assets.push({
        element,
        url,
        kind: "background-image"
      });
    }

    return assets;
  }

  function extractCanvasDataUrl(canvas) {
    try {
      if (!(canvas instanceof HTMLCanvasElement)) {
        return null;
      }

      if (canvas.width < 32 || canvas.height < 32) {
        return null;
      }

      return canvas.toDataURL("image/png");
    } catch (error) {
      return null;
    }
  }

  function extractUrlFromSrcset(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return null;
    }

    const firstCandidate = raw.split(",")[0]?.trim();
    if (!firstCandidate) {
      return null;
    }

    return normalizeAssetUrl(firstCandidate.split(/\s+/)[0]);
  }

  function extractUrlFromCssImage(value) {
    const raw = String(value || "").trim();
    if (!raw || raw === "none") {
      return null;
    }

    const directMatch = raw.match(/url\((['"]?)(.*?)\1\)/i);
    if (directMatch?.[2]) {
      return normalizeAssetUrl(directMatch[2]);
    }

    const imageSetMatch = raw.match(/image-set\((.+)\)/i);
    if (!imageSetMatch?.[1]) {
      return null;
    }

    const nestedMatch = imageSetMatch[1].match(/url\((['"]?)(.*?)\1\)/i);
    return nestedMatch?.[2] ? normalizeAssetUrl(nestedMatch[2]) : null;
  }

  function normalizeAssetUrl(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return null;
    }

    if (/^data:image\//i.test(raw) || /^blob:/i.test(raw) || /^https?:/i.test(raw)) {
      return raw;
    }

    try {
      return new URL(raw, window.location.href).href;
    } catch (error) {
      return null;
    }
  }

  function pickFirstValidUrl(values) {
    for (const value of values) {
      const normalized = normalizeAssetUrl(value);
      if (normalized) {
        return normalized;
      }
    }

    return null;
  }

  function dedupeAssetCandidates(items) {
    const seen = new Set();
    const deduped = [];

    for (const item of items) {
      const key = String(item?.url || "").trim();
      if (!key || seen.has(key)) {
        continue;
      }

      seen.add(key);
      deduped.push(item);
    }

    return deduped;
  }

  function buildImageDiagnostics() {
    const imgCount = document.querySelectorAll("img").length;
    const videoPosterCount = document.querySelectorAll("video[poster]").length;
    const canvasCount = document.querySelectorAll("canvas").length;
    const backgroundCandidateCount = Array.from(document.querySelectorAll("div, article, section, button, a, span"))
      .filter((element) => {
        if (!(element instanceof HTMLElement) || !isVisible(element)) {
          return false;
        }

        const style = window.getComputedStyle(element);
        return Boolean(extractUrlFromCssImage(style.backgroundImage || ""));
      }).length;

    const sampleImages = Array.from(document.querySelectorAll("img"))
      .slice(0, 8)
      .map((element, index) => {
        const rect = element.getBoundingClientRect();
        const mapped = mapVisualAssetElement(element);
        return {
          index: index + 1,
          visible: isVisible(element),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          naturalWidth: Number(element.naturalWidth || 0),
          naturalHeight: Number(element.naturalHeight || 0),
          src: String(mapped?.url || element.currentSrc || element.src || "").slice(0, 160),
          alt: String(element.alt || "").slice(0, 80),
          accepted: Boolean(mapped && isLikelyGeneratedVisual(mapped))
        };
      });

    return {
      imgCount,
      videoPosterCount,
      canvasCount,
      backgroundCandidateCount,
      collectedCount: collectResultImages().length,
      sampleImages
    };
  }

  function findCurrentOpenedImage() {
    const candidates = Array.from(document.querySelectorAll("img"))
      .filter((element) => {
        if (!(element instanceof HTMLImageElement)) {
          return false;
        }

        const rect = element.getBoundingClientRect();
        const alt = normalizeText(element.alt || "");
        return isVisible(element)
          && rect.width >= 110
          && rect.height >= 90
          && rect.width * rect.height >= 12000
          && rect.left >= 12
          && rect.top >= 70
          && rect.left < window.innerWidth * 0.35
          && (alt.includes("hình ảnh được tạo") || alt.includes("generated image") || alt.includes("corgi") || Boolean(element.currentSrc || element.src));
      })
      .sort((a, b) => {
        const aRect = a.getBoundingClientRect();
        const bRect = b.getBoundingClientRect();
        return (bRect.width * bRect.height) - (aRect.width * aRect.height);
      });

    return candidates[0] || null;
  }

  function isViewerOpen() {
    if (findActionButtonByLabels(["tải xuống", "download", "xong", "done"], document.body)) {
      return true;
    }

    const topButtons = Array.from(document.querySelectorAll("button, [role='button']"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        rect: element.getBoundingClientRect(),
        text: normalizeText(getElementText(element))
      }))
      .filter((entry) => entry.rect.top >= 0 && entry.rect.top < 96 && entry.rect.width >= 24 && entry.rect.height >= 24);

    const leftToolbarButtons = topButtons.filter((entry) => entry.rect.left < window.innerWidth * 0.35);
    const rightToolbarButtons = topButtons.filter((entry) => entry.rect.left > window.innerWidth * 0.45);
    const largeViewerImage = findCurrentOpenedImage();

    return Boolean(
      largeViewerImage
      && leftToolbarButtons.length >= 1
      && rightToolbarButtons.length >= 2
    );
  }

  function findCropToolButton() {
    const explicit = findActionButtonByLabels(
      ["crop cắt", "crop", "crop square", "crop_square", "cắt xén", "cắt"],
      document.body
    );
    if (explicit) {
      return explicit;
    }

    const viewerImage = findCurrentOpenedImage();
    const baseScope = viewerImage?.closest("main, [role='dialog'], body") || document.body;
    const candidates = Array.from(baseScope.querySelectorAll("button, [role='button']"))
      .filter((element) => isVisible(element))
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        return rect.left < window.innerWidth * 0.18 && rect.top > 40 && rect.height >= 28 && rect.width >= 28;
      })
      .map((element) => ({
        element,
        score: scoreCropToolButton(element, viewerImage)
      }))
      .sort((a, b) => b.score - a.score);

    return candidates[0]?.score >= 12 ? candidates[0].element : null;
  }

  function findSquareCropOption() {
    const explicit = findActionButtonByLabels([
      "vuông (1:1)",
      "crop_square vuông (1:1)",
      "crop_square",
      "square (1:1)",
      "1:1",
      "vuông"
    ], document.body);
    if (explicit) {
      return explicit;
    }

    const candidates = Array.from(document.querySelectorAll("[role='menuitem'], [role='option'], button, li, div[tabindex]"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreSquareCropOption(element)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return candidates[0]?.score >= 14 ? candidates[0].element : null;
  }

  function scoreCropToolButton(element, viewerImage) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    const ariaLabel = normalizeText(element.getAttribute?.("aria-label"));
    const viewerRect = viewerImage?.getBoundingClientRect();
    let score = 0;

    if (
      text.includes("crop cắt")
      || text.includes("crop")
      || text.includes("crop_square")
      || text.includes("cắt xén")
      || ariaLabel.includes("crop cắt")
      || ariaLabel.includes("crop")
    ) {
      score += 22;
    }

    if (text === "cắt" || ariaLabel.includes("cắt")) {
      score += 16;
    }

    if (rect.width >= 28 && rect.width <= 72 && rect.height >= 28 && rect.height <= 72) {
      score += 8;
    }

    if (rect.top > 60 && rect.top < 180) {
      score += 10;
    }

    if (rect.left > window.innerWidth * 0.18 && rect.left < window.innerWidth * 0.55) {
      score += 12;
    }

    if (viewerRect) {
      const horizontalGap = Math.abs(rect.left - viewerRect.left);
      score += Math.max(0, 8 - horizontalGap / 50);
    }

    if (text.includes("download") || ariaLabel.includes("download")) {
      score -= 18;
    }

    if (text.includes("check") || ariaLabel.includes("check") || text.includes("xong")) {
      score -= 18;
    }

    return score;
  }

  function scoreSquareCropOption(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    let score = 0;

    if (text.includes("vuông")) {
      score += 12;
    }

    if (text.includes("1:1")) {
      score += 12;
    }

    if (text.includes("crop_square") || text.includes("square")) {
      score += 10;
    }

    if (text.includes("khổ")) {
      score += 4;
    }

    if (rect.left < window.innerWidth * 0.3) {
      score += 6;
    }

    if (rect.top > window.innerHeight * 0.2 && rect.top < window.innerHeight * 0.75) {
      score += 4;
    }

    return score;
  }

  function findCheckButton() {
    const explicit = findActionButtonByLabels(["check", "xong", "done"], document.body);
    if (explicit) {
      return explicit;
    }

    const candidates = Array.from(document.querySelectorAll("button, [role='button']"))
      .filter((element) => isVisible(element))
      .map((element) => ({
        element,
        score: scoreCheckButton(element)
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    return candidates[0]?.score >= 16 ? candidates[0].element : null;
  }

  function scoreCheckButton(element) {
    const rect = element.getBoundingClientRect();
    const text = normalizeText(getElementText(element));
    const ariaLabel = normalizeText(element.getAttribute?.("aria-label"));
    let score = 0;

    if (text.includes("check") || ariaLabel.includes("check")) {
      score += 18;
    }

    if (text.includes("xong") || ariaLabel.includes("xong") || text.includes("done") || ariaLabel.includes("done")) {
      score += 14;
    }

    if (rect.top < window.innerHeight * 0.2) {
      score += 10;
    }

    if (rect.left > window.innerWidth * 0.78) {
      score += 10;
    }

    if (rect.width >= 28 && rect.width <= 64 && rect.height >= 28 && rect.height <= 64) {
      score += 6;
    }

    if (text.includes("download") || ariaLabel.includes("download")) {
      score -= 12;
    }

    return score;
  }

  function findActionButtonByLabels(labels, scopeRoot = document.body) {
    const normalizedLabels = labels.map(normalizeText).filter(Boolean);
    const clickables = Array.from(
      scopeRoot.querySelectorAll("button, [role='button'], [role='menuitem'], [role='option'], div[tabindex], li")
    ).filter((element) => isVisible(element));

    return clickables.find((element) => {
      const text = normalizeText(getElementText(element));
      const ariaLabel = normalizeText(element.getAttribute?.("aria-label"));
      return normalizedLabels.some((label) => text.includes(label) || ariaLabel.includes(label));
    }) || null;
  }

  async function waitForElement(getter, timeoutMs, errorMessage) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      const element = getter();
      if (element) {
        return element;
      }

      await wait(180);
    }

    throw new Error(errorMessage);
  }

  function findControlTrigger(selectorCandidates, textPatterns, targetTexts, scopeRoot = document.body) {
    const direct = findFirstVisibleWithin(selectorCandidates, scopeRoot);
    if (direct) {
      return direct;
    }

    const buttons = Array.from(scopeRoot.querySelectorAll("button, [role='button'], div[tabindex], span[tabindex]"))
      .filter((element) => isVisible(element));

    return buttons.find((element) => {
      const text = normalizeText(getElementText(element));
      if (!text) {
        return false;
      }

      const matchesPattern = textPatterns.some((pattern) => text.includes(normalizeText(pattern)));
      const matchesTarget = targetTexts.some((target) => text.includes(target));
      return matchesPattern || matchesTarget;
    }) || null;
  }

  function findClickableByExactText(texts, scopeRoot = document.body) {
    const normalizedTargets = texts.map(normalizeText).filter(Boolean);
    if (normalizedTargets.length === 0) {
      return null;
    }

    const clickables = Array.from(
      scopeRoot.querySelectorAll("button, [role='button'], [role='option'], li, div[tabindex], span[tabindex]")
    ).filter((element) => isVisible(element));

    return clickables.find((element) => {
      const text = normalizeText(getElementText(element));
      return normalizedTargets.includes(text);
    }) || null;
  }

  function findVisibleOptionByText(texts, scopeRoot = document.body) {
    const normalizedTargets = texts.map(normalizeText).filter(Boolean);
    const candidates = Array.from(
      scopeRoot.querySelectorAll(
        '[role="option"], [role="menuitem"], [role="listbox"] * , [data-value], li, button, div, span'
      )
    );

    return candidates.find((candidate) => {
      if (!(candidate instanceof HTMLElement) || !isVisible(candidate)) {
        return false;
      }

      const text = normalizeText(getElementText(candidate));
      return normalizedTargets.includes(text) || normalizedTargets.some((target) => text.includes(target));
    }) || null;
  }

  function dismissOverlay() {
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  }

  function setNativeInputValue(element, value) {
    const prototype = Object.getPrototypeOf(element);
    const valueSetter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;

    if (valueSetter) {
      valueSetter.call(element, value);
    } else {
      element.value = value;
    }

    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function getElementText(element) {
    return (
      element.getAttribute?.("aria-label")
      || element.getAttribute?.("placeholder")
      || element.getAttribute?.("title")
      || element.textContent
      || element.innerText
      || element.value
      || ""
    );
  }

  function readPromptValue(element) {
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      return element.value || "";
    }

    return element.textContent || element.innerText || "";
  }

  function promptLooksApplied(currentValue, prompt) {
    const current = normalizeText(currentValue);
    const target = normalizeText(prompt);

    if (!current || current === "bạn muốn tạo gì?" || current.includes("mô tả ý tưởng của bạn")) {
      return false;
    }

    if (current.includes(target.slice(0, Math.min(target.length, 48)))) {
      return true;
    }

    const promptWords = target.split(" ").filter((word) => word.length > 3).slice(0, 6);
    const matchedWords = promptWords.filter((word) => current.includes(word)).length;
    return matchedWords >= Math.min(3, promptWords.length);
  }

  function isPromptLikeElement(element) {
    if (!(element instanceof HTMLElement)) {
      return false;
    }

    return element.matches("input, textarea, [contenteditable='true'], [role='textbox']");
  }

  function dispatchPromptEvents(element, value) {
    element.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    element.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true, data: "" }));
    element.dispatchEvent(new InputEvent("beforeinput", { bubbles: true, data: value, inputType: "insertText" }));
    element.dispatchEvent(new InputEvent("input", { bubbles: true, data: value, inputType: "insertText" }));
    element.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true, data: value }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    element.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "a" }));
    element.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "a" }));
    element.dispatchEvent(new FocusEvent("blur", { bubbles: true }));
  }

  function elementTextMatches(element, normalizedTargets) {
    const text = normalizeText(getElementText(element));
    return normalizedTargets.some((target) => text.includes(target));
  }

  function findFirstVisible(selectors) {
    return findVisibleElements(selectors)[0] || null;
  }

  function findFirstVisibleWithin(selectors, scopeRoot) {
    return findVisibleElementsWithin(selectors, scopeRoot)[0] || null;
  }

  function findVisibleElements(selectors) {
    return findVisibleElementsWithin(selectors, document);
  }

  function findVisibleElementsWithin(selectors, scopeRoot) {
    const found = [];
    const queryRoot = scopeRoot || document;

    for (const selector of selectors) {
      try {
        for (const element of queryRoot.querySelectorAll(selector)) {
          if (isVisible(element)) {
            found.push(element);
          }
        }
      } catch (error) {
        console.warn("Selector lỗi:", selector, error);
      }
    }

    return uniqueElements(found);
  }

  function isVisible(element) {
    if (!(element instanceof Element)) {
      return false;
    }

    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);

    return rect.width > 0
      && rect.height > 0
      && style.visibility !== "hidden"
      && style.display !== "none"
      && style.opacity !== "0";
  }

  async function updateBatchState(partialState) {
    const current = await getStoredState();
    const nextState = {
      ...current,
      ...partialState
    };

    await storageSet({
      [STORAGE_KEYS.state]: nextState
    });
  }

  async function getStoredState() {
    const stored = await storageGet(STORAGE_KEYS.state);
    return stored[STORAGE_KEYS.state] || {
      status: "idle",
      totalPrompts: 0,
      currentPromptIndex: 0,
      currentPrompt: "",
      lastError: "",
      startedAt: null,
      completedAt: null,
      activeTabId: null
    };
  }

  async function getStoredResults() {
    const stored = await storageGet(STORAGE_KEYS.results);
    return Array.isArray(stored[STORAGE_KEYS.results]) ? stored[STORAGE_KEYS.results] : [];
  }

  function dedupeResults(items) {
    const seen = new Set();
    const deduped = [];

    for (const item of items) {
      const key = String(item.imageUrl || "").trim();
      if (seen.has(key)) {
        continue;
      }

      seen.add(key);
      deduped.push(item);
    }

    return deduped;
  }

  function createResultId(batchIndex, imageIndex) {
    const time = Date.now();
    const random = Math.random().toString(36).slice(2, 8);
    return `flow-${batchIndex}-${imageIndex}-${time}-${random}`;
  }

  function mergeByUrl(existingItems, nextItems) {
    return [...(Array.isArray(existingItems) ? existingItems : []), ...(Array.isArray(nextItems) ? nextItems : [])];
  }

  function normalizeSessionImageKey(value) {
    return String(value || "")
      .replace(/[^a-z0-9]+/gi, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48) || Math.random().toString(36).slice(2, 10);
  }

  function uniqueStrings(values) {
    return Array.from(new Set(values));
  }

  function uniqueElements(values) {
    return Array.from(new Set(values));
  }

  function describeElements(elements) {
    return elements
      .map((element, index) => {
        const label = element.getAttribute?.("aria-label") || "";
        const placeholder = element.getAttribute?.("placeholder") || "";
        const title = element.getAttribute?.("title") || "";
        const text = getElementText(element).slice(0, 80);
        const tag = element.tagName.toLowerCase();
        const id = element.id ? `#${element.id}` : "";
        const className = typeof element.className === "string" && element.className.trim()
          ? `.${element.className.trim().replace(/\s+/g, ".").slice(0, 60)}`
          : "";

        return `${index + 1}. ${tag}${id}${className} | aria="${label}" | placeholder="${placeholder}" | title="${title}" | text="${text}"`;
      })
      .join("\n");
  }

  function normalizeText(value) {
    return String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
  }

  function buildGenerationTypeAliases(value) {
    const normalized = String(value || "").trim().toLowerCase();
    const aliasMap = {
      image: ["Ảnh", "Hình ảnh"],
      video: ["Phim", "Clip"]
    };

    return aliasMap[normalized] || [];
  }

  function buildOrientationAliases(value) {
    const normalized = String(value || "").trim().toLowerCase();
    const aliasMap = {
      ngang: ["Landscape", "Horizontal"],
      dọc: ["Portrait", "Vertical"]
    };

    return aliasMap[normalized] || [];
  }

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function throwIfStopRequested() {
    if (runtimeState.stopRequested) {
      throw createStoppedError();
    }
  }

  function createStoppedError() {
    const error = new Error("BATCH_STOPPED");
    error.code = "BATCH_STOPPED";
    return error;
  }

  function isStoppedError(error) {
    return error?.code === "BATCH_STOPPED" || error?.message === "BATCH_STOPPED";
  }

  function storageGet(keys) {
    return chrome.storage.local.get(keys);
  }

  function storageSet(values) {
    return chrome.storage.local.set(values);
  }

  function runtimeSendMessage(message) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        const lastError = chrome.runtime.lastError;
        if (lastError) {
          reject(new Error(lastError.message));
          return;
        }

        resolve(response);
      });
    });
  }
})();


















