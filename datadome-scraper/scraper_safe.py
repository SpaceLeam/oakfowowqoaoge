#!/usr/bin/env python3
"""
DataDome Scraper - SINGLE THREAD OPTIMIZED
Lebih safe, human-like pattern
Target: 8-10 RPS (slower but won't get blocked)
"""

import tls_client
import time
import random
import re
import sys
import json
import argparse
from datetime import datetime
from collections import deque

# --- CONFIG ---
BASE_URL = "https://bounty-nginx.datashield.co"
START_PATH = "/scraping/1"
TARGET_COUNT = 20000
TIME_LIMIT = 1800

# Timing - human-like
BASE_DELAY = 0.08  # 80ms base
VARIANCE = 0.03    # ±30ms variance
BURST_SIZE = 15    # Fast requests in burst
BURST_PAUSE = 0.3  # Pause after burst

# Regex
link_pattern = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
hash_pattern = re.compile(r'\b([a-f0-9]{32})\b')


class SafeScraper:
    def __init__(self, cookie_value: str):
        self.cookie_value = cookie_value
        self.session = self._create_session()
        
        # BFS
        self.queue = deque([START_PATH])
        self.visited = set([START_PATH])
        self.results = []
        
        # Stats
        self.count = 0
        self.blocked = False
        self.burst_counter = 0
    
    def _create_session(self):
        session = tls_client.Session(
            client_identifier="chrome_131",
            random_tls_extension_order=True
        )
        session.cookies.set("datadome", self.cookie_value, domain=".datashield.co")
        return session
    
    def _headers(self, referer):
        return {
            "host": "bounty-nginx.datashield.co",
            "connection": "keep-alive",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": referer,
        }
    
    def _delay(self):
        """Human-like delay with burst pattern"""
        self.burst_counter += 1
        
        if self.burst_counter >= BURST_SIZE:
            self.burst_counter = 0
            return BURST_PAUSE + random.uniform(0, 0.2)
        
        return BASE_DELAY + random.uniform(-VARIANCE, VARIANCE)
    
    def run(self):
        print(f"[*] Single-thread Safe Mode")
        print(f"[*] Target: {TARGET_COUNT} pages")
        print(f"[*] Expected RPS: 8-10")
        print("-" * 50)
        
        start_time = time.time()
        
        while self.queue and self.count < TARGET_COUNT:
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT:
                print(f"\n[!] Time limit")
                break
            
            path = self.queue.popleft()
            url = f"{BASE_URL}{path}"
            
            try:
                resp = self.session.get(url, headers=self._headers(url), timeout_seconds=10)
            except Exception as e:
                print(f"\n[ERROR] {e}")
                continue
            
            if resp.status_code == 403:
                print(f"\n[BLOCKED] at {self.count}")
                self.blocked = True
                break
            
            if resp.status_code != 200:
                continue
            
            # Parse
            text = resp.text
            hash_match = hash_pattern.search(text[:500])
            content_hash = hash_match.group(1) if hash_match else None
            links = set(link_pattern.findall(text))
            
            # Queue new links
            for link in links:
                if link not in self.visited:
                    self.visited.add(link)
                    self.queue.append(link)
            
            # Store
            self.results.append({
                "path": path,
                "hash": content_hash,
                "status": 200
            })
            self.count += 1
            
            # Progress
            if self.count % 100 == 0:
                rps = self.count / elapsed if elapsed > 0 else 0
                eta = (TARGET_COUNT - self.count) / rps if rps > 0 else 0
                sys.stdout.write(f"\r[*] {self.count}/{TARGET_COUNT} | {rps:.2f} RPS | ETA: {eta:.0f}s | Q: {len(self.queue)}")
                sys.stdout.flush()
            
            # Delay
            time.sleep(self._delay())
        
        total_time = time.time() - start_time
        rps = self.count / total_time if total_time > 0 else 0
        
        print(f"\n\n{'='*50}")
        print(f"[DONE] Total: {self.count}")
        print(f"[DONE] Time: {total_time:.1f}s")
        print(f"[DONE] RPS: {rps:.2f}")
        print(f"[DONE] Blocked: {'YES' if self.blocked else 'NO'}")
        
        return {'total': self.count, 'time': total_time, 'rps': rps, 'blocked': self.blocked}
    
    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump({'total': len(self.results), 'blocked': self.blocked, 'results': self.results}, f, indent=2)
        print(f"[*] Saved: {filepath}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie', '-c', required=True)
    parser.add_argument('--output', '-o', default=None)
    args = parser.parse_args()
    
    output = args.output or f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print("=" * 50)
    print("   SAFE MODE SCRAPER")
    print("=" * 50)
    
    scraper = SafeScraper(args.cookie)
    
    try:
        scraper.run()
        scraper.save(output)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        scraper.save(output)


if __name__ == "__main__":
    main()
