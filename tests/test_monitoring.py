import pytest
from ai_project.api.monitoring import PhoenixMonitor

def test_monitoring_request_lifecycle():
    monitor = PhoenixMonitor()
    
    # Check initial values
    metrics = monitor.get_metrics()
    assert metrics["api"]["total_requests"] == 0
    assert metrics["api"]["active_requests"] == 0
    assert metrics["api"]["successful_requests"] == 0
    assert metrics["api"]["failed_requests"] == 0
    assert metrics["api"]["avg_response_latency_seconds"] == 0.0

    # Start a request
    monitor.start_request()
    metrics = monitor.get_metrics()
    assert metrics["api"]["total_requests"] == 1
    assert metrics["api"]["active_requests"] == 1

    # End first request successfully
    monitor.end_request(latency=0.15, success=True)
    metrics = monitor.get_metrics()
    assert metrics["api"]["active_requests"] == 0
    assert metrics["api"]["successful_requests"] == 1
    assert metrics["api"]["avg_response_latency_seconds"] == 0.15

    # Start and fail second request
    monitor.start_request()
    monitor.end_request(latency=0.35, success=False)
    metrics = monitor.get_metrics()
    assert metrics["api"]["total_requests"] == 2
    assert metrics["api"]["successful_requests"] == 1
    assert metrics["api"]["failed_requests"] == 1
    # Average of 0.15 and 0.35 is 0.25
    assert metrics["api"]["avg_response_latency_seconds"] == 0.25

def test_monitoring_llm_generation():
    monitor = PhoenixMonitor()
    
    # Check initial values
    metrics = monitor.get_metrics()
    assert metrics["llm"]["sessions_count"] == 0
    assert metrics["llm"]["total_tokens_generated"] == 0
    assert metrics["llm"]["avg_prefill_time_seconds"] == 0.0
    assert metrics["llm"]["avg_decode_time_seconds"] == 0.0
    assert metrics["llm"]["tokens_per_second"] == 0.0

    # Record first generation session
    # 100 tokens, 0.05s prefill, 1.25s decode -> 80 tokens/sec
    monitor.record_generation(num_tokens=100, prefill_time=0.05, decode_time=1.25)
    metrics = monitor.get_metrics()
    assert metrics["llm"]["sessions_count"] == 1
    assert metrics["llm"]["total_tokens_generated"] == 100
    assert metrics["llm"]["avg_prefill_time_seconds"] == 0.05
    assert metrics["llm"]["avg_decode_time_seconds"] == 1.25
    assert metrics["llm"]["tokens_per_second"] == 80.0

    # Record second generation session
    # 50 tokens, 0.03s prefill, 0.75s decode -> 2.0s total decode time, 150 total tokens -> 75 tokens/sec average
    monitor.record_generation(num_tokens=50, prefill_time=0.03, decode_time=0.75)
    metrics = monitor.get_metrics()
    assert metrics["llm"]["sessions_count"] == 2
    assert metrics["llm"]["total_tokens_generated"] == 150
    assert metrics["llm"]["avg_prefill_time_seconds"] == 0.04  # average of 0.05 and 0.03
    assert metrics["llm"]["avg_decode_time_seconds"] == 1.0   # average of 1.25 and 0.75
    assert metrics["llm"]["tokens_per_second"] == 75.0        # 150 / 2.0
