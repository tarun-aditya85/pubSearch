"""Configuration settings for pubSearch audit engine."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "pubSearch"
    app_version: str = "1.0.0"

    # User-Agent for ethical scanning
    user_agent: str = "pubSearch-Audit-Bot/1.0; +https://audit.pubsearch.io/info"

    # Timeouts (in milliseconds)
    page_load_timeout: int = 30000  # 30 seconds
    scan_total_timeout: int = 60000  # 60 seconds
    network_idle_timeout: int = 5000  # 5 seconds after network idle

    # Playwright settings
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080

    # Browser args for performance
    browser_args: list[str] = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]

    # Analysis thresholds
    min_ssp_count_for_healthy_bidding: int = 5
    high_script_count_threshold: int = 15

    # Signal recovery estimation weights
    s2s_bridge_recovery_pct: int = 15
    header_bidding_recovery_pct: int = 10
    script_bloat_recovery_pct: int = 5
    pii_leak_recovery_pct: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
