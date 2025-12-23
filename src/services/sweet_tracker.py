"""Sweet Tracker API client for delivery tracking."""

import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from src.config import config
from src.services.carrier_info import get_carrier_by_code, CARRIERS


# Mock data for testing without API key
MOCK_ENABLED = not config.SWEET_TRACKER_API_KEY


@dataclass
class TrackingEvent:
    """Single tracking event in delivery history."""
    time: str
    status: str
    location: str
    detail: str | None = None


@dataclass
class TrackingResult:
    """Complete tracking result from API."""
    success: bool
    tracking_number: str
    carrier_code: str
    carrier_name: str
    sender: str | None
    receiver: str | None
    item_name: str | None
    events: list[TrackingEvent]
    current_status: str
    is_delivered: bool
    error_message: str | None = None


def _generate_mock_result(tracking_number: str, carrier_code: str) -> TrackingResult:
    """Generate mock tracking result for testing."""
    carrier = get_carrier_by_code(carrier_code)
    carrier_name = carrier.name if carrier else f"택배사 {carrier_code}"

    # Generate realistic mock timeline
    now = datetime.now()
    scenarios = [
        # Scenario 1: In transit
        {
            "events": [
                TrackingEvent(time=(now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), status="집화처리", location="서울 강남구", detail="상품인수"),
                TrackingEvent(time=(now - timedelta(days=1, hours=18)).strftime("%Y-%m-%d %H:%M"), status="간선상차", location="서울 HUB", detail="간선상차"),
                TrackingEvent(time=(now - timedelta(days=1, hours=6)).strftime("%Y-%m-%d %H:%M"), status="간선하차", location="부산 HUB", detail="간선하차"),
                TrackingEvent(time=(now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"), status="SM입고", location="부산 해운대구", detail="배송기사인수"),
            ],
            "current_status": "SM입고",
            "is_delivered": False,
        },
        # Scenario 2: Out for delivery
        {
            "events": [
                TrackingEvent(time=(now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), status="집화처리", location="서울 송파구", detail="상품인수"),
                TrackingEvent(time=(now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"), status="간선상차", location="서울 HUB", detail="간선상차"),
                TrackingEvent(time=(now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"), status="간선하차", location="서울 강남 HUB", detail="간선하차"),
                TrackingEvent(time=(now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), status="SM입고", location="서울 강남구", detail="배송기사인수"),
                TrackingEvent(time=(now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"), status="배달출발", location="서울 강남구", detail="배달출발"),
            ],
            "current_status": "배달출발",
            "is_delivered": False,
        },
        # Scenario 3: Delivered
        {
            "events": [
                TrackingEvent(time=(now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), status="집화처리", location="경기 수원시", detail="상품인수"),
                TrackingEvent(time=(now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), status="간선상차", location="수원 HUB", detail="간선상차"),
                TrackingEvent(time=(now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"), status="SM입고", location="서울 마포구", detail="배송기사인수"),
                TrackingEvent(time=(now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"), status="배달출발", location="서울 마포구", detail="배달출발"),
                TrackingEvent(time=(now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), status="배달완료", location="서울 마포구", detail="배달완료"),
            ],
            "current_status": "배달완료",
            "is_delivered": True,
        },
        # Scenario 4: Stagnant (for testing diagnose)
        {
            "events": [
                TrackingEvent(time=(now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"), status="집화처리", location="서울 영등포구", detail="상품인수"),
                TrackingEvent(time=(now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"), status="간선상차", location="서울 HUB", detail="간선상차"),
                TrackingEvent(time=(now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), status="간선하차", location="부산 HUB", detail="간선하차"),
            ],
            "current_status": "간선하차",
            "is_delivered": False,
        },
    ]

    # Select scenario based on tracking number hash
    scenario_idx = hash(tracking_number) % len(scenarios)
    scenario = scenarios[scenario_idx]

    return TrackingResult(
        success=True,
        tracking_number=tracking_number,
        carrier_code=carrier_code,
        carrier_name=carrier_name,
        sender="테스트 판매자",
        receiver="테스트 고객",
        item_name="테스트 상품",
        events=scenario["events"],
        current_status=scenario["current_status"],
        is_delivered=scenario["is_delivered"],
    )


class SweetTrackerClient:
    """Client for Sweet Tracker API."""

    def __init__(self):
        self.api_key = config.SWEET_TRACKER_API_KEY
        self.base_url = config.SWEET_TRACKER_BASE_URL
        self.timeout = config.REQUEST_TIMEOUT
        self.mock_mode = MOCK_ENABLED

        if self.mock_mode:
            print("[TrackMate] Mock mode enabled (no API key). Using simulated data.")

    async def get_company_list(self) -> list[dict]:
        """Get list of supported carriers."""
        url = f"{self.base_url}/companylist"
        params = {"t_key": self.api_key}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "Company" in data:
                return data["Company"]
            return []

    async def track(
        self,
        tracking_number: str,
        carrier_code: str
    ) -> TrackingResult:
        """
        Track a package by tracking number and carrier code.

        Args:
            tracking_number: The tracking/invoice number
            carrier_code: Sweet Tracker carrier code (e.g., "04" for CJ)

        Returns:
            TrackingResult with delivery information
        """
        # Return mock data if mock mode enabled
        if self.mock_mode:
            return _generate_mock_result(tracking_number, carrier_code)

        url = f"{self.base_url}/trackingInfo"
        params = {
            "t_key": self.api_key,
            "t_code": carrier_code,
            "t_invoice": tracking_number
        }

        carrier = get_carrier_by_code(carrier_code)
        carrier_name = carrier.name if carrier else f"택배사 {carrier_code}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Check for API error
                if data.get("status") == "false" or "msg" in data:
                    return TrackingResult(
                        success=False,
                        tracking_number=tracking_number,
                        carrier_code=carrier_code,
                        carrier_name=carrier_name,
                        sender=None,
                        receiver=None,
                        item_name=None,
                        events=[],
                        current_status="조회 실패",
                        is_delivered=False,
                        error_message=data.get("msg", "조회에 실패했습니다")
                    )

                # Parse tracking info
                events = []
                tracking_details = data.get("trackingDetails", [])

                for detail in tracking_details:
                    events.append(TrackingEvent(
                        time=detail.get("timeString", ""),
                        status=detail.get("kind", ""),
                        location=detail.get("where", ""),
                        detail=detail.get("remark")
                    ))

                # Determine current status
                current_status = "정보 없음"
                is_delivered = False

                if events:
                    current_status = events[-1].status
                    # Check if delivered
                    last_status = current_status.lower()
                    if "완료" in last_status or "배달" in last_status and "출발" not in last_status:
                        is_delivered = True

                # Also check the completeYN field if available
                if data.get("completeYN") == "Y":
                    is_delivered = True

                return TrackingResult(
                    success=True,
                    tracking_number=tracking_number,
                    carrier_code=carrier_code,
                    carrier_name=carrier_name,
                    sender=data.get("senderName"),
                    receiver=data.get("receiverName"),
                    item_name=data.get("itemName"),
                    events=events,
                    current_status=current_status,
                    is_delivered=is_delivered
                )

        except httpx.HTTPStatusError as e:
            return TrackingResult(
                success=False,
                tracking_number=tracking_number,
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                sender=None,
                receiver=None,
                item_name=None,
                events=[],
                current_status="조회 실패",
                is_delivered=False,
                error_message=f"API 오류: {e.response.status_code}"
            )
        except httpx.TimeoutException:
            return TrackingResult(
                success=False,
                tracking_number=tracking_number,
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                sender=None,
                receiver=None,
                item_name=None,
                events=[],
                current_status="조회 실패",
                is_delivered=False,
                error_message="API 응답 시간 초과"
            )
        except Exception as e:
            return TrackingResult(
                success=False,
                tracking_number=tracking_number,
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                sender=None,
                receiver=None,
                item_name=None,
                events=[],
                current_status="조회 실패",
                is_delivered=False,
                error_message=f"오류 발생: {str(e)}"
            )

    async def track_auto_detect(self, tracking_number: str) -> TrackingResult:
        """
        Track a package with automatic carrier detection.
        Tries multiple carriers until one succeeds.
        """
        from src.services.carrier_info import detect_carrier_from_tracking

        # Return mock data if mock mode enabled
        if self.mock_mode:
            detected_code = detect_carrier_from_tracking(tracking_number)
            return _generate_mock_result(tracking_number, detected_code or "04")

        # Try auto-detection first
        detected_code = detect_carrier_from_tracking(tracking_number)
        if detected_code:
            result = await self.track(tracking_number, detected_code)
            if result.success:
                return result

        # Try major carriers
        major_carriers = ["04", "08", "05", "01", "06"]  # CJ, 롯데, 한진, 우체국, 로젠
        for code in major_carriers:
            if code == detected_code:
                continue  # Already tried
            result = await self.track(tracking_number, code)
            if result.success:
                return result

        # Return last failed result
        return TrackingResult(
            success=False,
            tracking_number=tracking_number,
            carrier_code="",
            carrier_name="알 수 없음",
            sender=None,
            receiver=None,
            item_name=None,
            events=[],
            current_status="조회 실패",
            is_delivered=False,
            error_message="택배사를 찾을 수 없습니다. 택배사를 직접 지정해주세요."
        )


# Singleton instance
sweet_tracker = SweetTrackerClient()
