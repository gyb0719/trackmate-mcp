"""Delivery status translator - converts technical terms to everyday Korean."""

from dataclasses import dataclass
from enum import Enum


class DeliveryPhase(Enum):
    """Delivery phase for progress indication."""
    PICKUP = "pickup"      # 물건 수거
    IN_TRANSIT = "transit" # 이동 중
    OUT_FOR_DELIVERY = "out"  # 배송 출발
    DELIVERED = "delivered"   # 배송 완료
    ISSUE = "issue"           # 문제 발생


@dataclass
class TranslatedStatus:
    """Translated delivery status with context."""
    original: str           # 원본 상태 (예: SM입고)
    translated: str         # 번역된 상태 (예: 배송 기사님이 물건 받았어요)
    short: str              # 짧은 버전 (예: 기사님 수령)
    phase: DeliveryPhase    # 단계
    emoji: str              # 상태 이모지
    is_final: bool          # 최종 상태 여부
    estimated_hours: int | None  # 예상 남은 시간 (시간 단위)


# Status translation mapping
# Key: lowercase status keyword, Value: (translated, short, phase, emoji, is_final, est_hours)
STATUS_TRANSLATIONS: dict[str, tuple[str, str, DeliveryPhase, str, bool, int | None]] = {
    # 접수/수거 단계
    "접수": ("판매자가 택배를 접수했어요", "접수됨", DeliveryPhase.PICKUP, "📝", False, 72),
    "집화처리": ("택배사가 물건을 수거했어요", "수거 완료", DeliveryPhase.PICKUP, "📦", False, 48),
    "집하": ("택배사가 물건을 수거했어요", "수거 완료", DeliveryPhase.PICKUP, "📦", False, 48),
    "상품인수": ("택배사가 물건을 받았어요", "인수 완료", DeliveryPhase.PICKUP, "📦", False, 48),

    # 이동 단계
    "간선상차": ("큰 트럭에 실려서 다음 허브로 이동 중이에요", "허브 이동 중", DeliveryPhase.IN_TRANSIT, "🚛", False, 24),
    "간선하차": ("허브에 도착해서 분류 중이에요", "허브 도착", DeliveryPhase.IN_TRANSIT, "🏭", False, 18),
    "간선": ("허브 간 이동 중이에요", "이동 중", DeliveryPhase.IN_TRANSIT, "🚛", False, 24),
    "행낭포장": ("여러 소포를 묶어서 포장 중이에요", "포장 중", DeliveryPhase.IN_TRANSIT, "📮", False, 24),
    "발송": ("발송 처리되었어요", "발송됨", DeliveryPhase.IN_TRANSIT, "📤", False, 48),
    "출고": ("출고 처리되었어요", "출고됨", DeliveryPhase.IN_TRANSIT, "📤", False, 48),
    "입고": ("허브에 도착했어요", "허브 입고", DeliveryPhase.IN_TRANSIT, "🏢", False, 18),
    "상차": ("트럭에 상차되었어요", "상차됨", DeliveryPhase.IN_TRANSIT, "🚚", False, 12),
    "하차": ("도착지에서 하차되었어요", "하차됨", DeliveryPhase.IN_TRANSIT, "📥", False, 8),
    "터미널": ("터미널에서 분류 중이에요", "터미널 분류", DeliveryPhase.IN_TRANSIT, "🏭", False, 18),
    "이동중": ("배송 중이에요", "이동 중", DeliveryPhase.IN_TRANSIT, "🚚", False, 12),

    # 배송 출발 단계
    "sm입고": ("배송 기사님이 물건을 받았어요! 오늘 도착 예정", "기사님 수령", DeliveryPhase.OUT_FOR_DELIVERY, "🙋", False, 6),
    "배달출발": ("배송 기사님이 출발했어요! 곧 도착해요", "배송 출발", DeliveryPhase.OUT_FOR_DELIVERY, "🚚", False, 3),
    "배달준비": ("배송 준비 중이에요", "배송 준비", DeliveryPhase.OUT_FOR_DELIVERY, "📋", False, 6),
    "배송출발": ("배송 기사님이 출발했어요!", "배송 출발", DeliveryPhase.OUT_FOR_DELIVERY, "🚚", False, 3),
    "배달중": ("배송 중이에요! 조금만 기다려주세요", "배송 중", DeliveryPhase.OUT_FOR_DELIVERY, "🚚", False, 2),

    # 배송 완료 단계
    "배달완료": ("배송이 완료되었어요! 확인해주세요", "배송 완료", DeliveryPhase.DELIVERED, "✅", True, 0),
    "배송완료": ("배송이 완료되었어요! 확인해주세요", "배송 완료", DeliveryPhase.DELIVERED, "✅", True, 0),
    "인수확인": ("수령이 확인되었어요", "수령 완료", DeliveryPhase.DELIVERED, "✅", True, 0),
    "수령": ("수령이 확인되었어요", "수령 완료", DeliveryPhase.DELIVERED, "✅", True, 0),
    "완료": ("배송이 완료되었어요!", "완료", DeliveryPhase.DELIVERED, "✅", True, 0),

    # 특수 상황
    "반송": ("반송 처리되었어요. 판매자에게 문의해주세요", "반송", DeliveryPhase.ISSUE, "↩️", True, None),
    "미배달": ("배송을 못 했어요. 재배송 예정이에요", "미배달", DeliveryPhase.ISSUE, "⚠️", False, 24),
    "보관": ("물건을 보관 중이에요 (경비실/택배함 등)", "보관 중", DeliveryPhase.DELIVERED, "📍", True, 0),
    "부재": ("부재중이라 배송을 못 했어요", "부재", DeliveryPhase.ISSUE, "🏠", False, 24),
    "주소불명": ("주소가 불명확해요. 판매자에게 확인 요청해주세요", "주소 오류", DeliveryPhase.ISSUE, "❓", False, None),
    "수취거부": ("수취가 거부되었어요", "수취 거부", DeliveryPhase.ISSUE, "🚫", True, None),
    "분실": ("분실 처리되었어요. 판매자에게 문의해주세요", "분실", DeliveryPhase.ISSUE, "❌", True, None),
}


def translate_status(raw_status: str) -> TranslatedStatus:
    """
    Translate raw delivery status to user-friendly Korean.

    Args:
        raw_status: Raw status string from carrier API

    Returns:
        TranslatedStatus with translation and metadata
    """
    status_lower = raw_status.lower().replace(" ", "")

    # Direct match
    if status_lower in STATUS_TRANSLATIONS:
        trans, short, phase, emoji, is_final, est = STATUS_TRANSLATIONS[status_lower]
        return TranslatedStatus(
            original=raw_status,
            translated=trans,
            short=short,
            phase=phase,
            emoji=emoji,
            is_final=is_final,
            estimated_hours=est
        )

    # Partial match
    for keyword, (trans, short, phase, emoji, is_final, est) in STATUS_TRANSLATIONS.items():
        if keyword in status_lower:
            return TranslatedStatus(
                original=raw_status,
                translated=trans,
                short=short,
                phase=phase,
                emoji=emoji,
                is_final=is_final,
                estimated_hours=est
            )

    # Unknown status - make best guess based on common patterns
    if "완료" in status_lower or "도착" in status_lower:
        return TranslatedStatus(
            original=raw_status,
            translated=f"{raw_status} - 배송 진행 중인 것 같아요",
            short=raw_status[:6],
            phase=DeliveryPhase.IN_TRANSIT,
            emoji="📦",
            is_final=False,
            estimated_hours=24
        )

    # Default unknown
    return TranslatedStatus(
        original=raw_status,
        translated=f"'{raw_status}' 상태예요. 배송이 진행 중인 것 같아요",
        short=raw_status[:6] if len(raw_status) > 6 else raw_status,
        phase=DeliveryPhase.IN_TRANSIT,
        emoji="📦",
        is_final=False,
        estimated_hours=None
    )


def get_progress_percentage(phase: DeliveryPhase) -> int:
    """Get progress percentage for a delivery phase."""
    progress_map = {
        DeliveryPhase.PICKUP: 20,
        DeliveryPhase.IN_TRANSIT: 50,
        DeliveryPhase.OUT_FOR_DELIVERY: 80,
        DeliveryPhase.DELIVERED: 100,
        DeliveryPhase.ISSUE: 50,  # Issues are mid-progress
    }
    return progress_map.get(phase, 0)


def format_timeline_entry(status: str, location: str, time_str: str) -> str:
    """Format a timeline entry with translation."""
    translated = translate_status(status)
    return f"{translated.emoji} {time_str} | {translated.short} ({location})"
