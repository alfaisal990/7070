import time
from typing import Dict, Any

class PhoenixMonitor:
    """
    Performance Metrics Collector & Latency Profiler for Phoenix AI.
    Tracks API traffic and profiles LLM generation throughput.
    """
    def __init__(self):
        # API Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.active_requests = 0
        self.accumulated_latency = 0.0

        # LLM Generation Metrics
        self.total_tokens_generated = 0
        self.total_prefill_time = 0.0
        self.total_decode_time = 0.0
        self.generation_sessions = 0

    def start_request(self):
        self.total_requests += 1
        self.active_requests += 1

    def end_request(self, latency: float, success: bool = True):
        self.active_requests = max(0, self.active_requests - 1)
        self.accumulated_latency += latency
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def record_generation(self, num_tokens: int, prefill_time: float, decode_time: float):
        if num_tokens > 0:
            self.total_tokens_generated += num_tokens
            self.total_prefill_time += prefill_time
            self.total_decode_time += decode_time
            self.generation_sessions += 1

    def get_metrics(self) -> Dict[str, Any]:
        avg_latency = (
            self.accumulated_latency / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        avg_tokens_per_sec = 0.0
        if self.total_decode_time > 0:
            # Tokens per second during generation decode phase
            # (only decode tokens, which is total_tokens_generated - prefill_sessions)
            # Or simpler: total generated divided by total decode time
            avg_tokens_per_sec = self.total_tokens_generated / self.total_decode_time

        avg_prefill_latency = (
            self.total_prefill_time / self.generation_sessions
            if self.generation_sessions > 0 else 0.0
        )

        return {
            "api": {
                "total_requests": self.total_requests,
                "active_requests": self.active_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "avg_response_latency_seconds": round(avg_latency, 3),
            },
            "llm": {
                "sessions_count": self.generation_sessions,
                "total_tokens_generated": self.total_tokens_generated,
                "avg_prefill_time_seconds": round(avg_prefill_latency, 3),
                "avg_decode_time_seconds": round(
                    self.total_decode_time / self.generation_sessions
                    if self.generation_sessions > 0 else 0.0, 3
                ),
                "tokens_per_second": round(avg_tokens_per_sec, 2),
            }
        }
