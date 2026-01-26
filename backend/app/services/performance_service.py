"""Performance testing service using k6 load testing tool."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Storage for test results
_RESULTS_DIR = Path(__file__).resolve().parents[1] / "data" / "performance_tests"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class PerformanceTestError(RuntimeError):
    """Raised when performance test execution fails."""


def generate_test_id(test_type: str) -> str:
    """Generate unique test ID with timestamp and type."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"perftest_{timestamp}_{test_type}_{unique_id}"


def _generate_k6_script(
    target_url: str,
    config: Dict[str, Any]
) -> str:
    """Generate k6 JavaScript test script based on configuration."""
    
    test_type = config.get("test_type", "load")
    vus = config.get("vus", 10)
    duration = config.get("duration", "30s")
    endpoints = config.get("endpoints", [{"method": "GET", "path": "/health"}])
    headers = config.get("headers", {})
    
    # Build headers object
    headers_js = json.dumps(headers) if headers else "{}"
    
    # Build endpoint requests
    endpoint_calls = []
    for idx, endpoint in enumerate(endpoints):
        method = endpoint.get("method", "GET").upper()
        path = endpoint.get("path", "/")
        url = f"{target_url.rstrip('/')}{path}"
        
        if method == "GET":
            endpoint_calls.append(f"    http.get('{url}', {{ headers: headers }});")
        elif method == "POST":
            endpoint_calls.append(f"    http.post('{url}', '', {{ headers: headers }});")
        elif method == "PUT":
            endpoint_calls.append(f"    http.put('{url}', '', {{ headers: headers }});")
        elif method == "DELETE":
            endpoint_calls.append(f"    http.del('{url}', '', {{ headers: headers }});")
    
    endpoint_code = "\n".join(endpoint_calls) if endpoint_calls else f"    http.get('{target_url}', {{ headers: headers }});"
    
    # Generate stages based on test type
    stages = _generate_stages(test_type, config)
    
    # Build thresholds
    thresholds = config.get("thresholds", {
        "http_req_duration": ["p(95)<500", "p(99)<1000"],
        "http_req_failed": ["rate<0.1"],
    })
    thresholds_js = json.dumps(thresholds)
    
    script = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export let options = {{
  stages: {stages},
  thresholds: {thresholds_js}
}};

const headers = {headers_js};

export default function() {{
{endpoint_code}
  sleep(1);
}}
"""
    
    return script


def _generate_stages(test_type: str, config: Dict[str, Any]) -> str:
    """Generate k6 stages configuration based on test type."""
    
    vus = config.get("vus", 10)
    duration = config.get("duration", "30s")
    
    if test_type == "smoke":
        return json.dumps([
            {"duration": "1m", "target": 5},
            {"duration": "1m", "target": 5},
        ])
    
    elif test_type == "load":
        ramp_up = config.get("ramp_up", "30s")
        return json.dumps([
            {"duration": ramp_up, "target": vus},
            {"duration": duration, "target": vus},
            {"duration": "30s", "target": 0},
        ])
    
    elif test_type == "stress":
        return json.dumps([
            {"duration": "2m", "target": vus},
            {"duration": "3m", "target": int(vus * 1.5)},
            {"duration": "3m", "target": int(vus * 2)},
            {"duration": "3m", "target": int(vus * 2.5)},
            {"duration": "3m", "target": int(vus * 3)},
            {"duration": "2m", "target": 0},
        ])
    
    elif test_type == "spike":
        return json.dumps([
            {"duration": "1m", "target": vus},
            {"duration": "30s", "target": vus * 5},
            {"duration": "1m", "target": vus * 5},
            {"duration": "30s", "target": vus},
            {"duration": "1m", "target": 0},
        ])
    
    elif test_type == "capacity":
        max_vus = config.get("max_vus", vus * 10)
        step_vus = max(10, vus)
        stages = []
        current_vus = vus
        
        while current_vus <= max_vus:
            stages.append({"duration": "3m", "target": current_vus})
            current_vus += step_vus
        
        stages.append({"duration": "5m", "target": max_vus})
        stages.append({"duration": "3m", "target": 0})
        
        return json.dumps(stages)
    
    elif test_type == "soak":
        soak_duration = config.get("soak_duration", "30m")
        soak_vus = int(vus * 0.7)
        return json.dumps([
            {"duration": "5m", "target": soak_vus},
            {"duration": soak_duration, "target": soak_vus},
            {"duration": "5m", "target": 0},
        ])
    
    else:
        # Default to simple load test
        return json.dumps([
            {"duration": "1m", "target": vus},
            {"duration": duration, "target": vus},
            {"duration": "30s", "target": 0},
        ])


def run_k6_test(
    test_id: str,
    target_url: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute k6 performance test and return results."""
    
    logger.info(
        "Starting k6 performance test",
        extra={
            "test_id": test_id,
            "target_url": target_url,
            "test_type": config.get("test_type"),
        }
    )
    
    # Check if k6 is installed
    try:
        subprocess.run(
            ["k6", "version"],
            capture_output=True,
            check=True,
            timeout=5
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("k6 not installed, using mock results")
        return _generate_mock_results(test_id, target_url, config)
    
    # Generate k6 script
    script_content = _generate_k6_script(target_url, config)
    
    # Create temporary script file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.js',
        delete=False
    ) as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    
    # Create temporary file for JSON output
    json_output_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False
    )
    json_output_path = json_output_file.name
    json_output_file.close()
    
    try:
        # Run k6 test with JSON output to file
        result = subprocess.run(
            [
                "k6", "run",
                "--out", f"json={json_output_path}",
                script_path
            ],
            capture_output=True,
            timeout=config.get("timeout", 300),
            text=True
        )
        
        # Read JSON output from file
        with open(json_output_path, 'r') as f:
            json_output = f.read()
        
        # Parse k6 output
        metrics = _parse_k6_output(json_output)
        
        # Save results
        test_result = {
            "test_id": test_id,
            "target_url": target_url,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "config": config,
            "metrics": metrics,
            "k6_version": _get_k6_version()
        }
        
        _save_test_result(test_id, test_result)
        
        logger.info(
            "k6 test completed successfully",
            extra={"test_id": test_id, "requests": metrics.get("requests", {}).get("total", 0)}
        )
        
        return test_result
        
    except subprocess.TimeoutExpired:
        error_msg = f"k6 test timed out after {config.get('timeout', 300)} seconds"
        logger.error(error_msg, extra={"test_id": test_id})
        raise PerformanceTestError(error_msg)
    
    except Exception as exc:
        logger.exception("k6 test execution failed", extra={"test_id": test_id})
        raise PerformanceTestError(f"k6 execution failed: {str(exc)}") from exc
    
    finally:
        # Clean up files
        try:
            Path(script_path).unlink()
        except:
            pass
        try:
            Path(json_output_path).unlink()
        except:
            pass


def _get_k6_version() -> str:
    """Get k6 version string."""
    try:
        result = subprocess.run(
            ["k6", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return "unknown"


def _parse_k6_output(output: str) -> Dict[str, Any]:
    """Parse k6 JSON output and extract metrics."""
    
    metrics = {
        "requests": {
            "total": 0,
            "rate": 0.0,
            "failed_rate": 0.0
        },
        "response_time": {
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0
        },
        "virtual_users": {
            "max": 0,
            "avg": 0.0
        },
        "checks": {
            "passed": 0,
            "failed": 0,
            "pass_rate": 100.0
        }
    }
    
    if not output:
        return metrics
    
    # Parse JSON lines from k6 output
    lines = output.strip().split('\n')
    durations = []
    vus = []
    
    for line in lines:
        try:
            data = json.loads(line)
            metric_type = data.get("type")
            metric_data = data.get("data", {})
            
            if metric_type == "Point":
                metric_name = data.get("metric")
                value = metric_data.get("value", 0)
                
                if metric_name == "http_req_duration":
                    durations.append(value)
                elif metric_name == "vus":
                    vus.append(value)
                elif metric_name == "http_reqs":
                    metrics["requests"]["total"] += 1
        except:
            continue
    
    # Calculate statistics
    if durations:
        durations.sort()
        metrics["response_time"]["avg"] = sum(durations) / len(durations)
        metrics["response_time"]["min"] = min(durations)
        metrics["response_time"]["max"] = max(durations)
        metrics["response_time"]["p50"] = durations[int(len(durations) * 0.5)]
        metrics["response_time"]["p95"] = durations[int(len(durations) * 0.95)]
        metrics["response_time"]["p99"] = durations[int(len(durations) * 0.99)]
    
    if vus:
        metrics["virtual_users"]["max"] = max(vus)
        metrics["virtual_users"]["avg"] = sum(vus) / len(vus)
    
    if metrics["requests"]["total"] > 0:
        metrics["requests"]["rate"] = metrics["requests"]["total"] / max(1, len(durations))
    
    return metrics


def _generate_mock_results(
    test_id: str,
    target_url: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate mock performance test results when k6 is not available."""
    
    import random
    
    vus = config.get("vus", 10)
    total_requests = vus * 60  # Simulated requests
    
    metrics = {
        "requests": {
            "total": total_requests,
            "rate": vus,
            "failed_rate": random.uniform(0.5, 2.0)
        },
        "response_time": {
            "avg": random.uniform(100, 300),
            "min": random.uniform(50, 100),
            "max": random.uniform(400, 800),
            "p50": random.uniform(150, 250),
            "p95": random.uniform(300, 500),
            "p99": random.uniform(500, 700)
        },
        "virtual_users": {
            "max": vus,
            "avg": vus * 0.8
        },
        "checks": {
            "passed": int(total_requests * 0.95),
            "failed": int(total_requests * 0.05),
            "pass_rate": 95.0
        }
    }
    
    test_result = {
        "test_id": test_id,
        "target_url": target_url,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "config": config,
        "metrics": metrics,
        "k6_version": "mock (k6 not installed)",
        "_mock": True
    }
    
    _save_test_result(test_id, test_result)
    
    logger.info(
        "Mock performance test completed",
        extra={"test_id": test_id, "requests": total_requests}
    )
    
    return test_result


def _save_test_result(test_id: str, result: Dict[str, Any]) -> None:
    """Save test result to disk."""
    
    result_path = _RESULTS_DIR / f"{test_id}.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def get_performance_test(test_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored performance test result."""
    
    result_path = _RESULTS_DIR / f"{test_id}.json"
    
    if not result_path.exists():
        return None
    
    try:
        with result_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"Failed to load test result {test_id}: {exc}")
        return None


def list_performance_tests(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent performance test results."""
    
    results = []
    
    for result_path in sorted(_RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            with result_path.open("r", encoding="utf-8") as f:
                result = json.load(f)
                results.append(result)
                
                if len(results) >= limit:
                    break
        except Exception as exc:
            logger.debug(f"Skipping unreadable result file {result_path}: {exc}")
            continue
    
    return results



def format_performance_test_response(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Format complete performance test results for API response."""
    
    metrics = test_result.get("metrics", {})
    requests_data = metrics.get("requests", {})
    response_time = metrics.get("response_time", {})
    virtual_users = metrics.get("virtual_users", {})
    checks = metrics.get("checks", {})
    
    # Calculate success rate
    total_requests = requests_data.get("total", 0)
    failed_rate = requests_data.get("failed_rate", 0)
    success_rate = 100.0 - failed_rate if failed_rate < 100 else 0.0
    
    return {
        "test_id": test_result.get("test_id"),
        "status": test_result.get("status"),
        "message": f"Load test completed. Total requests: {total_requests}",
        "target_url": test_result.get("target_url"),
        "timestamp": test_result.get("timestamp"),
        "test_config": {
            "test_type": test_result.get("config", {}).get("test_type"),
            "virtual_users": test_result.get("config", {}).get("vus"),
            "duration": test_result.get("config", {}).get("duration"),
            "endpoints": test_result.get("config", {}).get("endpoints")
        },
        "performance_metrics": {
            "requests": {
                "total": total_requests,
                "rate_per_second": round(requests_data.get("rate", 0), 2),
                "failed_rate_percent": round(failed_rate, 2),
                "success_rate_percent": round(success_rate, 2)
            },
            "response_time_ms": {
                "average": round(response_time.get("avg", 0), 2),
                "minimum": round(response_time.get("min", 0), 2),
                "maximum": round(response_time.get("max", 0), 2),
                "median_p50": round(response_time.get("p50", 0), 2),
                "percentile_95": round(response_time.get("p95", 0), 2),
                "percentile_99": round(response_time.get("p99", 0), 2)
            },
            "virtual_users": {
                "maximum": virtual_users.get("max", 0),
                "average": round(virtual_users.get("avg", 0), 2)
            },
            "checks": {
                "passed": checks.get("passed", 0),
                "failed": checks.get("failed", 0),
                "pass_rate_percent": round(checks.get("pass_rate", 100.0), 2)
            }
        },
        "system_info": {
            "k6_version": test_result.get("k6_version"),
            "is_mock": test_result.get("_mock", False)
        },
        "performance_summary": {
            "status": _get_performance_status(response_time, failed_rate),
            "bottlenecks": _identify_bottlenecks(metrics),
            "recommendations": _generate_recommendations(metrics, test_result.get("config", {}))
        }
    }


def _get_performance_status(response_time: Dict[str, Any], failed_rate: float) -> str:
    """Determine overall performance status."""
    avg_time = response_time.get("avg", 0)
    p95_time = response_time.get("p95", 0)
    
    if failed_rate > 10:
        return "CRITICAL - High failure rate"
    elif failed_rate > 5:
        return "WARNING - Elevated failure rate"
    elif p95_time > 1000:
        return "WARNING - High response times"
    elif avg_time > 500:
        return "FAIR - Moderate response times"
    elif avg_time < 200:
        return "EXCELLENT - Fast response times"
    else:
        return "GOOD - Acceptable performance"


def _identify_bottlenecks(metrics: Dict[str, Any]) -> List[str]:
    """Identify potential performance bottlenecks."""
    bottlenecks = []
    
    response_time = metrics.get("response_time", {})
    requests_data = metrics.get("requests", {})
    
    avg_time = response_time.get("avg", 0)
    p95_time = response_time.get("p95", 0)
    p99_time = response_time.get("p99", 0)
    failed_rate = requests_data.get("failed_rate", 0)
    
    if failed_rate > 5:
        bottlenecks.append(f"High failure rate: {failed_rate:.1f}%")
    
    if avg_time > 500:
        bottlenecks.append(f"Slow average response time: {avg_time:.0f}ms")
    
    if p95_time > 1000:
        bottlenecks.append(f"High P95 latency: {p95_time:.0f}ms")
    
    if p99_time > 2000:
        bottlenecks.append(f"Very high P99 latency: {p99_time:.0f}ms")
    
    # Check for high variance
    if p99_time > avg_time * 3:
        bottlenecks.append("High latency variance - inconsistent performance")
    
    if not bottlenecks:
        bottlenecks.append("No significant bottlenecks detected")
    
    return bottlenecks


def _generate_recommendations(metrics: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    """Generate performance improvement recommendations."""
    recommendations = []
    
    response_time = metrics.get("response_time", {})
    requests_data = metrics.get("requests", {})
    
    avg_time = response_time.get("avg", 0)
    failed_rate = requests_data.get("failed_rate", 0)
    vus = config.get("vus", 10)
    
    if failed_rate > 5:
        recommendations.append("Investigate server errors and failed requests")
        recommendations.append("Check server logs for error patterns")
    
    if avg_time > 500:
        recommendations.append("Optimize database queries and API calls")
        recommendations.append("Consider implementing caching strategies")
        recommendations.append("Review application code for performance bottlenecks")
    
    if response_time.get("p95", 0) > avg_time * 2:
        recommendations.append("Investigate outlier requests causing high latency")
        recommendations.append("Consider implementing request timeouts")
    
    if vus > 50 and avg_time > 1000:
        recommendations.append("Consider horizontal scaling to handle load")
        recommendations.append("Evaluate current infrastructure capacity")
    
    if not recommendations:
        recommendations.append("Performance is acceptable for current load")
        recommendations.append("Consider stress testing with higher VUs to find limits")
    
    return recommendations


__all__ = [
    "PerformanceTestError",
    "generate_test_id",
    "run_k6_test",
    "get_performance_test",
    "list_performance_tests",
    "format_performance_test_response",
]