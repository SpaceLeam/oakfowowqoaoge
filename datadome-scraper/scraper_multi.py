#!/usr/bin/env python3
"""
Multi-Cookie Parallel Scraper
Usage: python scraper_multi.py [test|run]
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
# COOKIES - Paste your cookies here
# ============================================================
COOKIES = [
    "5tH6KQo7YHC9g3ERhA5F12t0avdLDQn9rNVNTAHNlB92JJSlIEcmQXt7LTYhmtZxrnZtA~qDW1ljeM6Es7~wMSRZqFEpfwQXfclKuGUoJWS02fhX_YMZJBuHZVJx3xCR",
    "OWrOiTxAepXShvSZh6YvcG4j~wjY69zoco_HdJs~fDX9A0IxcWZJkRf6vZtV~s7r9jv3gSm3w~FXrhSi_8_3RxgDstV4x2GoOkhh2z2O59QWrC8DDl2Wl8zJgSlbmbTL",
    "9pkjNFe~y5cXgk3HPrmId25PSi~nri0eJu6KPiCUUIi2u4ojQbXuDG_NwCp0vk5CapqcXq7uZpMaDVLjjFpFowjKYSEqRq113_tYIQd8qEkQBcqBWBbQSk9LD0omx4Nk",
]
# ============================================================

BASE_URL = "https://bounty-nginx.datashield.co"
START_PATH = "/scraping/1"
TARGET_COUNT = 20000
TIME_LIMIT = 1800
OUTPUT_FILE = "results/results_hydra.json"

THREADS_PER_COOKIE = 3
DELAY_PER_REQ = 0.15
CHECKPOINT = 500

BROWSERS = [
    ("Chrome", "chrome_131"),
    ("Firefox", "firefox_120"),
    ("Brave", "chrome_124"),
    ("Edge", "chrome_120"),
]

link_re = re.compile(r'href=["\']?(/scraping/\d+)["\']?')
hash_re = re.compile(r'\b([a-f0-9]{32})\b')

job_queue = Queue()
visited = set()
results = []
lock = Lock()
stop = Event()
start_time = None
last_cp = 0


def ts():
    return datetime.now().strftime("%H:%M:%S")


def save():
    with lock:
        data = {'total': len(results), 'results': list(results)}
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def checkpoint(count, force=False):
    global last_cp
    if not force and count < last_cp + CHECKPOINT:
        return
    elapsed = time.time() - start_time
    rps = count / elapsed if elapsed > 0 else 0
    eta = (TARGET_COUNT - count) / rps if rps > 0 else 0
    print(f"\n[{ts()}] === CHECKPOINT: {count} | {rps:.2f} RPS | ETA: {int(eta)}s ===")
    save()
    last_cp = (count // CHECKPOINT) * CHECKPOINT


def sigint(sig, frame):
    print(f"\n[{ts()}] Interrupted - saving...")
    stop.set()
    elapsed = time.time() - start_time if start_time else 0
    rps = len(results) / elapsed if elapsed > 0 else 0
    print(f"[{ts()}] Total: {len(results)} | Time: {int(elapsed)}s | RPS: {rps:.2f}")
    save()
    print(f"[{ts()}] Saved: {OUTPUT_FILE}")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint)


def test_cookie(cookie, bid, name):
    s = tls_client.Session(client_identifier=bid, random_tls_extension_order=True)
    s.cookies.set("datadome", cookie, domain=".datashield.co")
    headers = {
        "host": "bounty-nginx.datashield.co",
        "connection": "keep-alive",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-dest": "document",
        "accept-language": "en-US,en;q=0.9",
    }
    try:
        r = s.get(f"{BASE_URL}{START_PATH}", headers=headers, timeout_seconds=10)
        return {"name": name, "ok": r.status_code == 200, "code": r.status_code}
    except:
        return {"name": name, "ok": False, "code": 0}


def test_all():
    print(f"[{ts()}] Testing cookies...")
    valid = []
    for i, c in enumerate(COOKIES):
        if c.startswith("PASTE_"):
            continue
        bn, bid = BROWSERS[i % len(BROWSERS)]
        name = f"Cookie-{i+1}"
        r = test_cookie(c, bid, name)
        status = "OK" if r["ok"] else f"FAIL({r['code']})"
        print(f"  {name} ({bn}): {status}")
        if r["ok"]:
            valid.append((c, bid, name))
    print(f"[{ts()}] Valid: {len(valid)}/{len([c for c in COOKIES if not c.startswith('PASTE_')])}")
    return valid


class Worker:
    def __init__(self, name, cookie, bid):
        self.name = name
        self.s = tls_client.Session(client_identifier=bid, random_tls_extension_order=True)
        self.s.cookies.set("datadome", cookie, domain=".datashield.co")
        self.blocked = False
        self.count = 0

    def headers(self, ref):
        return {
            "host": "bounty-nginx.datashield.co",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml",
            "referer": ref,
        }


def work(w):
    while not stop.is_set():
        with lock:
            if len(results) >= TARGET_COUNT:
                return
        if (time.time() - start_time) > TIME_LIMIT:
            return
        try:
            path, ref = job_queue.get(timeout=1)
        except Empty:
            continue
        if w.blocked:
            job_queue.put((path, ref))
            return

        time.sleep(random.uniform(0.05, DELAY_PER_REQ))
        try:
            r = w.s.get(f"{BASE_URL}{path}", headers=w.headers(ref), timeout_seconds=10)
            if r.status_code == 200:
                w.count += 1
                h = hash_re.search(r.text[:1000])
                links = set(link_re.findall(r.text))
                with lock:
                    results.append({"path": path, "hash": h.group(1) if h else None, "status": 200})
                    n = len(results)
                    if n % 10 == 0:
                        el = time.time() - start_time
                        rps = n / el if el > 0 else 0
                        sys.stdout.write(f"\r[{ts()}] {n}/{TARGET_COUNT} | {rps:.2f} RPS | Q:{job_queue.qsize()}  ")
                        sys.stdout.flush()
                    if n % CHECKPOINT == 0:
                        checkpoint(n)
                with lock:
                    for l in links:
                        if l not in visited:
                            visited.add(l)
                            job_queue.put((l, f"{BASE_URL}{path}"))
            elif r.status_code in [403, 429]:
                if not w.blocked:
                    print(f"\n[{ts()}] {w.name} blocked")
                    w.blocked = True
                job_queue.put((path, ref))
        except:
            job_queue.put((path, ref))
        finally:
            job_queue.task_done()


def run():
    global job_queue, visited, results, start_time, last_cp
    
    valid = test_all()
    if not valid:
        print("No valid cookies")
        return

    job_queue = Queue()
    job_queue.put((START_PATH, BASE_URL))
    visited = set([START_PATH])
    results = []
    last_cp = 0

    workers = [Worker(n, c, b) for c, b, n in valid]
    threads = len(workers) * THREADS_PER_COOKIE

    print(f"\n[{ts()}] Starting: {len(valid)} cookies, {threads} threads")
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            for w in workers:
                for _ in range(THREADS_PER_COOKIE):
                    ex.submit(work, w)
            while not stop.is_set():
                with lock:
                    if len(results) >= TARGET_COUNT:
                        break
                if (time.time() - start_time) > TIME_LIMIT:
                    break
                time.sleep(0.5)
    except:
        pass

    elapsed = time.time() - start_time
    rps = len(results) / elapsed if elapsed > 0 else 0
    print(f"\n\n[{ts()}] Done: {len(results)} pages | {int(elapsed)}s | {rps:.2f} RPS")
    for w in workers:
        st = "blocked" if w.blocked else "ok"
        print(f"  {w.name}: {w.count} ({st})")
    save()
    print(f"[{ts()}] Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper_multi.py [test|run]")
    elif sys.argv[1] == "test":
        test_all()
    elif sys.argv[1] == "run":
        run()
