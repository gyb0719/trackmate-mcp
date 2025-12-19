"""TrackMate MCP Server - Smart delivery tracking assistant."""

from fastmcp import FastMCP

from src.tools.parse import parse_tracking
from src.tools.track import track_package, my_packages
from src.tools.predict import predict_arrival
from src.tools.diagnose import diagnose_problem
from src.tools.inquiry import draft_inquiry

# Create MCP server
mcp = FastMCP(
    name="TrackMate",
    instructions="택배 추적부터 문제 해결까지, AI가 알아서 챙겨주는 스마트 배송 비서. "
                 "배송 상태를 일상 언어로 번역하고, 문제 발생 시 해결책을 제안합니다."
)


# Register tools
@mcp.tool()
async def tool_parse_tracking(text: str) -> str:
    """
    Extract tracking number from natural language text.

    Analyzes input text (SMS, chat message, etc.) and extracts tracking
    numbers along with carrier information when available.

    Args:
        text: Input text containing tracking information
              (e.g., "[CJ대한통운] 운송장번호 640123456789")

    Returns:
        Extracted tracking information with carrier details
    """
    return await parse_tracking(text)


@mcp.tool()
async def tool_track_package(tracking_number: str, carrier: str = "auto") -> str:
    """
    Track a delivery package and get status in plain Korean.

    Looks up delivery status and translates technical carrier terms
    (like "SM입고", "간선상차") into everyday language.

    Args:
        tracking_number: The tracking/invoice number (운송장 번호)
        carrier: Carrier name or "auto" for automatic detection
                 Examples: "CJ대한통운", "롯데택배", "한진", "우체국"

    Returns:
        Delivery status with timeline, translated to user-friendly Korean
    """
    return await track_package(tracking_number, carrier)


@mcp.tool()
async def tool_my_packages(tracking_numbers: str) -> str:
    """
    Track multiple packages at once and get a prioritized summary.

    Tracks several packages simultaneously and organizes them by priority
    (urgent items first, issues highlighted).

    Args:
        tracking_numbers: Comma-separated tracking numbers
                         (e.g., "640123456789, 234567890123")

    Returns:
        Summary of all packages with priority ordering
    """
    return await my_packages(tracking_numbers)


@mcp.tool()
async def tool_predict_arrival(
    tracking_number: str,
    carrier: str = "auto",
    schedule: str = ""
) -> str:
    """
    Predict when a package will arrive.

    Analyzes delivery status and provides estimated arrival time.
    Can also check for schedule conflicts if you provide your schedule.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection
        schedule: Optional schedule for conflict checking
                  (e.g., "오후 3시 회의", "저녁에 외출")

    Returns:
        Arrival prediction with time window and recommendations
    """
    return await predict_arrival(tracking_number, carrier, schedule)


@mcp.tool()
async def tool_diagnose_problem(tracking_number: str, carrier: str = "auto") -> str:
    """
    Diagnose delivery issues and suggest solutions.

    Analyzes problematic deliveries (delays, stagnation, issues) and
    provides possible causes with recommended actions.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection

    Returns:
        Diagnosis with possible causes and recommended actions
    """
    return await diagnose_problem(tracking_number, carrier)


@mcp.tool()
async def tool_draft_inquiry(
    tracking_number: str,
    carrier: str = "auto",
    inquiry_type: str = "auto"
) -> str:
    """
    Generate customer service inquiry templates.

    Creates ready-to-use inquiry templates for both the carrier and
    the seller, based on the current delivery status and issues.

    Args:
        tracking_number: The tracking/invoice number
        carrier: Carrier name or "auto" for automatic detection
        inquiry_type: "carrier" (택배사), "seller" (판매자), or "auto" (both)

    Returns:
        Ready-to-use inquiry templates
    """
    return await draft_inquiry(tracking_number, carrier, inquiry_type)


def main():
    """Run the MCP server."""
    import os

    # Use streamable-http transport for web deployment, stdio for local
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport in ["sse", "streamable-http", "http"]:
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", 8000))
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
