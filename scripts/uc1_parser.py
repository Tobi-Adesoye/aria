import re

# Strict regex matching string for master, bus, and utility cluster logs
CLUSTER_LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+"
    r"\[(?P<cluster_node>[^\]]+)\]\s+"
    r"(?P<severity>INFO|WARN|ERROR|CRITICAL):\s+"
    r"(?P<message>.*)$"
)

def validate_runbook_entry(raw_log: str) -> dict:
    """
    Parses unstructured multi-node telemetry inputs safely.
    """
    match = CLUSTER_LOG_PATTERN.match(raw_log.strip())
    if not match:
        return {
            "status": "MALFORMED_ENTRY", 
            "raw": raw_log,
            "severity": "UNKNOWN"
        }
    
    return {
        "status": "PARSED",
        **match.groupdict()
    }

if __name__ == "__main__":
    # Test execution trace
    test_log = "2026-06-09T06:05:00.123Z [cdp-master-01] ERROR: OutOfMemory exception encountered in HDFS log paths."
    result = validate_runbook_entry(test_log)
    print(f"Status: {result['status']} | Node: {result.get('cluster_node')} | Severity: {result.get('severity')}")