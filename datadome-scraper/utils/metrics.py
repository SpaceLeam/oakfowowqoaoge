"""
Real-time Metrics Tracking
"""

import sys
import time
from typing import Dict


class MetricsTracker:
    def __init__(self):
        self.errors = 0
        self.blocks = 0
        self.success = 0

    def print_progress(self, count: int, start_time: float, current_path: str):
        """Live progress display"""
        elapsed = time.time() - start_time
        rps = count / elapsed if elapsed > 0 else 0
        remaining = 20000 - count
        eta = remaining / rps if rps > 0 else 0

        sys.stdout.write(
            f"\r[*] {count}/20000 | "
            f"{rps:.2f} RPS | "
            f"ETA: {eta:.0f}s | "
            f"{current_path}"
        )
        sys.stdout.flush()

    def get_summary(self, count: int, start_time: float) -> Dict:
        """Final metrics summary"""
        total_time = time.time() - start_time
        return {
            'total_requests': count,
            'total_time_seconds': total_time,
            'final_rps': count / total_time if total_time > 0 else 0,
            'success': self.success,
            'errors': self.errors,
            'blocks': self.blocks
        }
