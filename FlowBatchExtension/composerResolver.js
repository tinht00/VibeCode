(function initComposerResolver(globalScope) {
  const PROMPT_POSITIVE_TOKENS = [
    "ban muon tao gi",
    "what do you want",
    "what would you like",
    "mo ta y tuong",
    "cau lenh",
    "prompt",
    "describe",
    "textbox"
  ];

  const PROMPT_NEGATIVE_TOKENS = [
    "tim kiem",
    "search",
    "filter",
    "bo loc",
    "settings",
    "cai dat",
    "gallery",
    "home"
  ];

  const ACTION_POSITIVE_TOKENS = [
    "generate",
    "tao",
    "send",
    "submit",
    "arrow_forward",
    "arrow_upward",
    "north_east"
  ];

  const ACTION_NEGATIVE_TOKENS = [
    "settings",
    "cai dat",
    "filter",
    "tim kiem",
    "search",
    "more_vert",
    "gallery",
    "home",
    "play_movies",
    "trinh tao canh",
    "arrow_back",
    "quay lai",
    "add",
    "them noi dung"
  ];

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function buildText(candidate) {
    return normalizeText([
      candidate?.text,
      candidate?.ariaLabel,
      candidate?.placeholder,
      candidate?.title,
      candidate?.role,
      candidate?.type
    ].filter(Boolean).join(" "));
  }

  function rectOf(candidate) {
    return candidate?.rect || { top: 0, right: 0, bottom: 0, left: 0, width: 0, height: 0 };
  }

  function isVisible(candidate) {
    return Boolean(candidate?.isVisible);
  }

  function matchesRememberedId(candidate, rememberedId) {
    return Boolean(rememberedId) && candidate?.id === rememberedId;
  }

  function includesAny(text, tokens) {
    return tokens.some((token) => text.includes(token));
  }

  function scorePromptCandidate(candidate, options = {}) {
    if (!isVisible(candidate)) {
      return Number.NEGATIVE_INFINITY;
    }

    const viewportHeight = Number(options.viewportHeight) || 900;
    const text = buildText(candidate);
    const rect = rectOf(candidate);
    let score = 0;

    if (matchesRememberedId(candidate, options.rememberedPromptId)) {
      score += 60;
    }

    if (candidate?.composerId && candidate.composerId === options.rememberedComposerId) {
      score += 36;
    }

    if (candidate?.tagName === "textarea") {
      score += 22;
    }

    if (candidate?.tagName === "input" && (!candidate?.type || candidate.type === "text")) {
      score += 16;
    }

    if (candidate?.role === "textbox") {
      score += 20;
    }

    if (candidate?.isContentEditable) {
      score += 18;
    }

    if (includesAny(text, PROMPT_POSITIVE_TOKENS)) {
      score += 22;
    }

    if (includesAny(text, PROMPT_NEGATIVE_TOKENS)) {
      score -= 28;
    }

    if (rect.width >= 220) {
      score += 8;
    }

    if (rect.bottom >= viewportHeight * 0.55) {
      score += 10;
    }

    return score;
  }

  function pickPromptCandidate(candidates, options = {}) {
    const visibleCandidates = Array.isArray(candidates) ? candidates.filter(isVisible) : [];
    if (visibleCandidates.length === 0) {
      return null;
    }

    const remembered = visibleCandidates.find((candidate) => matchesRememberedId(candidate, options.rememberedPromptId));
    if (remembered) {
      return remembered;
    }

    const ranked = visibleCandidates
      .map((candidate) => ({ candidate, score: scorePromptCandidate(candidate, options) }))
      .sort((a, b) => b.score - a.score);

    return ranked[0]?.candidate || null;
  }

  function scoreGenerateButtonCandidate(candidate, promptCandidate, options = {}) {
    if (!isVisible(candidate)) {
      return Number.NEGATIVE_INFINITY;
    }

    const viewportHeight = Number(options.viewportHeight) || 900;
    const text = buildText(candidate);
    const rect = rectOf(candidate);
    const promptRect = rectOf(promptCandidate);
    let score = 0;

    if (matchesRememberedId(candidate, options.rememberedActionId)) {
      score += 48;
    }

    if (candidate?.composerId && promptCandidate?.composerId && candidate.composerId === promptCandidate.composerId) {
      score += 30;
    }

    if (candidate?.composerId && candidate.composerId === options.rememberedComposerId) {
      score += 22;
    }

    if (includesAny(text, ACTION_POSITIVE_TOKENS)) {
      score += 22;
    }

    if (includesAny(text, ACTION_NEGATIVE_TOKENS)) {
      score -= 40;
    }

    if (candidate?.type === "submit") {
      score += 10;
    }

    if (rect.width >= 28 && rect.width <= 72 && rect.height >= 28 && rect.height <= 72) {
      score += 8;
    }

    if (rect.bottom >= viewportHeight * 0.68) {
      score += 10;
    }

    if (promptCandidate) {
      const horizontalGap = Math.abs(rect.left - promptRect.right);
      const verticalGap = Math.abs((rect.top + rect.height / 2) - (promptRect.top + promptRect.height / 2));
      score += Math.max(0, 24 - horizontalGap / 8);
      score += Math.max(0, 16 - verticalGap / 8);

      if (rect.left >= promptRect.right - 24) {
        score += 10;
      }
    }

    return score;
  }

  function pickGenerateButtonCandidate(candidates, promptCandidate, options = {}) {
    const visibleCandidates = Array.isArray(candidates) ? candidates.filter(isVisible) : [];
    if (visibleCandidates.length === 0) {
      return null;
    }

    const remembered = visibleCandidates.find((candidate) => matchesRememberedId(candidate, options.rememberedActionId));
    if (remembered && scoreGenerateButtonCandidate(remembered, promptCandidate, options) > 0) {
      return remembered;
    }

    const ranked = visibleCandidates
      .map((candidate) => ({
        candidate,
        score: scoreGenerateButtonCandidate(candidate, promptCandidate, options)
      }))
      .sort((a, b) => b.score - a.score);

    return ranked[0]?.candidate || null;
  }

  const exported = {
    normalizeText,
    pickPromptCandidate,
    pickGenerateButtonCandidate,
    scorePromptCandidate,
    scoreGenerateButtonCandidate
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = exported;
  }

  globalScope.FlowBatchComposerResolver = exported;
})(typeof globalThis !== "undefined" ? globalThis : window);
