"""
HTTP Client dengan TLS Fingerprinting (JA4/Chrome 131)
"""

import tls_client
import re
from typing import Dict, Optional


class HTTPClient:
    def __init__(self, config, cookie_value: str):
        self.config = config
        self.cookie_value = cookie_value
        self.session = self._create_session()
        self._set_cookie(cookie_value)
        self.request_count = 0

    def _create_session(self):
        """Initialize TLS client dengan JA4 fingerprint Chrome 131"""
        return tls_client.Session(
            client_identifier=self.config.TLS_CLIENT_VERSION,
            random_tls_extension_order=True  # GREASE support
        )

    def _set_cookie(self, cookie_value: str):
        """Set datadome cookie"""
        self.session.cookies.set(
            "datadome",
            cookie_value,
            domain=".datashield.co"
        )

    def get(self, url: str, headers: Dict) -> Optional[object]:
        """
        GET request dengan retry logic minimal (match nginx behavior)
        """
        try:
            resp = self.session.get(
                url,
                headers=headers,
                timeout_seconds=self.config.TIMEOUT
            )
            self.request_count += 1
            return resp
        except Exception as e:
            raise e

    def update_cookie(self, resp) -> bool:
        """
        Check dan update cookie dari response header
        Return True jika cookie di-update
        """
        cookies = resp.headers.get('set-cookie', '')
        match = re.search(r'datadome=([^;]+)', cookies)
        if match:
            new_cookie = match.group(1)
            if new_cookie != self.cookie_value:
                self.cookie_value = new_cookie
                self._set_cookie(new_cookie)
                return True
        return False
