#!/usr/bin/env python3
"""
DataDome Scraper - V3 (Session Rotation + Anti-Fatigue)
ADDED: Reset session tiap 200 request biar fingerprint fresh
"""

import tls_client
import time
import re
import sys
import json
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# --- CONFIG ---
BASE_URL = "https://bounty-nginx.datashield.co"
START_PATH = "/scraping/1"
TARGET_COUNT = 20000
TIME_LIMIT = 1800

# TUNED SETTINGS
BATCH_SIZE = 16
BATCH_DELAY = 0.15
JITTER = 0.05
RESET_INTERVAL = 200  # Ganti session tiap 200 request

# Regex
link_pattern = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
hash_pattern = re.compile(r'\b([a-f0-9]{32})\b')


class SmartBatchScraper:
    def __init__(self, cookie_value: str):
        self.cookie_value = cookie_value
        self.lock = Lock()
        self.session = None
        self._reset_session()
        
        self.queue = [(START_PATH, BASE_URL)]
        self.visited = set([START_PATH])
        self.results = []
        self.count = 0
        self.blocked = False
        self.start_time = None
    
    def _reset_session(self):
        """Create fresh session with new TLS fingerprint"""
        with self.lock:
            self.session = tls_client.Session(
                client_identifier="chrome_131",
                random_tls_extension_order=True
            )
            self.session.cookies.set("datadome", self.cookie_value, domain=".datashield.co")
    
    def _headers(self, referer: str):
        return {
            "host": "bounty-nginx.datashield.co",
            "connection": "keep-alive",
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "referer": referer,
            "accept-language": "en-US,en;q=0.9",
        }
    
    def _print_progress(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        rps = self.count / elapsed if elapsed > 0 else 0
        eta = (TARGET_COUNT - self.count) / rps if rps > 0 else 0
        sys.stdout.write(f"\r[*] {self.count}/{TARGET_COUNT} | {rps:.2f} RPS | ETA: {eta:.0f}s | Q: {len(self.queue)}   ")
        sys.stdout.flush()
    
    def fetch_page(self, path: str, referer: str):
        time.sleep(random.uniform(0.00, JITTER))
        
        url = f"{BASE_URL}{path}"
        try:
            resp = self.session.get(url, headers=self._headers(referer), timeout_seconds=10)
            
            if resp.status_code == 200:
                text = resp.text
                hash_match = hash_pattern.search(text[:1000])
                links = list(set(link_pattern.findall(text)))
                return {
                    "status": 200, "path": path, 
                    "hash": hash_match.group(1) if hash_match else None,
                    "links": links, "url": url
                }
            elif resp.status_code in [403, 429]:
                return {"status": resp.status_code, "path": path, "blocked": True}
            else:
                return {"status": resp.status_code, "path": path}
        except Exception as e:
            return {"status": 0, "path": path, "error": str(e)}
    
    def run(self):
        print(f"[*] MISSION: MEDIUM TARGET (€800)")
        print(f"[*] Batch={BATCH_SIZE}, Delay={BATCH_DELAY}s")
        print(f"[*] Session reset every {RESET_INTERVAL} requests")
        print("-" * 60)
        
        self.start_time = time.time()
        
        while self.queue and self.count < TARGET_COUNT:
            if (time.time() - self.start_time) > TIME_LIMIT:
                print(f"\n[!] Time limit")
                break
            
            # Session rotation - reset every RESET_INTERVAL
            if self.count > 0 and self.count % RESET_INTERVAL == 0:
                self._reset_session()
                print(f"\n[*] Session rotated at {self.count}")
            
            # Prepare batch
            batch = []
            while len(batch) < BATCH_SIZE and self.queue:
                batch.append(self.queue.pop(0))
            
            if not batch: 
                break
            
            # Execute batch
            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
                futures = {executor.submit(self.fetch_page, p, r): (p, r) for p, r in batch}
                
                for future in as_completed(futures):
                    res = future.result()
                    
                    if res.get('blocked'):
                        print(f"\n[BLOCKED] {res['status']} at {res['path']}")
                        self.blocked = True
                        break
                    
                    if res.get('status') == 200:
                        with self.lock:
                            self.count += 1
                            if res.get('hash'):
                                self.results.append({"path": res['path'], "hash": res['hash'], "status": 200})
                            
                            parent_url = res.get('url', BASE_URL)
                            for link in res.get('links', []):
                                if link not in self.visited:
                                    self.visited.add(link)
                                    self.queue.append((link, parent_url))
                            
                            if self.count % 10 == 0:
                                self._print_progress()

                if self.blocked: 
                    break

            if self.blocked: 
                break
            
            time.sleep(BATCH_DELAY)
        
        self._print_progress()
        total_time = time.time() - self.start_time
        print(f"\n\n{'='*60}")
        print(f"[DONE] Total: {self.count}")
        print(f"[DONE] Time: {total_time:.1f}s")
        print(f"[DONE] RPS: {self.count/total_time:.2f}")
        print(f"[DONE] Blocked: {'YES' if self.blocked else 'NO'}")
        print(f"{'='*60}")

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump({'total': len(self.results), 'results': self.results}, f, indent=2)
        print(f"[*] Saved: {filepath} ({len(self.results)} results)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie', '-c', required=True)
    args = parser.parse_args()
    
    scraper = SmartBatchScraper(args.cookie)
    try:
        scraper.run()
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        scraper.save(f"results_{int(time.time())}.json")


if __name__ == "__main__":
    main()
