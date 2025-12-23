"""
Fast HTML Parser menggunakan regex (NO BeautifulSoup - speed critical)
"""

import re
from typing import Optional


class FastParser:
    def __init__(self):
        # Pre-compile regex untuk speed
        self.link_pattern = re.compile(r'href=["\'](/scraping/\d+)["\']')
        self.hash_pattern = re.compile(r'[a-f0-9]{32,64}')

    def extract_next_link(self, html: str) -> Optional[str]:
        """Extract next page link dari HTML"""
        match = self.link_pattern.search(html)
        return match.group(1) if match else None

    def extract_hash(self, html: str) -> Optional[str]:
        """Extract content hash dari page"""
        match = self.hash_pattern.search(html)
        return match.group(0) if match else None
