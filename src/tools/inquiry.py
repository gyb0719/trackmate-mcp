"""draft_inquiry tool - Generate customer service inquiry templates."""

from src.services.sweet_tracker import sweet_tracker
from src.services.carrier_info import (
    detect_carrier_from_tracking,
    get_carrier_by_code,
    get_carrier_by_name,
)
from src.utils.status_translator import translate_status, DeliveryPhase
from src.utils.tracking_parser import normalize_tracking_number


def _generate_carrier_inquiry(
    tracking_number: str,
    carrier_name: str,
    issue_type: str,
    last_location: str | None,
    days_stagnant: int | None,
) -> str:
    """Generate inquiry template for carrier customer service."""

    templates = {
        "stagnant": f"""안녕하세요. 배송 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

{days_stagnant or '며칠'}일 전부터 '{last_location or '마지막 위치'}'에서 배송 상태가 업데이트되지 않고 있습니다.

현재 배송 상황 확인 부탁드립니다.
분실이나 누락된 것은 아닌지 확인해주시면 감사하겠습니다.

감사합니다.""",

        "delay": f"""안녕하세요. 배송 지연 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

배송이 예상보다 많이 지연되고 있어 문의드립니다.
현재 정확한 배송 상황과 예상 도착일을 알려주시면 감사하겠습니다.

감사합니다.""",

        "return": f"""안녕하세요. 반송 관련 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

배송 상태가 '반송'으로 확인됩니다.
반송 사유를 알려주시면 감사하겠습니다.

수령 가능한 상황이오니, 재배송이 가능한지 확인 부탁드립니다.

감사합니다.""",

        "address": f"""안녕하세요. 주소 관련 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

주소 불명확으로 배송이 중단된 것으로 확인됩니다.

정확한 주소는 다음과 같습니다:
[여기에 정확한 주소를 입력해주세요]

확인 후 배송 진행 부탁드립니다.

감사합니다.""",

        "general": f"""안녕하세요. 배송 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

배송 현황 확인 부탁드립니다.

감사합니다.""",
    }

    return templates.get(issue_type, templates["general"])


def _generate_seller_inquiry(
    tracking_number: str,
    carrier_name: str,
    issue_type: str,
    days_stagnant: int | None,
) -> str:
    """Generate inquiry template for seller."""

    templates = {
        "stagnant": f"""안녕하세요. 배송 확인 요청드립니다.

주문하신 상품의 배송이 {days_stagnant or '며칠'}일째 진행되지 않고 있습니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

택배사 확인 후 상황 공유 부탁드립니다.
분실된 경우 재발송 또는 환불 처리 요청드립니다.

감사합니다.""",

        "return": f"""안녕하세요. 반송 관련 문의드립니다.

배송 조회 결과 상품이 반송 처리된 것으로 확인됩니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

반송 사유 확인 후 재발송 부탁드립니다.
제 주소와 연락처는 정확히 입력되어 있습니다.

감사합니다.""",

        "delay": f"""안녕하세요. 배송 지연 문의드립니다.

주문한 상품 배송이 예상보다 많이 지연되고 있습니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

택배사에 확인 요청 부탁드립니다.

감사합니다.""",

        "general": f"""안녕하세요. 배송 관련 문의드립니다.

운송장 번호: {tracking_number}
택배사: {carrier_name}

배송 상황 확인 부탁드립니다.

감사합니다.""",
    }

    return templates.get(issue_type, templates["general"])


async def draft_inquiry(
    tracking_number: str,
    carrier: str = "auto",
    inquiry_type: str = "auto"
) -> str:
    """
    Generate customer service inquiry templates for delivery issues.

    This tool creates ready-to-use inquiry templates for both the carrier
    and the seller, based on the current delivery status and issues.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection
        inquiry_type: Type of inquiry - "carrier" (택배사), "seller" (판매자),
                     or "auto" (both based on situation)

    Returns:
        Ready-to-use inquiry templates
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

    # Determine issue type from status
    issue_type = "general"
    days_stagnant = None
    last_location = None

    if result.success:
        status_info = translate_status(result.current_status)

        # Check for specific issues
        status_lower = result.current_status.lower()
        if "반송" in status_lower:
            issue_type = "return"
        elif "주소" in status_lower:
            issue_type = "address"
        elif status_info.phase == DeliveryPhase.ISSUE:
            issue_type = "delay"

        # Check stagnation
        if result.events:
            last_event = result.events[-1]
            last_location = last_event.location

            # Simple stagnation check
            try:
                from datetime import datetime
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M"]:
                    try:
                        last_time = datetime.strptime(last_event.time, fmt)
                        days_stagnant = (datetime.now() - last_time).days
                        if days_stagnant >= 2:
                            issue_type = "stagnant"
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

    carrier_name = result.carrier_name if result.success else "택배사"
    carrier_info = get_carrier_by_code(result.carrier_code) if result.carrier_code else None

    # Build output
    lines = []
    lines.append(f"📝 문의 템플릿 생성: {tracking_number[:8]}...")
    lines.append("")

    # Carrier inquiry
    if inquiry_type in ["auto", "carrier"]:
        lines.append("=" * 50)
        lines.append("📞 택배사 문의용 템플릿")
        lines.append("=" * 50)
        if carrier_info:
            lines.append(f"연락처: {carrier_info.contact}")
            lines.append(f"웹사이트: {carrier_info.website}")
        lines.append("")
        lines.append("--- 아래 내용을 복사해서 사용하세요 ---")
        lines.append("")
        lines.append(_generate_carrier_inquiry(
            tracking_number,
            carrier_name,
            issue_type,
            last_location,
            days_stagnant
        ))
        lines.append("")

    # Seller inquiry
    if inquiry_type in ["auto", "seller"]:
        lines.append("=" * 50)
        lines.append("🏪 판매자 문의용 템플릿")
        lines.append("=" * 50)
        lines.append("(쇼핑몰/마켓 문의 게시판에 사용)")
        lines.append("")
        lines.append("--- 아래 내용을 복사해서 사용하세요 ---")
        lines.append("")
        lines.append(_generate_seller_inquiry(
            tracking_number,
            carrier_name,
            issue_type,
            days_stagnant
        ))
        lines.append("")

    # Tips
    lines.append("=" * 50)
    lines.append("💡 문의 팁")
    lines.append("=" * 50)
    lines.append("• 택배사 문의 시 운송장 번호를 정확히 전달하세요")
    lines.append("• 판매자 문의 시 주문번호도 함께 알려주면 좋아요")
    lines.append("• 5일 이상 지연 시 분실 가능성도 언급하세요")
    lines.append("• 답변이 없으면 다른 채널(전화/채팅)로 재문의하세요")

    return "\n".join(lines)
