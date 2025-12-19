"""Tracking number parser - extracts tracking numbers from natural language text."""

import re
from dataclasses import dataclass

from src.services.carrier_info import (
    CARRIER_ALIASES,
    detect_carrier_from_tracking,
    get_carrier_by_code,
    get_carrier_by_name,
)


@dataclass
class ParsedTracking:
    """Parsed tracking information."""
    tracking_number: str
    carrier_code: str | None
    carrier_name: str | None
    confidence: float  # 0.0 to 1.0
    source: str  # 추출 방법 설명


def normalize_tracking_number(raw: str) -> str:
    """Normalize tracking number by removing common separators."""
    # Remove spaces, dashes, and other common separators
    normalized = re.sub(r"[\s\-_.]", "", raw)
    return normalized


def extract_tracking_numbers(text: str) -> list[str]:
    """
    Extract potential tracking numbers from text.
    Returns list of candidate tracking numbers.
    """
    candidates = []

    # Pattern 1: Explicit "운송장" or "송장" mention followed by number
    explicit_patterns = [
        r"운송장\s*(?:번호)?[:\s]*([0-9\-\s]{10,20})",
        r"송장\s*(?:번호)?[:\s]*([0-9\-\s]{10,20})",
        r"invoice[:\s]*([0-9\-\s]{10,20})",
        r"tracking[:\s]*([0-9\-\s]{10,20})",
    ]

    for pattern in explicit_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            normalized = normalize_tracking_number(match)
            if 10 <= len(normalized) <= 15:
                candidates.append(normalized)

    # Pattern 2: Standalone number sequences (10-14 digits)
    number_pattern = r"\b([0-9]{10,14})\b"
    matches = re.findall(number_pattern, text)
    for match in matches:
        if match not in candidates:
            candidates.append(match)

    # Pattern 3: Numbers with dashes (e.g., 6401-2345-6789)
    dash_pattern = r"\b(\d{3,5}[\-\s]\d{3,5}[\-\s]\d{3,5})\b"
    matches = re.findall(dash_pattern, text)
    for match in matches:
        normalized = normalize_tracking_number(match)
        if normalized not in candidates and 10 <= len(normalized) <= 15:
            candidates.append(normalized)

    return candidates


def extract_carrier_name(text: str) -> str | None:
    """Extract carrier name from text."""
    text_lower = text.lower()

    # Check for carrier name mentions
    for alias in CARRIER_ALIASES.keys():
        if alias in text_lower:
            return alias

    # Common carrier mention patterns
    carrier_patterns = [
        r"\[([\w\s]+)\]",  # [CJ대한통운]
        r"([\w]+택배)",     # XX택배
        r"([\w]+로지스)",   # XX로지스
    ]

    for pattern in carrier_patterns:
        match = re.search(pattern, text)
        if match:
            carrier_text = match.group(1).lower().replace(" ", "")
            if carrier_text in CARRIER_ALIASES:
                return carrier_text

    return None


def parse_tracking_input(text: str) -> list[ParsedTracking]:
    """
    Parse user input to extract tracking information.

    Args:
        text: User input text (can be a message, SMS content, etc.)

    Returns:
        List of ParsedTracking objects with extracted information
    """
    results = []

    # Extract carrier name if mentioned
    mentioned_carrier = extract_carrier_name(text)
    carrier_code = None
    carrier_name = None

    if mentioned_carrier:
        carrier = get_carrier_by_name(mentioned_carrier)
        if carrier:
            carrier_code = carrier.code
            carrier_name = carrier.name

    # Extract tracking numbers
    candidates = extract_tracking_numbers(text)

    for tracking_num in candidates:
        # Determine carrier if not already known
        if not carrier_code:
            detected_code = detect_carrier_from_tracking(tracking_num)
            if detected_code:
                carrier = get_carrier_by_code(detected_code)
                if carrier:
                    carrier_code = carrier.code
                    carrier_name = carrier.name

        # Calculate confidence
        confidence = 0.5  # Base confidence

        # Boost confidence based on factors
        if 11 <= len(tracking_num) <= 13:
            confidence += 0.2  # Common length
        if carrier_code:
            confidence += 0.2  # Carrier detected
        if "운송장" in text or "송장" in text:
            confidence += 0.1  # Explicit mention

        confidence = min(confidence, 1.0)

        # Determine source description
        if "운송장" in text or "송장" in text:
            source = "운송장 번호 명시에서 추출"
        elif mentioned_carrier:
            source = f"{carrier_name or mentioned_carrier} 문자에서 추출"
        else:
            source = "텍스트에서 숫자 패턴으로 추출"

        results.append(ParsedTracking(
            tracking_number=tracking_num,
            carrier_code=carrier_code,
            carrier_name=carrier_name,
            confidence=confidence,
            source=source
        ))

    return results


def validate_tracking_number(tracking_number: str) -> bool:
    """
    Validate tracking number format.
    Returns True if the number looks like a valid tracking number.
    """
    # Basic validation
    if not tracking_number:
        return False

    # Should be mostly digits
    if not tracking_number.isdigit():
        return False

    # Length check (Korean carriers use 10-14 digits)
    if not (10 <= len(tracking_number) <= 14):
        return False

    return True
