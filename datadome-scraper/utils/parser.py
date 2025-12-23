"""
Fast HTML Parser (NO BeautifulSoup - speed critical)
Fixed hash extraction + all links
"""

import re
from typing import Optional, List


class FastParser:
    def __init__(self):
        # Pre-compile regex
        self.link_pattern = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
        # Hash is 32 char hex at start of page, standing alone
        self.hash_pattern = re.compile(r'\b([a-f0-9]{32})\b')

    def extract_all_links(self, html: str) -> List[str]:
        """Extract ALL page links dari HTML"""
        matches = self.link_pattern.findall(html)
        return list(set(matches))

    def extract_next_link(self, html: str) -> Optional[str]:
        """Extract first page link (legacy)"""
        match = self.link_pattern.search(html)
        return match.group(1) if match else None

    def extract_hash(self, html: str) -> Optional[str]:
        """Extract content hash (32 char MD5)"""
        # Take first 500 chars - hash biasanya di awal
        head = html[:500]
        match = self.hash_pattern.search(head)
        return match.group(1) if match else None
