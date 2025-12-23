"""
HTTP Client dengan TLS Fingerprinting (JA4/Chrome 131)
2025 Edition dengan response time tracking
"""

import tls_client
import re
import time
from typing import Dict, Optional


class HTTPClient:
    def __init__(self, config, cookie_value: str):
        self.config = config
        self.cookie_value = cookie_value
        self.session = self._create_session()
        self._set_cookie(cookie_value)
        self.request_count = 0
        
        # 2025: Track response times untuk exploit timeout
        self.response_times = []
        self.last_response_time = 0

    def _create_session(self):
        """Initialize TLS client dengan JA4 fingerprint Chrome 131"""
        session = tls_client.Session(
            client_identifier=self.config.TLS_CLIENT_VERSION,
            random_tls_extension_order=True
        )
        print("[*] TLS Client initialized with Chrome 131 fingerprint")
        return session

    def _set_cookie(self, cookie_value: str):
        """Set datadome cookie"""
        self.session.cookies.set(
            "datadome",
            cookie_value,
            domain=".datashield.co"
        )

    def get(self, url: str, headers: Dict) -> Optional[object]:
        """GET request dengan response time tracking"""
        start = time.time()
        try:
            resp = self.session.get(
                url,
                headers=headers,
                timeout_seconds=self.config.TIMEOUT
            )
            
            # Track response time
            self.last_response_time = time.time() - start
            self.response_times.append(self.last_response_time)
            
            self.request_count += 1
            return resp
        except Exception as e:
            raise e

    def update_cookie(self, resp) -> bool:
        """Check dan update cookie dari response header"""
        cookies = resp.headers.get('set-cookie', '')
        match = re.search(r'datadome=([^;]+)', cookies)
        if match:
            new_cookie = match.group(1)
            if new_cookie != self.cookie_value:
                self.cookie_value = new_cookie
                self._set_cookie(new_cookie)
                return True
        return False

    def get_avg_response_time(self) -> float:
        """Get average API response time (2025)"""
        if not self.response_times:
            return 0.0
        recent = self.response_times[-100:]
        return sum(recent) / len(recent)
