"""
ML-resistant Timing Controller
Burst pattern, cooldown, variance >15%
"""

import random
import time
from typing import Optional


class TimingController:
    def __init__(self, config):
        self.config = config
        
        # Burst state
        self.burst_counter = 0
        self.burst_size = random.randint(
            config.BURST_SIZE_MIN,
            config.BURST_SIZE_MAX
        )
        
        # Cooldown state
        self.cooldown_at = random.randint(
            config.COOLDOWN_EVERY_MIN,
            config.COOLDOWN_EVERY_MAX
        )

    def calculate_delay(self, request_count: int) -> float:
        """
        Generate delay dengan:
        1. Cooldown pattern (setiap ~500 request)
        2. Burst pattern (8-15 request cepat, lalu pause)
        3. Base delay dengan variance >15%
        4. Think time random
        """
        
        # 1. Cooldown check
        if request_count > 0 and request_count % self.cooldown_at == 0:
            # Reset cooldown target
            self.cooldown_at = random.randint(
                self.config.COOLDOWN_EVERY_MIN,
                self.config.COOLDOWN_EVERY_MAX
            )
            return random.uniform(
                self.config.COOLDOWN_DURATION_MIN,
                self.config.COOLDOWN_DURATION_MAX
            )
        
        # 2. Burst pattern
        self.burst_counter += 1
        if self.burst_counter >= self.burst_size:
            self.burst_counter = 0
            self.burst_size = random.randint(
                self.config.BURST_SIZE_MIN,
                self.config.BURST_SIZE_MAX
            )
            return random.uniform(
                self.config.BURST_INTERVAL_MIN,
                self.config.BURST_INTERVAL_MAX
            )
        
        # 3. Base delay (1/RPS) dengan variance
        base_delay = 1.0 / self.config.TARGET_RPS
        variance = random.uniform(
            -self.config.REQUEST_VARIANCE,
            self.config.REQUEST_VARIANCE
        )
        
        # 4. Think time
        think_time = random.uniform(
            self.config.THINK_TIME_MIN,
            self.config.THINK_TIME_MAX
        )
        
        final_delay = base_delay * (1 + variance) + think_time
        return max(0, final_delay)
