const test = require("node:test");
const assert = require("node:assert/strict");

const { getPromptWriteStrategy } = require("../editorStrategy");

test("contenteditable textbox ưu tiên strategy insertText", () => {
  const strategy = getPromptWriteStrategy({
    tagName: "div",
    role: "textbox",
    isContentEditable: true
  });

  assert.equal(strategy, "contenteditable-insert-text");
});

test("textarea dùng native setter", () => {
  const strategy = getPromptWriteStrategy({
    tagName: "textarea",
    role: "",
    isContentEditable: false
  });

  assert.equal(strategy, "native-value-setter");
});
