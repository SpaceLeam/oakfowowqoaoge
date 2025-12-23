"""
ML-resistant Timing Controller (2025 December Edition)
Activity phases, entropy >4.5 bits, API timeout exploitation
"""

import random
import time
import numpy as np
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
        
        # 2025: Activity phase state
        self.phase_start = time.time()
        self.in_active_phase = True
        self.active_phase_duration = random.uniform(
            config.ACTIVE_PHASE_MIN,
            config.ACTIVE_PHASE_MAX
        )
        self.rest_phase_duration = random.uniform(
            config.REST_PHASE_MIN,
            config.REST_PHASE_MAX
        )
        
        # 2025: Timing history untuk entropy calculation
        self.timing_history = []

    def calculate_delay(self, request_count: int, api_response_time: float = 0) -> float:
        """
        Generate delay dengan:
        1. Cooldown pattern
        2. Activity phases (2025)
        3. Burst pattern  
        4. API timeout exploitation (2025)
        5. Base delay dengan variance >15%
        6. Think time random
        """
        
        # 1. Cooldown check
        if request_count > 0 and request_count % self.cooldown_at == 0:
            self.cooldown_at = random.randint(
                self.config.COOLDOWN_EVERY_MIN,
                self.config.COOLDOWN_EVERY_MAX
            )
            cooldown = random.uniform(
                self.config.COOLDOWN_DURATION_MIN,
                self.config.COOLDOWN_DURATION_MAX
            )
            self.timing_history.append(cooldown)
            return cooldown
        
        # 2. Activity phase check (2025)
        elapsed = time.time() - self.phase_start
        if self.in_active_phase and elapsed > self.active_phase_duration:
            self.in_active_phase = False
            self.phase_start = time.time()
            self.rest_phase_duration = random.uniform(
                self.config.REST_PHASE_MIN,
                self.config.REST_PHASE_MAX
            )
            rest = self.rest_phase_duration
            print(f"\n[REST PHASE] {rest:.1f}s break")
            self.timing_history.append(rest)
            return rest
        elif not self.in_active_phase and elapsed > self.rest_phase_duration:
            self.in_active_phase = True
            self.phase_start = time.time()
            self.active_phase_duration = random.uniform(
                self.config.ACTIVE_PHASE_MIN,
                self.config.ACTIVE_PHASE_MAX
            )
        
        # 3. Burst pattern
        self.burst_counter += 1
        if self.burst_counter >= self.burst_size:
            self.burst_counter = 0
            self.burst_size = random.randint(
                self.config.BURST_SIZE_MIN,
                self.config.BURST_SIZE_MAX
            )
            burst_delay = random.uniform(
                self.config.BURST_INTERVAL_MIN,
                self.config.BURST_INTERVAL_MAX
            )
            self.timing_history.append(burst_delay)
            return burst_delay
        
        # 4. Exploit API timeout (aggressive when API slow)
        if (self.config.FAST_BURST_ON_SLOW_API and 
            api_response_time > self.config.RESPONSE_TIME_THRESHOLD):
            aggressive_delay = random.uniform(0.02, 0.05)
            self.timing_history.append(aggressive_delay)
            return aggressive_delay
        
        # 5. Base delay dengan variance
        base_delay = 1.0 / self.config.TARGET_RPS
        variance = random.uniform(
            -self.config.REQUEST_VARIANCE,
            self.config.REQUEST_VARIANCE
        )
        
        # 6. Think time
        think_time = random.uniform(
            self.config.THINK_TIME_MIN,
            self.config.THINK_TIME_MAX
        )
        
        final_delay = base_delay * (1 + variance) + think_time
        self.timing_history.append(final_delay)
        return max(0, final_delay)

    def get_entropy(self) -> float:
        """
        Calculate Shannon entropy (2025 requirement)
        Target: >4.5 bits
        """
        if len(self.timing_history) < 20:
            return 0.0
        
        recent = self.timing_history[-100:]
        hist, _ = np.histogram(recent, bins=20)
        prob = hist / hist.sum()
        entropy = -np.sum(prob * np.log2(prob + 1e-10))
        
        return entropy
