"""
DataDome Scraper Configuration - Nginx Optimized (Medium Scenario)
Target: 20,000 pages dalam 30 menit (~12 RPS)
"""

import os
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    # Target
    BASE_URL: str = "https://bounty-nginx.datashield.co"
    START_PATH: str = "/scraping/0001"
    TARGET_REQUESTS: int = 20000
    TIME_LIMIT: int = 1800  # 30 menit

    # Performance - Nginx Optimized
    TARGET_RPS: float = 12.0  # Aggressive untuk medium
    MAX_RETRIES: int = 1  # Nginx gak retry, kita juga
    TIMEOUT: int = 10

    # Behavioral - Burst Pattern
    BURST_SIZE_MIN: int = 20
    BURST_SIZE_MAX: int = 30
    BURST_INTERVAL_MIN: float = 0.5
    BURST_INTERVAL_MAX: float = 1.0

    # Cooldown
    COOLDOWN_EVERY_MIN: int = 450
    COOLDOWN_EVERY_MAX: int = 550
    COOLDOWN_DURATION_MIN: float = 4.0
    COOLDOWN_DURATION_MAX: float = 8.0

    # Timing Variance (ML-resistant, >15%)
    REQUEST_VARIANCE: float = 0.20
    THINK_TIME_MIN: float = 0.03
    THINK_TIME_MAX: float = 0.12

    # TLS Fingerprinting
    TLS_CLIENT_VERSION: str = "chrome_131"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # Cookie check interval
    COOKIE_CHECK_INTERVAL: int = 100


config = ScraperConfig()
