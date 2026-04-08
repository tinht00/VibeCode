"""Audit engine cho listing Etsy."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import BenchmarkQuery, BenchmarkSnapshot, Listing, ListingAudit


@dataclass
class AuditFinding:
    """Kết quả của một rule đơn lẻ."""

    code: str
    severity: str
    score_delta: int
    message_vi: str
    action_vi: str

    def as_dict(self) -> dict:
        """Chuyển sang dict để lưu DB/JSON."""

        return {
            "code": self.code,
            "severity": self.severity,
            "score_delta": self.score_delta,
            "message_vi": self.message_vi,
            "action_vi": self.action_vi,
        }


def _recommendation(code: str, title: str, content: str) -> dict:
    """Sinh khối recommendation ngắn gọn cho UI."""

    return {"code": code, "title": title, "content": content}


def _title_rules(listing: Listing) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    title = listing.title.strip()
    if len(title) < 25:
        findings.append(
            AuditFinding(
                code="TITLE_TOO_SHORT",
                severity="medium",
                score_delta=12,
                message_vi="Tiêu đề đang quá ngắn nên khó diễn đạt rõ ý định tìm kiếm.",
                action_vi="Mở rộng tiêu đề bằng cụm chính + chất liệu + đối tượng mua phù hợp.",
            )
        )
    if len(title) > 140:
        findings.append(
            AuditFinding(
                code="TITLE_TOO_LONG",
                severity="medium",
                score_delta=10,
                message_vi="Tiêu đề dài quá mức dễ giảm khả năng đọc nhanh.",
                action_vi="Rút gọn bớt các cụm lặp hoặc modifier ít giá trị.",
            )
        )
    first_words = title.lower().split()[:3]
    if len(first_words) >= 3 and len(set(first_words)) == 1:
        findings.append(
            AuditFinding(
                code="TITLE_WEAK_OPENING",
                severity="high",
                score_delta=15,
                message_vi="Cụm mở đầu tiêu đề không đủ mạnh hoặc lặp từ quá sớm.",
                action_vi="Đưa cụm sản phẩm chính lên đầu tiêu đề một cách tự nhiên.",
            )
        )
    return findings


def _tag_rules(listing: Listing) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    tags = [item.tag.strip().lower() for item in listing.tags if item.tag.strip()]
    if len(tags) < 8:
        findings.append(
            AuditFinding(
                code="TOO_FEW_TAGS",
                severity="high",
                score_delta=18,
                message_vi="Listing đang dùng quá ít tags so với mức khuyến nghị của Etsy.",
                action_vi="Bổ sung thêm các tag long-tail mô tả chủ thể, dịp tặng và vật liệu.",
            )
        )
    duplicates = [tag for tag, count in Counter(tags).items() if count > 1]
    if duplicates:
        findings.append(
            AuditFinding(
                code="DUPLICATE_TAGS",
                severity="medium",
                score_delta=10,
                message_vi="Một số tags đang bị lặp và không mở rộng thêm phủ từ khóa.",
                action_vi=f"Thay thế các tag trùng như {', '.join(duplicates[:3])} bằng biến thể dài hơn.",
            )
        )
    return findings


def _taxonomy_rules(listing: Listing) -> list[AuditFinding]:
    if listing.taxonomy_id is None:
        return [
            AuditFinding(
                code="MISSING_TAXONOMY",
                severity="high",
                score_delta=16,
                message_vi="Listing chưa có taxonomy/category cụ thể.",
                action_vi="Chọn category sâu nhất có thể trong Etsy để hệ thống hiểu đúng sản phẩm.",
            )
        ]
    return []


def _attribute_rules(listing: Listing) -> list[AuditFinding]:
    if len(listing.attributes) < 2:
        return [
            AuditFinding(
                code="LOW_ATTRIBUTE_COVERAGE",
                severity="medium",
                score_delta=12,
                message_vi="Listing đang thiếu thuộc tính quan trọng để mở rộng tìm kiếm.",
                action_vi="Điền thêm thuộc tính về chất liệu, dịp dùng hoặc đối tượng nhận quà.",
            )
        ]
    return []


def _description_rules(listing: Listing) -> list[AuditFinding]:
    opening = listing.description.strip()[:160]
    if len(opening) < 80:
        return [
            AuditFinding(
                code="THIN_DESCRIPTION_OPENING",
                severity="medium",
                score_delta=10,
                message_vi="Phần mở đầu mô tả còn mỏng, chưa nêu rõ sản phẩm và bối cảnh mua.",
                action_vi="Viết 2-3 câu đầu giải thích sản phẩm là gì, dành cho ai và dùng khi nào.",
            )
        ]
    return []


def _image_rules(listing: Listing) -> list[AuditFinding]:
    if len(listing.images) < settings.min_listing_images:
        return [
            AuditFinding(
                code="LOW_IMAGE_COUNT",
                severity="medium",
                score_delta=10,
                message_vi="Số lượng ảnh listing còn ít so với mức nên có cho Etsy.",
                action_vi="Bổ sung thêm ảnh lifestyle, ảnh chi tiết và ảnh nêu kích thước nếu phù hợp.",
            )
        ]
    return []


def _price_rules(db: Session, listing: Listing) -> list[AuditFinding]:
    latest_query = (
        db.query(BenchmarkQuery)
        .filter(BenchmarkQuery.shop_id == listing.shop_id)
        .order_by(BenchmarkQuery.last_captured_at.desc().nullslast())
        .first()
    )
    if latest_query is None or listing.price_amount is None:
        return []

    snapshot_prices = [
        item.price_amount
        for item in db.query(BenchmarkSnapshot)
        .filter(BenchmarkSnapshot.benchmark_query_id == latest_query.id)
        .all()
        if item.price_amount is not None
    ]
    if len(snapshot_prices) < 3:
        return []
    baseline = mean(snapshot_prices)
    if listing.price_amount > baseline * 1.4 or listing.price_amount < baseline * 0.6:
        return [
            AuditFinding(
                code="PRICE_OUTLIER",
                severity="low",
                score_delta=8,
                message_vi="Giá listing đang lệch đáng kể so với mặt bằng benchmark gần nhất.",
                action_vi="Kiểm tra lại giá trị cảm nhận, bundle và USP trước khi tăng hoặc giảm giá.",
            )
        ]
    return []


def run_listing_audit(db: Session, listing: Listing) -> ListingAudit:
    """Chạy toàn bộ rules và lưu kết quả audit."""

    groups = {
        "title_score": _title_rules(listing),
        "tag_score": _tag_rules(listing),
        "taxonomy_score": _taxonomy_rules(listing),
        "attribute_score": _attribute_rules(listing),
        "description_score": _description_rules(listing),
        "image_score": _image_rules(listing),
        "price_score": _price_rules(db, listing),
    }
    total_penalty = sum(item.score_delta for values in groups.values() for item in values)
    recommendations: list[dict] = []
    if not groups["title_score"]:
        recommendations.append(
            _recommendation(
                "TITLE_GOOD_BASE",
                "Tiêu đề đã có nền tảng tốt",
                "Giữ cấu trúc mở đầu hiện tại và chỉ tinh chỉnh thêm long-tail theo benchmark.",
            )
        )
    for finding in [item for values in groups.values() for item in values]:
        recommendations.append(_recommendation(finding.code, "Việc nên làm tiếp theo", finding.action_vi))

    audit = ListingAudit(
        listing=listing,
        overall_score=max(0, 100 - total_penalty),
        title_score=max(0, 100 - sum(item.score_delta for item in groups["title_score"])),
        tag_score=max(0, 100 - sum(item.score_delta for item in groups["tag_score"])),
        taxonomy_score=max(0, 100 - sum(item.score_delta for item in groups["taxonomy_score"])),
        attribute_score=max(0, 100 - sum(item.score_delta for item in groups["attribute_score"])),
        description_score=max(0, 100 - sum(item.score_delta for item in groups["description_score"])),
        image_score=max(0, 100 - sum(item.score_delta for item in groups["image_score"])),
        price_score=max(0, 100 - sum(item.score_delta for item in groups["price_score"])),
        findings_json=[item.as_dict() for values in groups.values() for item in values],
        recommendations_json=recommendations,
    )
    db.add(audit)
    db.flush()
    return audit
