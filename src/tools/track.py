"""track_package and my_packages tools - Core delivery tracking functionality."""

from src.services.sweet_tracker import sweet_tracker, TrackingResult
from src.services.carrier_info import (
    get_carrier_by_code,
    get_carrier_by_name,
    detect_carrier_from_tracking,
)
from src.utils.status_translator import (
    translate_status,
    get_progress_percentage,
    DeliveryPhase,
)
from src.utils.tracking_parser import normalize_tracking_number


def _format_tracking_result(result: TrackingResult) -> str:
    """Format tracking result into user-friendly output."""
    if not result.success:
        carrier = get_carrier_by_code(result.carrier_code) if result.carrier_code else None
        contact = carrier.contact if carrier else "해당 택배사"

        return (
            f"❌ 조회 실패\n\n"
            f"운송장: {result.tracking_number}\n"
            f"택배사: {result.carrier_name}\n"
            f"오류: {result.error_message}\n\n"
            f"💡 확인사항:\n"
            f"• 운송장 번호가 정확한지 확인해주세요\n"
            f"• 택배사가 맞는지 확인해주세요\n"
            f"• 발송 직후라면 1-2시간 후 다시 조회해주세요\n"
            f"• 문제가 계속되면 {contact}에 문의해주세요"
        )

    # Translate current status
    status_info = translate_status(result.current_status)
    progress = get_progress_percentage(status_info.phase)

    # Build output
    lines = []

    # Header
    lines.append(f"📦 {result.carrier_name} 배송 현황")
    lines.append(f"운송장: {result.tracking_number}")
    lines.append("")

    # Current status with translation
    lines.append(f"{status_info.emoji} 현재 상태: {status_info.translated}")
    lines.append(f"   (원본: {status_info.original})")
    lines.append("")

    # Progress bar
    filled = int(progress / 10)
    empty = 10 - filled
    progress_bar = "█" * filled + "░" * empty
    lines.append(f"진행률: [{progress_bar}] {progress}%")
    lines.append("")

    # Estimated time
    if status_info.estimated_hours is not None and not status_info.is_final:
        if status_info.estimated_hours <= 3:
            lines.append("🕐 예상 도착: 곧 도착해요!")
        elif status_info.estimated_hours <= 6:
            lines.append("🕐 예상 도착: 오늘 중")
        elif status_info.estimated_hours <= 24:
            lines.append("🕐 예상 도착: 내일 예상")
        else:
            days = status_info.estimated_hours // 24
            lines.append(f"🕐 예상 도착: {days}일 후 예상")
        lines.append("")

    # Delivery timeline (last 5 events)
    if result.events:
        lines.append("📜 배송 경로:")
        recent_events = result.events[-5:]  # Last 5 events
        for event in reversed(recent_events):
            event_status = translate_status(event.status)
            lines.append(f"  {event_status.emoji} {event.time} | {event_status.short}")
            if event.location:
                lines.append(f"     📍 {event.location}")

        if len(result.events) > 5:
            lines.append(f"  ... 외 {len(result.events) - 5}건")
        lines.append("")

    # Carrier contact info
    carrier = get_carrier_by_code(result.carrier_code)
    if carrier:
        lines.append(f"📞 {carrier.name}: {carrier.contact}")
        lines.append(f"🔗 조회: {carrier.tracking_url}")

    return "\n".join(lines)


async def track_package(
    tracking_number: str,
    carrier: str = "auto"
) -> str:
    """
    Track a delivery package and get status in plain Korean.

    This tool looks up the delivery status and translates technical
    carrier terms into everyday language that's easy to understand.

    Args:
        tracking_number: The tracking/invoice number (운송장 번호)
        carrier: Carrier name or code. Use "auto" for automatic detection.
                 Examples: "CJ대한통운", "롯데택배", "한진", "우체국", "04"

    Returns:
        Delivery status with timeline, translated to user-friendly Korean
    """
    # Normalize tracking number
    tracking_number = normalize_tracking_number(tracking_number)

    if not tracking_number:
        return "운송장 번호를 입력해주세요."

    # Determine carrier code
    carrier_code = None

    if carrier.lower() == "auto":
        # Auto-detect carrier
        carrier_code = detect_carrier_from_tracking(tracking_number)
        if carrier_code:
            result = await sweet_tracker.track(tracking_number, carrier_code)
        else:
            result = await sweet_tracker.track_auto_detect(tracking_number)
    else:
        # Try to find carrier by name or code
        carrier_obj = get_carrier_by_name(carrier)
        if carrier_obj:
            carrier_code = carrier_obj.code
        elif carrier.isdigit() and len(carrier) <= 3:
            carrier_code = carrier.zfill(2)

        if carrier_code:
            result = await sweet_tracker.track(tracking_number, carrier_code)
        else:
            return (
                f"'{carrier}' 택배사를 찾을 수 없어요.\n\n"
                "지원하는 택배사:\n"
                "• CJ대한통운\n"
                "• 롯데택배\n"
                "• 한진택배\n"
                "• 우체국택배\n"
                "• 로젠택배\n"
                "등\n\n"
                "택배사 이름을 다시 확인해주세요."
            )

    return _format_tracking_result(result)


async def my_packages(tracking_numbers: str) -> str:
    """
    Track multiple packages at once and get a prioritized summary.

    This tool tracks several packages simultaneously and organizes them
    by priority (urgent items first, issues highlighted).

    Args:
        tracking_numbers: Comma-separated list of tracking numbers
                         (e.g., "640123456789, 234567890123, 345678901234")

    Returns:
        Summary of all packages with priority ordering and action items
    """
    if not tracking_numbers:
        return "운송장 번호를 입력해주세요. (쉼표로 구분)"

    # Parse tracking numbers
    numbers = [
        normalize_tracking_number(n.strip())
        for n in tracking_numbers.split(",")
        if n.strip()
    ]

    if not numbers:
        return "유효한 운송장 번호를 찾을 수 없어요."

    if len(numbers) > 10:
        return "한 번에 최대 10개까지 조회할 수 있어요."

    # Track all packages
    results = []
    for num in numbers:
        result = await sweet_tracker.track_auto_detect(num)
        status_info = translate_status(result.current_status) if result.success else None
        results.append((num, result, status_info))

    # Categorize results
    delivered = []
    arriving_today = []
    in_transit = []
    issues = []
    failed = []

    for num, result, status_info in results:
        if not result.success:
            failed.append((num, result))
        elif result.is_delivered:
            delivered.append((num, result, status_info))
        elif status_info and status_info.phase == DeliveryPhase.ISSUE:
            issues.append((num, result, status_info))
        elif status_info and status_info.phase == DeliveryPhase.OUT_FOR_DELIVERY:
            arriving_today.append((num, result, status_info))
        else:
            in_transit.append((num, result, status_info))

    # Build output
    lines = []
    lines.append(f"📦 내 택배 현황 ({len(numbers)}건)")
    lines.append("")

    # Summary
    lines.append("📊 요약")
    lines.append(f"  ✅ 배송 완료: {len(delivered)}건")
    lines.append(f"  🚚 오늘 도착 예정: {len(arriving_today)}건")
    lines.append(f"  📦 배송 중: {len(in_transit)}건")
    if issues:
        lines.append(f"  ⚠️ 주의 필요: {len(issues)}건")
    if failed:
        lines.append(f"  ❌ 조회 실패: {len(failed)}건")
    lines.append("")

    # Priority items (arriving today + issues first)
    if arriving_today:
        lines.append("🚚 오늘 도착 예정")
        for num, result, status_info in arriving_today:
            lines.append(f"  • {num[:6]}... ({result.carrier_name})")
            lines.append(f"    {status_info.emoji} {status_info.translated}")
        lines.append("")

    if issues:
        lines.append("⚠️ 확인 필요")
        for num, result, status_info in issues:
            lines.append(f"  • {num[:6]}... ({result.carrier_name})")
            lines.append(f"    {status_info.emoji} {status_info.translated}")
        lines.append("")

    if in_transit:
        lines.append("📦 배송 중")
        for num, result, status_info in in_transit:
            if status_info:
                lines.append(f"  • {num[:6]}... - {status_info.short}")
        lines.append("")

    if delivered:
        lines.append("✅ 배송 완료")
        for num, result, status_info in delivered:
            lines.append(f"  • {num[:6]}... ({result.carrier_name})")
        lines.append("")

    if failed:
        lines.append("❌ 조회 실패")
        for num, result in failed:
            lines.append(f"  • {num[:6]}... - {result.error_message}")
        lines.append("")

    # Action items
    action_items = []
    if issues:
        action_items.append("⚠️ 문제 있는 택배 확인 필요")
    if arriving_today:
        action_items.append("🏠 오늘 택배 수령 준비")

    if action_items:
        lines.append("💡 할 일")
        for item in action_items:
            lines.append(f"  {item}")

    return "\n".join(lines)
