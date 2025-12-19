"""predict_arrival tool - Estimate delivery arrival time."""

from datetime import datetime, timedelta

from src.services.sweet_tracker import sweet_tracker
from src.services.carrier_info import detect_carrier_from_tracking, get_carrier_by_code
from src.utils.status_translator import translate_status, DeliveryPhase
from src.utils.tracking_parser import normalize_tracking_number


# Average delivery times by carrier (in hours from pickup)
CARRIER_AVG_HOURS = {
    "04": 36,   # CJ대한통운
    "08": 36,   # 롯데택배
    "05": 36,   # 한진택배
    "01": 48,   # 우체국
    "06": 42,   # 로젠택배
    "default": 48
}

# Rush hours when deliveries typically arrive
DELIVERY_HOURS = {
    "morning": (9, 12),     # 오전
    "afternoon": (14, 18),  # 오후
    "evening": (18, 21),    # 저녁
}


def _estimate_arrival_time(
    status_info,
    carrier_code: str,
    events: list
) -> dict:
    """Calculate estimated arrival time based on current status and patterns."""

    now = datetime.now()
    result = {
        "estimated_date": None,
        "time_window": None,
        "confidence": "낮음",
        "basis": [],
    }

    # If already delivered
    if status_info.is_final and status_info.phase == DeliveryPhase.DELIVERED:
        return {
            "estimated_date": "배송 완료",
            "time_window": None,
            "confidence": "확정",
            "basis": ["이미 배송이 완료되었습니다"],
        }

    # If there's an issue
    if status_info.phase == DeliveryPhase.ISSUE:
        return {
            "estimated_date": "확인 필요",
            "time_window": None,
            "confidence": "낮음",
            "basis": ["배송에 문제가 발생했습니다. 택배사 문의가 필요합니다."],
        }

    # Calculate based on estimated hours
    est_hours = status_info.estimated_hours

    if est_hours is not None:
        if est_hours <= 3:
            # Arriving very soon
            result["estimated_date"] = "오늘"
            result["time_window"] = "곧 도착"
            result["confidence"] = "높음"
            result["basis"].append("배송 기사님이 배달 중입니다")
        elif est_hours <= 6:
            # Today
            result["estimated_date"] = "오늘"
            if now.hour < 12:
                result["time_window"] = "오후 2-6시"
            else:
                result["time_window"] = "저녁 6-9시"
            result["confidence"] = "중간"
            result["basis"].append("오늘 중 도착 예상")
        elif est_hours <= 24:
            # Tomorrow
            tomorrow = now + timedelta(days=1)
            result["estimated_date"] = tomorrow.strftime("%m월 %d일")
            result["time_window"] = "오후"
            result["confidence"] = "중간"
            result["basis"].append("내일 도착 예상")
        else:
            # 2+ days
            days = est_hours // 24
            future = now + timedelta(days=days)
            result["estimated_date"] = future.strftime("%m월 %d일")
            result["time_window"] = "오후"
            result["confidence"] = "낮음"
            result["basis"].append(f"약 {days}일 후 도착 예상")

    # Add carrier average as reference
    avg_hours = CARRIER_AVG_HOURS.get(carrier_code, CARRIER_AVG_HOURS["default"])
    result["basis"].append(f"이 택배사 평균 배송 시간: {avg_hours // 24}일")

    return result


async def predict_arrival(
    tracking_number: str,
    carrier: str = "auto",
    schedule: str = ""
) -> str:
    """
    Predict when a package will arrive based on current status and patterns.

    This tool analyzes the delivery status and provides an estimated arrival
    time. If you provide your schedule, it can also warn about conflicts.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection
        schedule: Optional - your schedule for conflict checking
                  (e.g., "오후 3시 회의", "저녁에 외출")

    Returns:
        Arrival prediction with time window and recommendations
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
        from src.services.carrier_info import get_carrier_by_name
        carrier_obj = get_carrier_by_name(carrier)
        if carrier_obj:
            result = await sweet_tracker.track(tracking_number, carrier_obj.code)
        else:
            result = await sweet_tracker.track_auto_detect(tracking_number)

    if not result.success:
        return (
            f"❌ 조회 실패: {result.error_message}\n\n"
            "도착 예측을 위해서는 먼저 배송 조회가 필요해요."
        )

    # Translate status and predict
    status_info = translate_status(result.current_status)
    prediction = _estimate_arrival_time(
        status_info,
        result.carrier_code,
        result.events
    )

    # Build output
    lines = []
    lines.append(f"🕐 도착 예측: {result.tracking_number[:8]}...")
    lines.append("")

    # Current status
    lines.append(f"현재 상태: {status_info.emoji} {status_info.translated}")
    lines.append("")

    # Prediction
    lines.append("📅 예상 도착")
    if prediction["estimated_date"]:
        lines.append(f"  날짜: {prediction['estimated_date']}")
    if prediction["time_window"]:
        lines.append(f"  시간대: {prediction['time_window']}")
    lines.append(f"  신뢰도: {prediction['confidence']}")
    lines.append("")

    # Basis
    if prediction["basis"]:
        lines.append("📊 예측 근거")
        for basis in prediction["basis"]:
            lines.append(f"  • {basis}")
        lines.append("")

    # Schedule conflict check
    if schedule:
        lines.append("📋 일정 확인")
        lines.append(f"  입력하신 일정: {schedule}")

        # Simple conflict detection
        conflict = False
        schedule_lower = schedule.lower()

        if prediction["time_window"]:
            if "오후" in prediction["time_window"]:
                if "오후" in schedule_lower or "3시" in schedule_lower or "4시" in schedule_lower:
                    conflict = True
            if "저녁" in prediction["time_window"]:
                if "저녁" in schedule_lower or "6시" in schedule_lower or "7시" in schedule_lower:
                    conflict = True

        if conflict:
            lines.append("  ⚠️ 일정과 겹칠 수 있어요!")
            lines.append("")
            lines.append("💡 추천")
            lines.append("  • 경비실/무인택배함 배송 요청")
            lines.append("  • 문 앞 배송 요청")
            lines.append("  • 택배 기사님께 연락")
        else:
            lines.append("  ✅ 일정 충돌 없음")
        lines.append("")

    # Recommendations
    if status_info.phase == DeliveryPhase.OUT_FOR_DELIVERY:
        lines.append("💡 오늘 배송 예정이에요!")
        lines.append("  부재 시 경비실/문앞 배송을 요청하세요.")
    elif status_info.phase == DeliveryPhase.ISSUE:
        lines.append("💡 배송에 문제가 있어요")
        lines.append("  diagnose_problem 도구로 상세 분석을 확인하세요.")

    return "\n".join(lines)
