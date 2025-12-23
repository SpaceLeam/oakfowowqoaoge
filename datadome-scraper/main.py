#!/usr/bin/env python3
"""
DataDome Scraper - Entry Point (2025 December Edition)
Auto-generates unique output filenames with timestamp
"""

import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from scrapers.datadome_scraper import DataDomeScraper


def get_unique_filename():
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"results_{timestamp}.json"


def main():
    parser = argparse.ArgumentParser(
        description='DataDome Scraper - 2025 December Edition'
    )
    parser.add_argument(
        '--cookie', '-c',
        required=True,
        help='DataDome cookie value'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output file (default: auto-generated timestamp)'
    )
    parser.add_argument(
        '--target', '-t',
        type=int,
        default=20000,
        help='Target pages (default: 20000)'
    )
    parser.add_argument(
        '--rps',
        type=float,
        default=15.0,
        help='Target RPS (default: 15.0)'
    )
    
    args = parser.parse_args()
    
    # Auto-generate unique filename if not specified
    output_file = args.output if args.output else get_unique_filename()
    
    if args.target:
        config.TARGET_REQUESTS = args.target
    if args.rps:
        config.TARGET_RPS = args.rps
    
    print("=" * 60)
    print("   DATADOME SCRAPER - 2025 DECEMBER EDITION")
    print("=" * 60)
    print(f"Target URL: {config.BASE_URL}")
    print(f"Target Pages: {config.TARGET_REQUESTS}")
    print(f"Target RPS: {config.TARGET_RPS}")
    print(f"Time Limit: {config.TIME_LIMIT}s ({config.TIME_LIMIT//60} minutes)")
    print(f"Output: {output_file}")
    print("=" * 60)
    
    scraper = DataDomeScraper(config, args.cookie)
    
    try:
        summary = scraper.run()
        scraper.save_results(output_file)
        
        print("\n" + "=" * 60)
        print("   REPORT DATA")
        print("=" * 60)
        print(f"Total scraped: {summary['total_requests']}")
        print(f"Time taken: {summary['total_time_seconds']:.1f}s")
        print(f"Speed: {summary['final_rps']:.2f} hits/sec")
        print(f"Entropy: {summary.get('entropy', 0):.2f} bits")
        print(f"Blocked: {'YES' if scraper.blocked else 'NO'}")
        print(f"Results file: {output_file}")
        
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        scraper.save_results(output_file)
        print(f"[*] Partial results saved to {output_file}")


if __name__ == "__main__":
    main()
