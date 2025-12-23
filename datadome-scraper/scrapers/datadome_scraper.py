"""
DataDome Scraper - Nginx Optimized
Main scraping logic untuk bypass DataDome protection
"""

import time
import json
from typing import Dict, List

from core.client import HTTPClient
from detections.timing import TimingController
from utils.parser import FastParser
from utils.validator import ResponseValidator
from utils.metrics import MetricsTracker


class DataDomeScraper:
    def __init__(self, config, cookie_value: str):
        self.config = config
        
        # Initialize components
        self.client = HTTPClient(config, cookie_value)
        self.timing = TimingController(config)
        self.parser = FastParser()
        self.validator = ResponseValidator()
        self.metrics = MetricsTracker()
        
        # State
        self.current_path = config.START_PATH
        self.results = []
        self.blocked = False

    def _build_headers(self, current_url: str) -> Dict:
        """Build request headers"""
        return {
            "host": "bounty-nginx.datashield.co",
            "connection": "keep-alive",
            "upgrade-insecure-requests": "1",
            "user-agent": self.config.USER_AGENT,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": current_url,
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
        }

    def run(self) -> Dict:
        """
        Main scraping loop
        Returns: metrics dict
        """
        print(f"[*] Starting DataDome Scraper (Nginx-Optimized)")
        print(f"[*] Target: {self.config.TARGET_REQUESTS} pages in {self.config.TIME_LIMIT}s")
        print(f"[*] Target RPS: {self.config.TARGET_RPS}")
        print("-" * 60)
        
        start_time = time.time()
        count = 0
        
        while count < self.config.TARGET_REQUESTS:
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > self.config.TIME_LIMIT:
                print(f"\n[!] Time limit reached ({self.config.TIME_LIMIT}s)")
                break
            
            # Build URL and headers
            url = f"{self.config.BASE_URL}{self.current_path}"
            headers = self._build_headers(url)
            
            # Execute request
            try:
                resp = self.client.get(url, headers)
            except Exception as e:
                print(f"\n[ERROR] Request failed: {e}")
                self.metrics.errors += 1
                break
            
            # Validate response
            if self.validator.is_blocked(resp):
                self.blocked = True
                self.metrics.blocks += 1
                print(f"\n[BLOCKED] at request {count}")
                print(f"Status: {resp.status_code if resp else 'None'}")
                break
            
            if not self.validator.is_valid(resp):
                print(f"\n[!] Invalid response at {count}, status: {resp.status_code}")
                self.metrics.errors += 1
                time.sleep(2)
                continue
            
            # Parse content
            next_path = self.parser.extract_next_link(resp.text)
            content_hash = self.parser.extract_hash(resp.text)
            
            if not next_path:
                print(f"\n[!] No next link found at {self.current_path}")
                break
            
            # Store result
            self.results.append({
                'path': self.current_path,
                'hash': content_hash,
                'status': resp.status_code
            })
            self.metrics.success += 1
            
            # Update state
            self.current_path = next_path
            count += 1
            
            # Check cookie update
            if count % self.config.COOKIE_CHECK_INTERVAL == 0:
                if self.client.update_cookie(resp):
                    print(f"\n[!] Cookie updated at {count}")
            
            # Progress display
            if count % 50 == 0:
                self.metrics.print_progress(count, start_time, self.current_path)
            
            # Smart delay
            delay = self.timing.calculate_delay(count)
            time.sleep(delay)
        
        # Final summary
        print("\n" + "=" * 60)
        summary = self.metrics.get_summary(count, start_time)
        print(f"[DONE] Total: {summary['total_requests']} requests")
        print(f"[DONE] Time: {summary['total_time_seconds']:.1f}s")
        print(f"[DONE] Final RPS: {summary['final_rps']:.2f}")
        print(f"[DONE] Success: {summary['success']}, Errors: {summary['errors']}, Blocks: {summary['blocks']}")
        
        return summary

    def save_results(self, filepath: str):
        """Save scraped results to JSON"""
        output = {
            'total': len(self.results),
            'blocked': self.blocked,
            'results': self.results
        }
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"[*] Results saved to {filepath}")
