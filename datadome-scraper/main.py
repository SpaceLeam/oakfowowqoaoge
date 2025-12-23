#!/usr/bin/env python3
"""
DataDome Scraper - Entry Point
Target: bounty-nginx.datashield.co
Scenario: Medium (20,000 pages in 30 minutes)

USAGE:
    python main.py --cookie "YOUR_DATADOME_COOKIE_VALUE"

CARA DAPAT COOKIE:
    1. Buka https://bounty-nginx.datashield.co/scraping/0001 di browser
    2. Selesaikan CAPTCHA jika ada
    3. Buka DevTools > Application > Cookies
    4. Copy value dari cookie "datadome"
"""

import argparse
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from scrapers.datadome_scraper import DataDomeScraper


def main():
    parser = argparse.ArgumentParser(
        description='DataDome Scraper untuk Bug Bounty (Medium Scenario)'
    )
    parser.add_argument(
        '--cookie', '-c',
        required=True,
        help='DataDome cookie value (dapatkan dari browser setelah solve CAPTCHA)'
    )
    parser.add_argument(
        '--output', '-o',
        default='results.json',
        help='Output file untuk hasil scraping (default: results.json)'
    )
    parser.add_argument(
        '--target', '-t',
        type=int,
        default=20000,
        help='Target jumlah pages (default: 20000)'
    )
    parser.add_argument(
        '--rps',
        type=float,
        default=12.0,
        help='Target requests per second (default: 12.0)'
    )
    
    args = parser.parse_args()
    
    # Update config jika ada override
    if args.target:
        config.TARGET_REQUESTS = args.target
    if args.rps:
        config.TARGET_RPS = args.rps
    
    print("=" * 60)
    print("   DATADOME SCRAPER - NGINX OPTIMIZED (MEDIUM SCENARIO)")
    print("=" * 60)
    print(f"Target URL: {config.BASE_URL}")
    print(f"Target Pages: {config.TARGET_REQUESTS}")
    print(f"Target RPS: {config.TARGET_RPS}")
    print(f"Time Limit: {config.TIME_LIMIT}s ({config.TIME_LIMIT//60} minutes)")
    print("=" * 60)
    
    # Initialize scraper
    scraper = DataDomeScraper(config, args.cookie)
    
    # Run
    try:
        summary = scraper.run()
        
        # Save results
        scraper.save_results(args.output)
        
        # Report untuk bug bounty
        print("\n" + "=" * 60)
        print("   REPORT DATA (untuk submission)")
        print("=" * 60)
        print(f"Total scraped: {summary['total_requests']}")
        print(f"Time taken: {summary['total_time_seconds']:.1f}s")
        print(f"Speed: {summary['final_rps']:.2f} hits/sec")
        print(f"Blocked: {'YES' if scraper.blocked else 'NO'}")
        print(f"Results file: {args.output}")
        
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        scraper.save_results(args.output)


if __name__ == "__main__":
    main()
