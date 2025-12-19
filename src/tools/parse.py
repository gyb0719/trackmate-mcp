"""parse_tracking tool - Extract tracking numbers from natural language."""

from src.utils.tracking_parser import parse_tracking_input, validate_tracking_number
from src.services.carrier_info import get_all_carriers


async def parse_tracking(text: str) -> str:
    """
    Extract tracking number from natural language text (SMS, chat message, etc.)

    This tool analyzes the input text and extracts tracking numbers along with
    carrier information when available. Useful for processing delivery
    notification messages from carriers.

    Args:
        text: The input text containing tracking information
              (e.g., SMS message, chat content, or just the tracking number)

    Returns:
        Extracted tracking information in a formatted string
    """
    if not text or not text.strip():
        return "텍스트를 입력해주세요."

    # Parse the input
    results = parse_tracking_input(text)

    if not results:
        # No tracking numbers found - provide guidance
        carriers = get_all_carriers()
        carrier_list = ", ".join([c.name for c in carriers[:5]])
        return (
            "운송장 번호를 찾을 수 없어요.\n\n"
            "다음과 같은 형식으로 입력해주세요:\n"
            "• 운송장 번호만: 640123456789\n"
            "• 택배사 포함: [CJ대한통운] 운송장번호 640123456789\n"
            "• SMS 전체 붙여넣기도 가능해요\n\n"
            f"지원 택배사: {carrier_list} 등"
        )

    # Format results
    output_lines = []

    for i, parsed in enumerate(results, 1):
        if len(results) > 1:
            output_lines.append(f"📦 운송장 #{i}")
        else:
            output_lines.append("📦 추출된 운송장 정보")

        output_lines.append(f"• 운송장 번호: {parsed.tracking_number}")

        if parsed.carrier_name:
            output_lines.append(f"• 택배사: {parsed.carrier_name}")
        elif parsed.carrier_code:
            output_lines.append(f"• 택배사 코드: {parsed.carrier_code}")
        else:
            output_lines.append("• 택배사: 자동 감지 필요")

        confidence_text = "높음" if parsed.confidence > 0.7 else "중간" if parsed.confidence > 0.4 else "낮음"
        output_lines.append(f"• 신뢰도: {confidence_text}")
        output_lines.append(f"• 추출 방법: {parsed.source}")

        if not validate_tracking_number(parsed.tracking_number):
            output_lines.append("⚠️ 번호 형식이 일반적이지 않아요. 확인해주세요.")

        output_lines.append("")

    # Add next step guidance
    if results:
        best = results[0]
        if best.carrier_code:
            output_lines.append(
                f"💡 track_package 도구로 '{best.tracking_number}' 배송 조회를 할 수 있어요."
            )
        else:
            output_lines.append(
                "💡 택배사를 알려주시면 더 정확한 조회가 가능해요."
            )

    return "\n".join(output_lines)
