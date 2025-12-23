"""
DataDome Scraper - Nginx Optimized (2025 December Edition)
BFS-based traversal untuk tree structure pages
"""

import time
import json
from collections import deque
from typing import Dict, List, Set

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
        
        # BFS State
        self.queue = deque([config.START_PATH])  # Queue of paths to visit
        self.visited: Set[str] = set()  # Already visited paths
        self.results = []
        self.blocked = False

    def _build_headers(self, current_url: str) -> Dict:
        """Build complete 2025 Chrome 131 headers"""
        return {
            "host": "bounty-nginx.datashield.co",
            "connection": "keep-alive",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": self.config.USER_AGENT,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "referer": current_url,
            "priority": "u=0, i"
        }

    def run(self) -> Dict:
        """Main scraping loop using BFS"""
        print(f"[*] Starting DataDome Scraper (2025 BFS Edition)")
        print(f"[*] Target: {self.config.TARGET_REQUESTS} pages in {self.config.TIME_LIMIT}s")
        print(f"[*] Target RPS: {self.config.TARGET_RPS}")
        print(f"[*] Start path: {self.config.START_PATH}")
        print("-" * 60)
        
        start_time = time.time()
        count = 0
        
        while self.queue and count < self.config.TARGET_REQUESTS:
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > self.config.TIME_LIMIT:
                print(f"\n[!] Time limit reached ({self.config.TIME_LIMIT}s)")
                break
            
            # Get next path from queue
            current_path = self.queue.popleft()
            
            # Skip if already visited
            if current_path in self.visited:
                continue
            
            self.visited.add(current_path)
            
            # Build URL and headers
            url = f"{self.config.BASE_URL}{current_path}"
            headers = self._build_headers(url)
            
            # Execute request
            try:
                resp = self.client.get(url, headers)
            except Exception as e:
                print(f"\n[ERROR] Request failed: {e}")
                self.metrics.errors += 1
                continue  # Don't break, try next in queue
            
            # Validate response
            if self.validator.is_blocked(resp):
                self.blocked = True
                self.metrics.blocks += 1
                print(f"\n[BLOCKED] at request {count}")
                print(f"Status: {resp.status_code if resp else 'None'}")
                break
            
            if not self.validator.is_valid(resp):
                self.metrics.errors += 1
                continue  # Skip invalid, try next
            
            # Parse content - get ALL links
            new_links = self.parser.extract_all_links(resp.text)
            content_hash = self.parser.extract_hash(resp.text)
            
            # Add new links to queue (if not visited)
            for link in new_links:
                if link not in self.visited:
                    self.queue.append(link)
            
            # Store result
            self.results.append({
                'path': current_path,
                'hash': content_hash,
                'status': resp.status_code
            })
            self.metrics.success += 1
            count += 1
            
            # Check cookie update
            if count % self.config.COOKIE_CHECK_INTERVAL == 0:
                if self.client.update_cookie(resp):
                    print(f"\n[!] Cookie updated at {count}")
            
            # Check entropy
            if count % self.config.ENTROPY_CHECK_INTERVAL == 0 and count > 0:
                entropy = self.timing.get_entropy()
                if entropy > 0:
                    if entropy < self.config.ENTROPY_TARGET:
                        print(f"\n[WARNING] Low entropy: {entropy:.2f}")
            
            # Progress display
            if count % 50 == 0:
                self.metrics.print_progress(count, start_time, current_path)
                print(f" | Queue: {len(self.queue)}", end='')
            
            # Smart delay
            delay = self.timing.calculate_delay(count, self.client.last_response_time)
            time.sleep(delay)
        
        # Final summary
        print("\n" + "=" * 60)
        summary = self.metrics.get_summary(count, start_time)
        print(f"[DONE] Total: {summary['total_requests']} requests")
        print(f"[DONE] Time: {summary['total_time_seconds']:.1f}s")
        print(f"[DONE] Final RPS: {summary['final_rps']:.2f}")
        print(f"[DONE] Success: {summary['success']}, Errors: {summary['errors']}, Blocks: {summary['blocks']}")
        
        final_entropy = self.timing.get_entropy()
        print(f"[DONE] Final Entropy: {final_entropy:.2f} bits")
        summary['entropy'] = final_entropy
        
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
