"""Configuration for TrackMate MCP."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    SWEET_TRACKER_API_KEY: str = os.getenv("SWEET_TRACKER_API_KEY", "")
    SWEET_TRACKER_BASE_URL: str = "http://info.sweettracker.co.kr/api/v1"

    REQUEST_TIMEOUT: int = 30
    MAX_RESPONSE_SIZE: int = 20000  # 20k safe margin (PlayMCP limit: 24k)

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.SWEET_TRACKER_API_KEY:
            return False
        return True


config = Config()
