(function initDownloadStrategy(globalScope) {
  function isDirectDownloadableUrl(url) {
    const value = String(url || "").trim().toLowerCase();
    return value.startsWith("https://") || value.startsWith("http://") || value.startsWith("data:");
  }

  function splitDownloadItems(items) {
    const directItems = [];
    const fallbackItems = [];

    for (const item of Array.isArray(items) ? items : []) {
      if (isDirectDownloadableUrl(item?.imageUrl)) {
        directItems.push(item);
      } else {
        fallbackItems.push(item);
      }
    }

    return { directItems, fallbackItems };
  }

  function normalizeDownloadQuality(value) {
    const normalized = String(value || "").trim().toLowerCase();
    return normalized === "1k" ? "1k" : "2k";
  }

  function normalizeDownloadMethod(value) {
    const normalized = String(value || "").trim().toLowerCase();
    return normalized === "flow-menu" ? "flow-menu" : "direct-url";
  }

  function normalizeDirectFormat(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized === "png" || normalized === "webp") {
      return normalized;
    }

    return "jpg";
  }

  const exported = {
    isDirectDownloadableUrl,
    normalizeDirectFormat,
    normalizeDownloadMethod,
    normalizeDownloadQuality,
    splitDownloadItems
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = exported;
  }

  globalScope.FlowBatchDownloadStrategy = exported;
})(typeof globalThis !== "undefined" ? globalThis : window);
