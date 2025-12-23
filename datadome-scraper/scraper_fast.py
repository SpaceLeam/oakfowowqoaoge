#!/usr/bin/env python3
"""
DataDome Scraper - STEALTH MODE
Target: 12-15 RPS (not too fast to avoid velocity detection)
"""

import tls_client
import time
import random
import re
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# --- CONFIG ---
BASE_URL = "https://bounty-nginx.datashield.co"
START_PATH = "/scraping/1"
TARGET_COUNT = 20000
MAX_THREADS = 5  # Turunin dari 8 ke 5 biar stealth
TIME_LIMIT = 1800  # 30 minutes

# Jitter delay - kunci anti-detection
JITTER_MIN = 0.05  # 50ms
JITTER_MAX = 0.15  # 150ms

# Regex patterns
link_pattern = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
hash_pattern = re.compile(r'\b([a-f0-9]{32})\b')


class StealthScraper:
    def __init__(self, cookie_value: str, max_threads: int = 5):
        self.cookie_value = cookie_value
        self.max_threads = max_threads
        
        # Thread-safe containers
        self.visited = set()
        self.results = []
        self.lock = Lock()
        
        # Stats
        self.success_count = 0
        self.error_count = 0
        self.blocked = False
        
        # Create session
        self.session = self._create_session()
    
    def _create_session(self):
        """Create TLS session with Chrome fingerprint"""
        session = tls_client.Session(
            client_identifier="chrome_131",
            random_tls_extension_order=True
        )
        session.cookies.set("datadome", self.cookie_value, domain=".datashield.co")
        return session
    
    def _build_headers(self, referer: str = None):
        """Build request headers"""
        return {
            "host": "bounty-nginx.datashield.co",
            "connection": "keep-alive",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": referer or BASE_URL,
        }
    
    def fetch_page(self, path: str):
        """Fetch single page with jitter delay"""
        
        # STEALTH: Random delay sebelum request
        time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
        
        url = f"{BASE_URL}{path}"
        try:
            resp = self.session.get(url, headers=self._build_headers(url), timeout_seconds=10)
            
            if resp.status_code == 200:
                text = resp.text
                
                # Extract hash
                hash_match = hash_pattern.search(text[:500])
                content_hash = hash_match.group(1) if hash_match else None
                
                # Extract all links
                new_links = list(set(link_pattern.findall(text)))
                
                return {
                    "status": 200,
                    "path": path,
                    "hash": content_hash,
                    "links": new_links
                }
            elif resp.status_code in [403, 429]:
                print(f"\n[!] BLOCKED: {resp.status_code} at {path}")
                self.blocked = True
                return {"status": resp.status_code, "path": path, "blocked": True}
            else:
                return {"status": resp.status_code, "path": path}
                
        except Exception as e:
            return {"status": 0, "path": path, "error": str(e)}
    
    def run(self):
        """Main scraping loop - stealth mode"""
        print(f"[*] Starting STEALTH Mode Scraper")
        print(f"[*] Threads: {self.max_threads}")
        print(f"[*] Jitter: {JITTER_MIN*1000:.0f}ms - {JITTER_MAX*1000:.0f}ms")
        print(f"[*] Target: {TARGET_COUNT} pages")
        print(f"[*] Expected RPS: 12-15 (stealth)")
        print("-" * 60)
        
        start_time = time.time()
        
        # Initialize
        self.visited.add(START_PATH)
        pending_paths = [START_PATH]
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(self.fetch_page, path): path for path in pending_paths}
            pending_paths = []
            
            while futures and self.success_count < TARGET_COUNT:
                # Time check
                elapsed = time.time() - start_time
                if elapsed > TIME_LIMIT:
                    print(f"\n[!] Time limit reached")
                    break
                
                if self.blocked:
                    print(f"\n[BLOCKED] Stopping...")
                    break
                
                for future in as_completed(futures, timeout=30):
                    path = futures.pop(future)
                    
                    try:
                        result = future.result()
                    except Exception:
                        self.error_count += 1
                        continue
                    
                    if result and result.get('status') == 200:
                        self.success_count += 1
                        
                        with self.lock:
                            self.results.append({
                                "path": result['path'],
                                "hash": result.get('hash'),
                                "status": 200
                            })
                        
                        for link in result.get('links', []):
                            if link not in self.visited:
                                self.visited.add(link)
                                pending_paths.append(link)
                        
                        if self.success_count % 100 == 0:
                            elapsed = time.time() - start_time
                            rps = self.success_count / elapsed if elapsed > 0 else 0
                            eta = (TARGET_COUNT - self.success_count) / rps if rps > 0 else 0
                            sys.stdout.write(
                                f"\r[*] {self.success_count}/{TARGET_COUNT} | "
                                f"{rps:.2f} RPS | "
                                f"ETA: {eta:.0f}s | "
                                f"Queue: {len(pending_paths)}"
                            )
                            sys.stdout.flush()
                    else:
                        self.error_count += 1
                    
                    while pending_paths and len(futures) < self.max_threads * 2:
                        new_path = pending_paths.pop(0)
                        futures[executor.submit(self.fetch_page, new_path)] = new_path
                    
                    if self.success_count >= TARGET_COUNT or self.blocked:
                        break
        
        # Summary
        total_time = time.time() - start_time
        final_rps = self.success_count / total_time if total_time > 0 else 0
        
        print(f"\n\n{'=' * 60}")
        print(f"[DONE] Total: {self.success_count}")
        print(f"[DONE] Time: {total_time:.1f}s")
        print(f"[DONE] RPS: {final_rps:.2f}")
        print(f"[DONE] Blocked: {'YES' if self.blocked else 'NO'}")
        
        return {
            'total_requests': self.success_count,
            'total_time_seconds': total_time,
            'final_rps': final_rps,
            'blocked': self.blocked
        }
    
    def save_results(self, filepath: str):
        output = {
            'total': len(self.results),
            'blocked': self.blocked,
            'results': self.results
        }
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"[*] Saved to {filepath}")


def main():
    parser = argparse.ArgumentParser(description='DataDome Stealth Scraper')
    parser.add_argument('--cookie', '-c', required=True, help='DataDome cookie')
    parser.add_argument('--threads', '-t', type=int, default=5, help='Threads (default: 5)')
    parser.add_argument('--output', '-o', default=None, help='Output file')
    
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"results_{timestamp}.json"
    
    print("=" * 60)
    print("   DATADOME SCRAPER - STEALTH MODE")
    print("=" * 60)
    
    scraper = StealthScraper(args.cookie, args.threads)
    
    try:
        scraper.run()
        scraper.save_results(output_file)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        scraper.save_results(output_file)


if __name__ == "__main__":
    main()
