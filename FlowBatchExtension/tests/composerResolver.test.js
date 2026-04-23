const test = require("node:test");
const assert = require("node:assert/strict");

const {
  pickPromptCandidate,
  pickGenerateButtonCandidate
} = require("../composerResolver");

function createPromptCandidate(overrides = {}) {
  return {
    id: overrides.id || "prompt",
    composerId: overrides.composerId || "composer-a",
    kind: "prompt",
    tagName: overrides.tagName || "textarea",
    role: overrides.role || "",
    type: overrides.type || "",
    text: overrides.text || "",
    ariaLabel: overrides.ariaLabel || "",
    placeholder: overrides.placeholder || "",
    title: overrides.title || "",
    isContentEditable: Boolean(overrides.isContentEditable),
    isVisible: overrides.isVisible !== false,
    rect: overrides.rect || { top: 720, right: 860, bottom: 804, left: 240, width: 620, height: 84 }
  };
}

function createButtonCandidate(overrides = {}) {
  return {
    id: overrides.id || "button",
    composerId: overrides.composerId || "composer-a",
    kind: "button",
    tagName: overrides.tagName || "button",
    role: overrides.role || "button",
    type: overrides.type || "",
    text: overrides.text || "",
    ariaLabel: overrides.ariaLabel || "",
    placeholder: overrides.placeholder || "",
    title: overrides.title || "",
    isContentEditable: false,
    isVisible: overrides.isVisible !== false,
    rect: overrides.rect || { top: 734, right: 924, bottom: 786, left: 872, width: 52, height: 52 }
  };
}

test("pickPromptCandidate ưu tiên prompt trong composer vừa được nhớ", () => {
  const rememberedPrompt = createPromptCandidate({
    id: "remembered-prompt",
    composerId: "composer-remembered",
    ariaLabel: "Bạn muốn tạo gì?"
  });
  const strayPrompt = createPromptCandidate({
    id: "stray-prompt",
    composerId: "composer-other",
    tagName: "div",
    role: "textbox",
    ariaLabel: "Bộ lọc"
  });

  const result = pickPromptCandidate([strayPrompt, rememberedPrompt], {
    rememberedPromptId: "remembered-prompt",
    rememberedComposerId: "composer-remembered",
    viewportHeight: 900
  });

  assert.equal(result?.id, "remembered-prompt");
});

test("pickGenerateButtonCandidate ưu tiên nút submit cùng composer thay vì button gây nhiễu", () => {
  const prompt = createPromptCandidate({
    id: "prompt-a",
    composerId: "composer-a",
    ariaLabel: "Bạn muốn tạo gì?",
    rect: { top: 730, right: 860, bottom: 806, left: 220, width: 640, height: 76 }
  });

  const wrongTopButton = createButtonCandidate({
    id: "settings-top",
    composerId: "header",
    text: "settings_2",
    ariaLabel: "Xem chế độ cài đặt",
    rect: { top: 44, right: 1180, bottom: 96, left: 1128, width: 52, height: 52 }
  });

  const submitButton = createButtonCandidate({
    id: "submit-a",
    composerId: "composer-a",
    ariaLabel: "Generate image",
    text: "arrow_forward",
    rect: { top: 738, right: 926, bottom: 790, left: 874, width: 52, height: 52 }
  });

  const result = pickGenerateButtonCandidate([wrongTopButton, submitButton], prompt, {
    rememberedComposerId: "composer-a",
    rememberedActionId: "submit-a",
    viewportHeight: 900,
    viewportWidth: 1280
  });

  assert.equal(result?.id, "submit-a");
});

test("pickGenerateButtonCandidate bỏ qua action đã nhớ nếu không còn hợp lệ", () => {
  const prompt = createPromptCandidate({
    id: "prompt-a",
    composerId: "composer-a",
    ariaLabel: "What do you want to create?",
    rect: { top: 708, right: 852, bottom: 792, left: 212, width: 640, height: 84 }
  });

  const staleButton = createButtonCandidate({
    id: "old-submit",
    composerId: "composer-a",
    ariaLabel: "Generate image",
    isVisible: false
  });

  const fallbackButton = createButtonCandidate({
    id: "fallback-submit",
    composerId: "composer-a",
    ariaLabel: "Generate image",
    text: "arrow_forward",
    rect: { top: 724, right: 928, bottom: 780, left: 872, width: 56, height: 56 }
  });

  const result = pickGenerateButtonCandidate([staleButton, fallbackButton], prompt, {
    rememberedComposerId: "composer-a",
    rememberedActionId: "old-submit",
    viewportHeight: 900,
    viewportWidth: 1280
  });

  assert.equal(result?.id, "fallback-submit");
});
