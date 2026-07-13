from app.models import Evidence


def check_upstream_dependencies(service: str) -> list[Evidence]:
    """Simulate checking upstream dependency health (DB, cache, etc.)."""
    return [
        Evidence(source="dependency-db", detail=f"Database connection pool usage at 87% (threshold 80%), {service} is the top consumer."),
        Evidence(source="dependency-cache", detail="Redis cluster hit rate 94%, no replication lag."),
        Evidence(source="dependency-pg", detail="Payment gateway upstream latency increased 2x in last 15 min (180ms vs 90ms baseline)."),
    ]


def inspect_service_health(service: str) -> list[Evidence]:
    """A deliberately read-only diagnostic tool; replace with real observability queries."""
    return [
        Evidence(source="health-check", detail=f"{service} returned HTTP 503 for 18% of requests."),
        Evidence(source="metrics", detail="Error rate started increasing 12 minutes ago after a deployment."),
        Evidence(source="runbook", detail="For elevated 503s, verify upstream connection-pool saturation before rollback."),
    ]


def inspect_service_logs(service: str) -> list[Evidence]:
    log_path = f"sample_logs/{service}.log"
    try:
        with open(log_path, encoding="utf-8") as log_file:
            lines = [line.strip() for line in log_file if line.strip()]
    except FileNotFoundError:
        return [Evidence(source="logs", detail=f"No local sample log found at {log_path}.")]

    error_lines = [line for line in lines if " ERROR " in line or " WARN " in line or " status=5" in line]
    if not error_lines:
        return [Evidence(source="logs", detail=f"{service} sample log has no warning or error entries.")]

    latest = error_lines[-1]
    repeated_pool_errors = sum("connection pool exhausted" in line for line in error_lines)
    return [
        Evidence(source="logs", detail=f"Found {len(error_lines)} warning/error entries in {log_path}."),
        Evidence(source="logs", detail=f"Latest suspicious entry: {latest}"),
        Evidence(source="logs", detail=f"Connection-pool exhaustion appears {repeated_pool_errors} times."),
    ]
