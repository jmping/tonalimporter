"""Local API client for Tonal Companion."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class TonalApiError(Exception):
    """Base Tonal Companion API error."""


class TonalAuthRequired(TonalApiError):
    """Tonal authentication is required."""


class TonalClient:
    def __init__(self, host: str) -> None:
        self.host = host.rstrip("/")

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        method = "GET"
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
            method = "POST"
        request = Request(f"{self.host}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 - configured local endpoint
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            try:
                detail = json.loads(err.read().decode("utf-8"))
                message = detail.get("error", str(err))
            except Exception:  # noqa: BLE001
                message = str(err)
            raise TonalApiError(message) from err
        except (URLError, TimeoutError, OSError) as err:
            raise TonalApiError(str(err)) from err

    def health(self) -> dict[str, Any]:
        return self._request("/health")

    def summary(self) -> dict[str, Any]:
        data = self._request("/summary")
        if data.get("auth_required"):
            raise TonalAuthRequired("Tonal authentication required")
        return data

    def authenticate(self, email: str, password: str) -> None:
        result = self._request("/auth", {"email": email, "password": password})
        if not result.get("ok"):
            raise TonalApiError(result.get("error", "Authentication failed"))
