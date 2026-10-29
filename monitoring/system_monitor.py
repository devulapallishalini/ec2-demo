#!/usr/bin/env python3
"""Expose local system and booking-site health metrics for Prometheus."""

import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

LOG = logging.getLogger("booking-system-monitor")
METRICS_LOCK = threading.Lock()
METRICS = {
    "system_cpu_usage_percent": 0.0,
    "system_memory_usage_percent": 0.0,
    "system_disk_usage_percent": 0.0,
    "booking_nginx_http_healthy": 0,
    "booking_nginx_http_status_code": 0,
}


def collect_metrics(health_url):
    import psutil

    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage("/").percent

    try:
        with urlopen(health_url, timeout=3) as response:
            status_code = response.status
    except HTTPError as error:
        LOG.warning("Booking health check returned HTTP %s", error.code)
        status_code = error.code
    except (OSError, URLError, TimeoutError) as error:
        LOG.warning("Booking health check failed for %s: %s", health_url, error)
        status_code = 0

    return {
        "system_cpu_usage_percent": cpu_percent,
        "system_memory_usage_percent": memory_percent,
        "system_disk_usage_percent": disk_percent,
        "booking_nginx_http_healthy": int(status_code == 200),
        "booking_nginx_http_status_code": status_code,
    }


def update_metrics(health_url, interval):
    while True:
        try:
            values = collect_metrics(health_url)
            with METRICS_LOCK:
                METRICS.update(values)
        except Exception:
            LOG.exception("Could not collect system metrics")
        time.sleep(interval)


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return

        with METRICS_LOCK:
            snapshot = dict(METRICS)

        body = "".join(f"{name} {value}\n" for name, value in snapshot.items())
        encoded_body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def log_message(self, format_string, *args):
        LOG.info("%s - %s", self.address_string(), format_string % args)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    health_url = os.environ.get("BOOKING_HEALTH_URL", "http://127.0.0.1/")
    interval = int(os.environ.get("METRICS_INTERVAL_SECONDS", "15"))
    if interval < 1:
        raise ValueError("METRICS_INTERVAL_SECONDS must be at least 1")

    collector = threading.Thread(
        target=update_metrics,
        args=(health_url, interval),
        daemon=True,
    )
    collector.start()

    server = ThreadingHTTPServer(("127.0.0.1", 9100), MetricsHandler)
    LOG.info("Serving Prometheus metrics on http://127.0.0.1:9100/metrics")
    server.serve_forever()


if __name__ == "__main__":
    main()
