import importlib.util
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "monitoring" / "system_monitor.py"
SPEC = importlib.util.spec_from_file_location("system_monitor", MODULE_PATH)
system_monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(system_monitor)


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class SystemMonitorTests(unittest.TestCase):
    @patch.object(system_monitor, "urlopen", return_value=FakeResponse(200))
    def test_collects_system_metrics_and_healthy_status(self, urlopen):
        fake_psutil = type(
            "FakePsutil",
            (),
            {
                "cpu_percent": staticmethod(lambda interval: 12.5),
                "virtual_memory": staticmethod(lambda: type("Memory", (), {"percent": 64.0})()),
                "disk_usage": staticmethod(lambda path: type("Disk", (), {"percent": 33.0})()),
            },
        )
        with patch.dict(sys.modules, {"psutil": fake_psutil}):
            metrics = system_monitor.collect_metrics("http://127.0.0.1/")

        self.assertEqual(metrics["system_cpu_usage_percent"], 12.5)
        self.assertEqual(metrics["system_memory_usage_percent"], 64.0)
        self.assertEqual(metrics["system_disk_usage_percent"], 33.0)
        self.assertEqual(metrics["booking_nginx_http_healthy"], 1)
        self.assertEqual(metrics["booking_nginx_http_status_code"], 200)
        urlopen.assert_called_once_with("http://127.0.0.1/", timeout=3)

    @patch.object(
        system_monitor,
        "urlopen",
        side_effect=HTTPError("http://127.0.0.1/", 503, "Unavailable", {}, None),
    )
    def test_non_200_status_is_unhealthy(self, _urlopen):
        fake_psutil = type(
            "FakePsutil",
            (),
            {
                "cpu_percent": staticmethod(lambda interval: 0.0),
                "virtual_memory": staticmethod(lambda: type("Memory", (), {"percent": 0.0})()),
                "disk_usage": staticmethod(lambda path: type("Disk", (), {"percent": 0.0})()),
            },
        )
        with patch.dict(sys.modules, {"psutil": fake_psutil}):
            metrics = system_monitor.collect_metrics("http://127.0.0.1/")

        self.assertEqual(metrics["booking_nginx_http_healthy"], 0)
        self.assertEqual(metrics["booking_nginx_http_status_code"], 503)

    def test_metrics_endpoint_returns_prometheus_text(self):
        original_metrics = system_monitor.METRICS.copy()
        system_monitor.METRICS.update(
            {
                "system_cpu_usage_percent": 12.5,
                "booking_nginx_http_healthy": 1,
            }
        )
        server = system_monitor.ThreadingHTTPServer(("127.0.0.1", 0), system_monitor.MetricsHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            from urllib.request import urlopen

            with urlopen(f"http://127.0.0.1:{server.server_port}/metrics", timeout=3) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("system_cpu_usage_percent 12.5", body)
                self.assertIn("booking_nginx_http_healthy 1", body)
        finally:
            thread.join(timeout=3)
            server.server_close()
            system_monitor.METRICS.clear()
            system_monitor.METRICS.update(original_metrics)


if __name__ == "__main__":
    unittest.main()
