#!/usr/bin/env python
import argparse
import json
import time
import urllib.error
import urllib.request


def call(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "aiops-lab-traffic/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, json.dumps({"error": str(exc)})


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate normal and failure traffic for demo-service.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for demo-service.")
    parser.add_argument("--iterations", type=int, default=8, help="Traffic loop count.")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep between iterations.")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    common_paths = [
        "/health",
        "/ready",
        "/api/orders",
        "/api/orders/ord-1001",
    ]

    for index in range(1, args.iterations + 1):
        paths = list(common_paths)

        if index % 2 == 0:
            paths.append("/simulate/latency?min_ms=500&max_ms=1600")
        if index % 3 == 0:
            paths.append("/simulate/error?probability=1.0")
        if index % 4 == 0:
            paths.append("/simulate/memory-pressure?size_mb=8")
        if index % 5 == 0:
            paths.append("/api/orders/missing-order")
        if index % 6 == 0:
            paths.append("/simulate/log-event?event=manual_investigation_marker&level=warning")

        for path in paths:
            status, body = call(f"{base_url}{path}")
            print(f"{status:>3} {path} {body[:140]}")

        time.sleep(args.sleep)

    print("\nTraffic generation complete. Run: make analyze-logs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

