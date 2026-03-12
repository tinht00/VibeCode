"""Các rule validate nội bộ cho metadata và media URL."""

from __future__ import annotations

from clipart_ops.domain.models import MetadataCandidate

ETSY_TITLE_MAX = 140
PINTEREST_DESCRIPTION_MAX = 500
MAX_TAGS = 13


def score_candidate(candidate: MetadataCandidate) -> MetadataCandidate:
    """Chấm điểm nhanh candidate dựa trên rule cục bộ."""
    warnings = list(candidate.warnings)
    seo = 90
    clarity = 90
    policy = 95

    if len(candidate.etsy_title) > ETSY_TITLE_MAX:
        warnings.append("Tiêu đề Etsy vượt giới hạn nội bộ 140 ký tự.")
        seo -= 15
        policy -= 10
    if len(candidate.pinterest_description) > PINTEREST_DESCRIPTION_MAX:
        warnings.append("Mô tả Pinterest vượt 500 ký tự.")
        clarity -= 15
        policy -= 10
    if len(candidate.etsy_tags) > MAX_TAGS:
        warnings.append("Số lượng tag Etsy vượt 13 tag.")
        seo -= 10
    unique_tags = {tag.strip().lower() for tag in candidate.etsy_tags if tag.strip()}
    if len(unique_tags) != len(candidate.etsy_tags):
        warnings.append("Tag Etsy bị lặp.")
        seo -= 8

    prohibited_fragments = ["best seller", "guaranteed", "official disney", "licensed"]
    text_blob = " ".join(
        [
            candidate.etsy_title.lower(),
            candidate.etsy_description.lower(),
            candidate.pinterest_title.lower(),
            candidate.pinterest_description.lower(),
        ]
    )
    for fragment in prohibited_fragments:
        if fragment in text_blob:
            warnings.append(f"Phát hiện claim rủi ro: {fragment}.")
            policy -= 15

    candidate.warnings = warnings
    candidate.scores.seo = max(seo, 0)
    candidate.scores.clarity = max(clarity, 0)
    candidate.scores.policy_safety = max(policy, 0)
    return candidate
