#!/usr/bin/env python3
"""
DataDome Scraper - HYDRA V7
Usage:
  python scraper_multi.py test   # Test cookies
  python scraper_multi.py run    # Run scraping
"""

import tls_client
import time
import re
import sys
import json
import random
import signal
from datetime import datetime
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Event

# ============================================================
#  PASTE COOKIES DISINI (Max 6)
# ============================================================
COOKIES = [
    "Y83XPQBXNPEmUG5G78UnKbmZdMlMNdAkn0THPMFikBQdj2Iq~iGf2dt8h5V0ztNgStr9g~FIjcKpDqnh8WGQtkHbiIoeVI8SVtUkwVBCz0LMPPQWlnHagiI8qgG1~Yoq",
    "B7AARNG3TRRyJANrs3bHzx5Oe6C6FCkxuPvdYlh2coRUjRWjonBO42dESM~q0EkacpRQEAQngpR1qBRXSVzPylo6QiMsJ_biXnh9v8j7C27yw10ghP5eySStj2QVG8eI",
    "KJSFnzalG3OlC~fO2ZSBi~9Je4AXaU3GXK3XuHlPgPjMiz~OETYIWhgYPlMFF6ZklDU6mLiKfKOK53F2HFzpKiDp2VXynK04KFiwEYYxiuGOIojU_Bj2PMVFv1acJZ0C",
    # "PASTE_COOKIE_4_DISINI",
    # "PASTE_COOKIE_5_DISINI",
    # "PASTE_COOKIE_6_DISINI",
]
# ============================================================

# --- CONFIG ---
BASE_URL = "https://bounty-nginx.datashield.co"
START_PATH = "/scraping/1"
TARGET_COUNT = 20000
TIME_LIMIT = 1800
OUTPUT_FILE = "results/results_hydra.json"

THREADS_PER_COOKIE = 3
DELAY_PER_REQ = 0.15
CHECKPOINT_INTERVAL = 500  # Print stats every 500 results

BROWSERS = [
    ("Chrome", "chrome_131"),
    ("Firefox", "firefox_120"),
    ("Brave", "chrome_124"),
    ("Edge", "chrome_120"),
    ("Opera", "opera_90"),
    ("Safari", "safari_16_0"),
]

link_pattern = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
hash_pattern = re.compile(r'\b([a-f0-9]{32})\b')

# Global state
job_queue = Queue()
visited_links = set()
results = []
visited_lock = Lock()
results_lock = Lock()
stop_event = Event()
start_time = None
last_checkpoint = 0


def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")


def save_results():
    with results_lock:
        data = {'total': len(results), 'results': results}
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def print_checkpoint(count, force=False):
    global last_checkpoint
    
    if not force and count < last_checkpoint + CHECKPOINT_INTERVAL:
        return
    
    elapsed = time.time() - start_time
    rps = count / elapsed if elapsed > 0 else 0
    eta = (TARGET_COUNT - count) / rps if rps > 0 else 0
    
    print(f"\n[{get_timestamp()}] ═══════════════════════════════════════")
    print(f"[{get_timestamp()}] 📊 CHECKPOINT: {count} pages scraped")
    print(f"[{get_timestamp()}] ⚡ Speed: {rps:.2f} RPS")
    print(f"[{get_timestamp()}] ⏱️  Elapsed: {int(elapsed)}s | ETA: {int(eta)}s")
    print(f"[{get_timestamp()}] 📁 Queue: {job_queue.qsize()} pending")
    print(f"[{get_timestamp()}] ═══════════════════════════════════════")
    
    save_results()
    last_checkpoint = (count // CHECKPOINT_INTERVAL) * CHECKPOINT_INTERVAL


def signal_handler(sig, frame):
    print(f"\n\n[{get_timestamp()}] ⚠️  INTERRUPTED!")
    stop_event.set()
    
    elapsed = time.time() - start_time if start_time else 0
    rps = len(results) / elapsed if elapsed > 0 else 0
    
    print(f"\n{'='*50}")
    print(f"📋 FINAL REPORT")
    print(f"{'='*50}")
    print(f"🕐 Started:  {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}")
    print(f"🕐 Ended:    {get_timestamp()}")
    print(f"⏱️  Duration: {int(elapsed)}s ({elapsed/60:.1f} min)")
    print(f"📊 Total:    {len(results)} pages")
    print(f"⚡ Avg RPS:  {rps:.2f}")
    print(f"{'='*50}")
    
    save_results()
    print(f"💾 Saved: {OUTPUT_FILE}")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class CookieTester:
    @staticmethod
    def test_cookie(cookie: str, browser_id: str, name: str) -> dict:
        session = tls_client.Session(client_identifier=browser_id, random_tls_extension_order=True)
        session.cookies.set("datadome", cookie, domain=".datashield.co")
        try:
            resp = session.get(f"{BASE_URL}{START_PATH}", 
                             headers={"user-agent": "Mozilla/5.0"}, 
                             timeout_seconds=10)
            if resp.status_code == 200:
                return {"name": name, "status": "✅ VALID", "code": 200}
            elif resp.status_code == 403:
                return {"name": name, "status": "❌ BLOCKED", "code": 403}
            else:
                return {"name": name, "status": f"⚠️ {resp.status_code}", "code": resp.status_code}
        except:
            return {"name": name, "status": "❌ ERROR", "code": 0}
    
    @staticmethod
    def test_all():
        print(f"\n[{get_timestamp()}] {'='*40}")
        print(f"[{get_timestamp()}] 🔍 COOKIE TESTER")
        print(f"[{get_timestamp()}] {'='*40}")
        
        valid = []
        for i, cookie in enumerate(COOKIES):
            if cookie.startswith("PASTE_"):
                continue
            browser_name, browser_id = BROWSERS[i % len(BROWSERS)]
            name = f"Cookie-{i+1} ({browser_name})"
            print(f"[{get_timestamp()}] Testing {name}...", end=" ", flush=True)
            result = CookieTester.test_cookie(cookie, browser_id, name)
            print(result["status"])
            if result["code"] == 200:
                valid.append((cookie, browser_id, name))
        
        print(f"[{get_timestamp()}] {'-'*40}")
        print(f"[{get_timestamp()}] ✅ Valid: {len(valid)}/{len([c for c in COOKIES if not c.startswith('PASTE_')])}")
        return valid


class Worker:
    def __init__(self, name, cookie, browser_id):
        self.name = name
        self.session = tls_client.Session(client_identifier=browser_id, random_tls_extension_order=True)
        self.session.cookies.set("datadome", cookie, domain=".datashield.co")
        self.blocked = False
        self.count = 0

    def headers(self, referer):
        return {
            "host": "bounty-nginx.datashield.co",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml",
            "referer": referer,
        }


def process_job(worker):
    global start_time
    
    while not stop_event.is_set():
        with results_lock:
            count = len(results)
            if count >= TARGET_COUNT:
                return
        
        if (time.time() - start_time) > TIME_LIMIT:
            return
        
        try:
            path, referer = job_queue.get(timeout=1)
        except Empty:
            continue

        if worker.blocked:
            job_queue.put((path, referer))
            return

        time.sleep(random.uniform(0.05, DELAY_PER_REQ))
        
        try:
            resp = worker.session.get(f"{BASE_URL}{path}", 
                                     headers=worker.headers(referer), 
                                     timeout_seconds=10)
            
            if resp.status_code == 200:
                worker.count += 1
                text = resp.text
                hash_match = hash_pattern.search(text[:1000])
                new_links = set(link_pattern.findall(text))
                
                with results_lock:
                    results.append({
                        "path": path,
                        "hash": hash_match.group(1) if hash_match else None,
                        "status": 200
                    })
                    current = len(results)
                    
                    # Progress every 10
                    if current % 10 == 0:
                        elapsed = time.time() - start_time
                        rps = current / elapsed if elapsed > 0 else 0
                        sys.stdout.write(f"\r[{get_timestamp()}] 📈 {current}/{TARGET_COUNT} | {rps:.2f} RPS | Q: {job_queue.qsize()}   ")
                        sys.stdout.flush()
                    
                    # Checkpoint every 500
                    if current % CHECKPOINT_INTERVAL == 0:
                        print_checkpoint(current)

                with visited_lock:
                    for link in new_links:
                        if link not in visited_links:
                            visited_links.add(link)
                            job_queue.put((link, f"{BASE_URL}{path}"))
            
            elif resp.status_code in [403, 429]:
                if not worker.blocked:
                    print(f"\n[{get_timestamp()}] ❌ {worker.name} BLOCKED!")
                    worker.blocked = True
                job_queue.put((path, referer))
                
        except:
            job_queue.put((path, referer))
        finally:
            job_queue.task_done()


def run_scraper():
    global job_queue, visited_links, results, start_time, last_checkpoint
    
    print(f"\n[{get_timestamp()}] 🔍 Testing cookies first...")
    valid = CookieTester.test_all()
    
    if not valid:
        print(f"\n[{get_timestamp()}] ❌ No valid cookies!")
        return
    
    # Reset state
    job_queue = Queue()
    job_queue.put((START_PATH, BASE_URL))
    visited_links = set([START_PATH])
    results = []
    last_checkpoint = 0
    
    workers = [Worker(name, cookie, bid) for cookie, bid, name in valid]
    total_threads = len(workers) * THREADS_PER_COOKIE
    
    print(f"\n[{get_timestamp()}] {'='*40}")
    print(f"[{get_timestamp()}] 🚀 HYDRA SCRAPER STARTING")
    print(f"[{get_timestamp()}] {'='*40}")
    print(f"[{get_timestamp()}] 🍪 Cookies: {len(valid)}")
    print(f"[{get_timestamp()}] 🧵 Threads: {total_threads}")
    print(f"[{get_timestamp()}] 🎯 Target: {TARGET_COUNT} pages")
    print(f"[{get_timestamp()}] ⚡ Expected: ~{len(workers) * 4} RPS")
    print(f"[{get_timestamp()}] {'='*40}\n")
    
    start_time = time.time()
    
    try:
        with ThreadPoolExecutor(max_workers=total_threads) as executor:
            futures = []
            for worker in workers:
                for _ in range(THREADS_PER_COOKIE):
                    futures.append(executor.submit(process_job, worker))
            
            while not stop_event.is_set():
                with results_lock:
                    if len(results) >= TARGET_COUNT:
                        break
                if (time.time() - start_time) > TIME_LIMIT:
                    break
                time.sleep(0.5)
    except:
        pass
    
    # Final report
    elapsed = time.time() - start_time
    rps = len(results) / elapsed if elapsed > 0 else 0
    
    print(f"\n\n[{get_timestamp()}] {'='*50}")
    print(f"[{get_timestamp()}] 📋 FINAL REPORT")
    print(f"[{get_timestamp()}] {'='*50}")
    print(f"[{get_timestamp()}] 🕐 Started:  {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}")
    print(f"[{get_timestamp()}] 🕐 Ended:    {get_timestamp()}")
    print(f"[{get_timestamp()}] ⏱️  Duration: {int(elapsed)}s ({elapsed/60:.1f} min)")
    print(f"[{get_timestamp()}] 📊 Total:    {len(results)} pages")
    print(f"[{get_timestamp()}] ⚡ Avg RPS:  {rps:.2f}")
    print(f"[{get_timestamp()}] {'-'*50}")
    
    for w in workers:
        status = "❌ BLOCKED" if w.blocked else "✅ OK"
        print(f"[{get_timestamp()}] [{w.name}] {w.count} reqs | {status}")
    
    print(f"[{get_timestamp()}] {'='*50}")
    save_results()
    print(f"[{get_timestamp()}] 💾 Saved: {OUTPUT_FILE}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scraper_multi.py test")
        print("  python scraper_multi.py run"   )
        return
    
    cmd = sys.argv[1].lower()
    if cmd == "test":
        CookieTester.test_all()
    elif cmd == "run":
        run_scraper()
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
