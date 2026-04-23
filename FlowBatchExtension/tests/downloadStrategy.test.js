const test = require("node:test");
const assert = require("node:assert/strict");

const {
  isDirectDownloadableUrl,
  normalizeDirectFormat,
  normalizeDownloadMethod,
  normalizeDownloadQuality,
  splitDownloadItems
} = require("../downloadStrategy");

test("http, https và data URL được tải trực tiếp", () => {
  assert.equal(isDirectDownloadableUrl("https://example.com/image.png"), true);
  assert.equal(isDirectDownloadableUrl("http://example.com/image.jpg"), true);
  assert.equal(isDirectDownloadableUrl("data:image/png;base64,AAAA"), true);
});

test("blob URL và URL rỗng phải fallback qua menu Flow", () => {
  assert.equal(isDirectDownloadableUrl("blob:https://labs.google/id"), false);
  assert.equal(isDirectDownloadableUrl(""), false);
});

test("splitDownloadItems tách đúng direct và fallback", () => {
  const items = [
    { id: "a", imageUrl: "https://example.com/a.png" },
    { id: "b", imageUrl: "blob:https://labs.google/b" },
    { id: "c", imageUrl: "data:image/webp;base64,AAAA" }
  ];

  const result = splitDownloadItems(items);

  assert.deepEqual(result.directItems.map((item) => item.id), ["a", "c"]);
  assert.deepEqual(result.fallbackItems.map((item) => item.id), ["b"]);
});

test("normalizeDownloadQuality chỉ cho phép 1K hoặc 2K", () => {
  assert.equal(normalizeDownloadQuality("1K"), "1k");
  assert.equal(normalizeDownloadQuality("2k"), "2k");
  assert.equal(normalizeDownloadQuality("4k"), "2k");
  assert.equal(normalizeDownloadQuality(""), "2k");
});

test("normalizeDownloadMethod mặc định về tải URL trực tiếp", () => {
  assert.equal(normalizeDownloadMethod("flow-menu"), "flow-menu");
  assert.equal(normalizeDownloadMethod("direct-url"), "direct-url");
  assert.equal(normalizeDownloadMethod("unknown"), "direct-url");
});

test("normalizeDirectFormat chỉ cho phép JPG, PNG hoặc WebP", () => {
  assert.equal(normalizeDirectFormat("jpg"), "jpg");
  assert.equal(normalizeDirectFormat("png"), "png");
  assert.equal(normalizeDirectFormat("webp"), "webp");
  assert.equal(normalizeDirectFormat("jfif"), "jpg");
  assert.equal(normalizeDirectFormat(""), "jpg");
});
