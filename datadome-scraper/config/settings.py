"""
DataDome Scraper Configuration - Nginx Optimized (2025 December Edition)
Target: 20,000 pages dalam 30 menit (~12 RPS)
AGGRESSIVE SETTINGS for Medium scenario
"""

import os
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    # Target
    BASE_URL: str = "https://bounty-nginx.datashield.co"
    START_PATH: str = "/scraping/1"
    TARGET_REQUESTS: int = 20000
    TIME_LIMIT: int = 1800  # 30 menit

    # Performance - AGGRESSIVE
    TARGET_RPS: float = 15.0  # Lebih tinggi
    MAX_RETRIES: int = 1
    TIMEOUT: int = 10

    # Behavioral - Faster Burst
    BURST_SIZE_MIN: int = 30
    BURST_SIZE_MAX: int = 50
    BURST_INTERVAL_MIN: float = 0.2
    BURST_INTERVAL_MAX: float = 0.5

    # Cooldown - Less frequent
    COOLDOWN_EVERY_MIN: int = 800
    COOLDOWN_EVERY_MAX: int = 1000
    COOLDOWN_DURATION_MIN: float = 2.0
    COOLDOWN_DURATION_MAX: float = 4.0

    # Timing Variance - Minimal delay
    REQUEST_VARIANCE: float = 0.15
    THINK_TIME_MIN: float = 0.01
    THINK_TIME_MAX: float = 0.03

    # TLS Fingerprinting
    TLS_CLIENT_VERSION: str = "chrome_131"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # Cookie check interval
    COOKIE_CHECK_INTERVAL: int = 200

    # Activity Phase - Shorter rest
    ACTIVE_PHASE_MIN: float = 120.0
    ACTIVE_PHASE_MAX: float = 180.0
    REST_PHASE_MIN: float = 2.0
    REST_PHASE_MAX: float = 4.0

    # Entropy tracking
    ENTROPY_TARGET: float = 4.5
    ENTROPY_CHECK_INTERVAL: int = 200

    # Response time - exploit timeout
    RESPONSE_TIME_THRESHOLD: float = 0.050
    FAST_BURST_ON_SLOW_API: bool = True


config = ScraperConfig()
