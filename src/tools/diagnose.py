"""diagnose_problem tool - Analyze delivery issues and suggest solutions."""

from datetime import datetime, timedelta

from src.services.sweet_tracker import sweet_tracker, TrackingResult
from src.services.carrier_info import (
    detect_carrier_from_tracking,
    get_carrier_by_code,
    get_carrier_by_name,
)
from src.utils.status_translator import translate_status, DeliveryPhase
from src.utils.tracking_parser import normalize_tracking_number


def _analyze_stagnation(events: list, carrier_code: str) -> dict:
    """Analyze if package is stagnant and determine possible causes."""
    if not events:
        return {
            "is_stagnant": False,
            "days_stagnant": 0,
            "last_location": None,
            "possible_causes": [],
        }

    # Get last event time
    last_event = events[-1]
    last_time_str = last_event.time

    # Parse time (format varies by carrier)
    try:
        # Try common formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M"]:
            try:
                last_time = datetime.strptime(last_time_str, fmt)
                break
            except ValueError:
                continue
        else:
            # If parsing fails, assume recent
            return {
                "is_stagnant": False,
                "days_stagnant": 0,
                "last_location": last_event.location,
                "possible_causes": [],
            }

        # Calculate days since last update
        days_since = (datetime.now() - last_time).days

        if days_since >= 2:
            # Determine causes based on location
            location = last_event.location or ""
            possible_causes = []

            if "허브" in location or "터미널" in location:
                possible_causes.append(("물량 폭주로 인한 분류 지연", 60))
                possible_causes.append(("분류 과정에서 누락", 30))
                possible_causes.append(("시스템 오류", 10))
            elif "공항" in location:
                possible_causes.append(("통관 지연", 70))
                possible_causes.append(("세관 검사", 20))
                possible_causes.append(("서류 문제", 10))
            else:
                possible_causes.append(("물량 폭주로 인한 지연", 50))
                possible_causes.append(("배송 경로 변경", 25))
                possible_causes.append(("분류 누락 가능성", 25))

            return {
                "is_stagnant": True,
                "days_stagnant": days_since,
                "last_location": location,
                "possible_causes": possible_causes,
            }

    except Exception:
        pass

    return {
        "is_stagnant": False,
        "days_stagnant": 0,
        "last_location": last_event.location if events else None,
        "possible_causes": [],
    }


def _get_recommended_actions(
    result: TrackingResult,
    status_info,
    stagnation: dict
) -> list[dict]:
    """Get recommended actions based on the diagnosis."""
    actions = []
    carrier = get_carrier_by_code(result.carrier_code)
    carrier_contact = carrier.contact if carrier else "택배사"

    # Stagnation issues
    if stagnation["is_stagnant"]:
        days = stagnation["days_stagnant"]

        if days >= 5:
            actions.append({
                "priority": 1,
                "action": "택배사 고객센터에 분실 여부 확인",
                "detail": f"전화: {carrier_contact}",
            })
            actions.append({
                "priority": 2,
                "action": "판매자에게 배송 확인 요청",
                "detail": "분실 시 재발송 또는 환불 협의",
            })
        elif days >= 3:
            actions.append({
                "priority": 1,
                "action": "택배사 고객센터 문의",
                "detail": f"전화: {carrier_contact}",
            })
            actions.append({
                "priority": 2,
                "action": "판매자에게 상황 공유",
                "detail": "배송 지연 상황 알리기",
            })
        else:
            actions.append({
                "priority": 1,
                "action": "1-2일 더 대기",
                "detail": "물량 폭주 시 자연 해소될 수 있음",
            })
            actions.append({
                "priority": 2,
                "action": "개선 없으면 택배사 문의",
                "detail": f"전화: {carrier_contact}",
            })

    # Issue-specific actions
    if status_info.phase == DeliveryPhase.ISSUE:
        status_lower = status_info.original.lower()

        if "반송" in status_lower:
            actions = [{
                "priority": 1,
                "action": "판매자에게 즉시 연락",
                "detail": "반송 사유 확인 및 재발송 요청",
            }]
        elif "주소" in status_lower:
            actions = [{
                "priority": 1,
                "action": "정확한 주소 확인 후 판매자에게 전달",
                "detail": "주소 수정 요청",
            }]
        elif "부재" in status_lower:
            actions = [{
                "priority": 1,
                "action": "택배 기사님 연락 또는 재배송 요청",
                "detail": "부재 시 배송 위치 지정 (경비실/문앞 등)",
            }]

    # Default action if none specific
    if not actions:
        actions.append({
            "priority": 1,
            "action": "택배사 고객센터 문의",
            "detail": f"전화: {carrier_contact}",
        })

    return actions


async def diagnose_problem(
    tracking_number: str,
    carrier: str = "auto"
) -> str:
    """
    Diagnose delivery issues and suggest solutions.

    This tool analyzes problematic deliveries (delays, issues, stagnation)
    and provides possible causes with recommended actions.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection

    Returns:
        Diagnosis with possible causes and recommended actions
    """
    tracking_number = normalize_tracking_number(tracking_number)

    if not tracking_number:
        return "운송장 번호를 입력해주세요."

    # Get tracking info
    if carrier.lower() == "auto":
        carrier_code = detect_carrier_from_tracking(tracking_number)
        if carrier_code:
            result = await sweet_tracker.track(tracking_number, carrier_code)
        else:
            result = await sweet_tracker.track_auto_detect(tracking_number)
    else:
        carrier_obj = get_carrier_by_name(carrier)
        if carrier_obj:
            result = await sweet_tracker.track(tracking_number, carrier_obj.code)
        else:
            result = await sweet_tracker.track_auto_detect(tracking_number)

    if not result.success:
        carrier_info = get_carrier_by_code(result.carrier_code) if result.carrier_code else None
        contact = carrier_info.contact if carrier_info else "해당 택배사"

        return (
            f"❌ 조회 실패\n\n"
            f"오류: {result.error_message}\n\n"
            f"💡 추천 액션:\n"
            f"1. 운송장 번호 재확인\n"
            f"2. 택배사 직접 문의: {contact}\n"
            f"3. 발송자(판매자)에게 확인 요청"
        )

    # Analyze the problem
    status_info = translate_status(result.current_status)
    stagnation = _analyze_stagnation(result.events, result.carrier_code)

    # Build output
    lines = []
    lines.append(f"🔍 배송 문제 진단: {tracking_number[:8]}...")
    lines.append("")

    # Current status
    lines.append(f"현재 상태: {status_info.emoji} {status_info.original}")
    lines.append(f"해석: {status_info.translated}")
    lines.append("")

    # Determine severity
    severity = "정상"
    if status_info.phase == DeliveryPhase.ISSUE:
        severity = "심각"
    elif stagnation["is_stagnant"]:
        if stagnation["days_stagnant"] >= 5:
            severity = "심각"
        elif stagnation["days_stagnant"] >= 3:
            severity = "주의"
        else:
            severity = "경미"

    severity_emoji = {"정상": "✅", "경미": "⚠️", "주의": "🟠", "심각": "🔴"}
    lines.append(f"심각도: {severity_emoji.get(severity, '❓')} {severity}")
    lines.append("")

    # Stagnation analysis
    if stagnation["is_stagnant"]:
        lines.append(f"📍 마지막 위치: {stagnation['last_location'] or '정보 없음'}")
        lines.append(f"⏱️ 정체 기간: {stagnation['days_stagnant']}일")
        lines.append("")

        if stagnation["possible_causes"]:
            lines.append("🔍 가능한 원인")
            for cause, probability in stagnation["possible_causes"]:
                bar_len = probability // 10
                bar = "█" * bar_len + "░" * (10 - bar_len)
                lines.append(f"  • {cause}")
                lines.append(f"    [{bar}] {probability}%")
            lines.append("")

    # Check for specific issues
    elif status_info.phase == DeliveryPhase.ISSUE:
        lines.append("⚠️ 문제 감지됨")
        lines.append(f"  {status_info.translated}")
        lines.append("")
    elif result.is_delivered:
        lines.append("✅ 정상 배송 완료")
        lines.append("  특별한 문제가 없습니다.")
        return "\n".join(lines)
    else:
        lines.append("✅ 정상 진행 중")
        lines.append("  현재 특별한 문제가 감지되지 않았습니다.")
        lines.append("")
        lines.append("💡 팁: 배송이 늦어지고 있다면 1-2일 더 기다려보세요.")
        lines.append("  물량이 많은 시기에는 정상보다 지연될 수 있어요.")
        return "\n".join(lines)

    # Recommended actions
    actions = _get_recommended_actions(result, status_info, stagnation)

    if actions:
        lines.append("🎯 추천 액션")
        for action in actions:
            lines.append(f"  {action['priority']}. {action['action']}")
            if action.get("detail"):
                lines.append(f"     → {action['detail']}")
        lines.append("")

    # Carrier contact
    carrier_info = get_carrier_by_code(result.carrier_code)
    if carrier_info:
        lines.append(f"📞 {carrier_info.name} 고객센터: {carrier_info.contact}")
        lines.append(f"🔗 온라인 문의: {carrier_info.website}")
        lines.append("")

    # Next step
    lines.append("💡 문의 템플릿이 필요하면 draft_inquiry 도구를 사용하세요.")

    return "\n".join(lines)
