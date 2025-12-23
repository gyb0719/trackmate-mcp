"""Korean delivery carrier information and contact details."""

from dataclasses import dataclass


@dataclass
class Carrier:
    """Delivery carrier information."""
    code: str
    name: str
    name_en: str
    contact: str
    website: str
    tracking_url: str


# Major Korean carriers with Sweet Tracker codes
CARRIERS: dict[str, Carrier] = {
    "04": Carrier(
        code="04",
        name="CJ대한통운",
        name_en="CJ Logistics",
        contact="1588-1255",
        website="https://www.cjlogistics.com",
        tracking_url="https://www.cjlogistics.com/ko/tool/parcel/tracking"
    ),
    "08": Carrier(
        code="08",
        name="롯데택배",
        name_en="Lotte Global Logistics",
        contact="1588-2121",
        website="https://www.lotteglogis.com",
        tracking_url="https://www.lotteglogis.com/home/reservation/tracking/index"
    ),
    "05": Carrier(
        code="05",
        name="한진택배",
        name_en="Hanjin Express",
        contact="1588-0011",
        website="https://www.hanjin.com",
        tracking_url="https://www.hanjin.com/kor/CMS/DeliveryMgr/WaybillResult.do"
    ),
    "01": Carrier(
        code="01",
        name="우체국택배",
        name_en="Korea Post",
        contact="1588-1300",
        website="https://www.epost.go.kr",
        tracking_url="https://service.epost.go.kr/trace.RetrieveDomRi498Trv.postal"
    ),
    "06": Carrier(
        code="06",
        name="로젠택배",
        name_en="Logen",
        contact="1588-9988",
        website="https://www.ilogen.com",
        tracking_url="https://www.ilogen.com/web/delivery/tracking"
    ),
    "11": Carrier(
        code="11",
        name="일양로지스",
        name_en="Ilyang Logis",
        contact="1588-0002",
        website="https://www.ilyanglogis.com",
        tracking_url="https://www.ilyanglogis.com/functionality/tracking.asp"
    ),
    "23": Carrier(
        code="23",
        name="경동택배",
        name_en="Kyungdong Express",
        contact="1899-5368",
        website="https://kdexp.com",
        tracking_url="https://kdexp.com/service/delivery"
    ),
    "46": Carrier(
        code="46",
        name="CU편의점택배",
        name_en="CU CVS Delivery",
        contact="1566-1025",
        website="https://www.cupost.co.kr",
        tracking_url="https://www.cupost.co.kr/tracking.cupost"
    ),
    "24": Carrier(
        code="24",
        name="대신택배",
        name_en="Daesin",
        contact="043-222-4582",
        website="https://www.ds3211.com",
        tracking_url="https://www.ds3211.com/freight/internalFreightSearch.ht"
    ),
    "22": Carrier(
        code="22",
        name="대한통운",
        name_en="Korea Express",
        contact="1588-1255",
        website="https://www.cjlogistics.com",
        tracking_url="https://www.cjlogistics.com/ko/tool/parcel/tracking"
    ),
}

# Carrier name aliases for auto-detection
CARRIER_ALIASES: dict[str, str] = {
    "cj대한통운": "04",
    "cj택배": "04",
    "대한통운": "04",
    "씨제이대한통운": "04",
    "롯데택배": "08",
    "롯데글로벌로지스": "08",
    "롯데": "08",
    "한진택배": "05",
    "한진": "05",
    "우체국": "01",
    "우체국택배": "01",
    "우편": "01",
    "로젠택배": "06",
    "로젠": "06",
    "일양로지스": "11",
    "일양": "11",
    "경동택배": "23",
    "경동": "23",
    "cu택배": "46",
    "cu편의점": "46",
    "씨유택배": "46",
    "대신택배": "24",
    "대신": "24",
}


def get_carrier_by_code(code: str) -> Carrier | None:
    """Get carrier information by Sweet Tracker code."""
    return CARRIERS.get(code)


def get_carrier_by_name(name: str) -> Carrier | None:
    """Get carrier information by name (supports aliases)."""
    name_lower = name.lower().replace(" ", "")
    code = CARRIER_ALIASES.get(name_lower)
    if code:
        return CARRIERS.get(code)
    return None


def detect_carrier_from_tracking(tracking_number: str) -> str | None:
    """
    Attempt to detect carrier from tracking number pattern.
    Returns Sweet Tracker carrier code or None.

    Note: Pattern matching is not 100% reliable.
    When detection fails, track_auto_detect will try multiple carriers.
    """
    # CJ대한통운: starts with 6, 12-13 digits (most reliable)
    if tracking_number.startswith("6") and len(tracking_number) in [12, 13]:
        return "04"

    # 우체국: 13 digits (reliable)
    if len(tracking_number) == 13 and tracking_number.isdigit():
        return "01"

    # 로젠택배: 11 digits (reliable)
    if len(tracking_number) == 11 and tracking_number.isdigit():
        return "06"

    # 12자리 숫자는 여러 택배사가 사용하므로 auto-detect에 맡김
    # (CJ대한통운, 한진택배, 롯데택배 등이 모두 12자리 사용)

    return None


def get_all_carriers() -> list[Carrier]:
    """Get all supported carriers."""
    return list(CARRIERS.values())
