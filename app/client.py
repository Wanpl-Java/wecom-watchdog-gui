"""HTTP client for wecom-group-watchdog."""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class WatchdogClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8092", timeout: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def healthz(self) -> Dict[str, Any]:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"{self.base_url}/healthz")
            r.raise_for_status()
            return r.json()

    def get_interval(self) -> Dict[str, Any]:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"{self.base_url}/admin/scan-interval")
            r.raise_for_status()
            return r.json()

    def set_interval(self, minutes: int) -> Dict[str, Any]:
        with httpx.Client(timeout=15.0) as c:
            r = c.post(
                f"{self.base_url}/admin/scan-interval",
                params={"minutes": minutes},
            )
            r.raise_for_status()
            return r.json()

    def force_scan(self) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(f"{self.base_url}/admin/scan", params={"force": "true"})
            r.raise_for_status()
            return r.json()

    def suggest(
        self,
        question: str,
        group_name: str = "【JS】GUI模拟群",
        waiting_minutes: float = 6.0,
        product: str = "js",
    ) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(
                f"{self.base_url}/admin/suggest",
                json={
                    "question": question,
                    "group_name": group_name,
                    "waiting_minutes": waiting_minutes,
                    "product": product,
                },
            )
            r.raise_for_status()
            return r.json()

    def rooms(self) -> Dict[str, Any]:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"{self.base_url}/admin/rooms")
            r.raise_for_status()
            return r.json()
