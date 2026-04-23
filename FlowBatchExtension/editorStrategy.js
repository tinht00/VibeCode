(function initEditorStrategy(globalScope) {
  function getPromptWriteStrategy(descriptor) {
    const tagName = String(descriptor?.tagName || "").toLowerCase();
    const role = String(descriptor?.role || "").toLowerCase();

    if (tagName === "textarea" || tagName === "input") {
      return "native-value-setter";
    }

    if (descriptor?.isContentEditable || role === "textbox") {
      return "contenteditable-insert-text";
    }

    return "unsupported";
  }

  const exported = {
    getPromptWriteStrategy
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = exported;
  }

  globalScope.FlowBatchEditorStrategy = exported;
})(typeof globalThis !== "undefined" ? globalThis : window);
