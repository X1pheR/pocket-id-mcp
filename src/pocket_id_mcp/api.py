from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

from .config import Settings


class PocketIdError(RuntimeError):
    pass


class PocketIdClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        authenticated: bool = True,
    ) -> Any:
        if not path.startswith("/"):
            raise ValueError("Pocket ID API path must be absolute")
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "User-Agent": "pocket-id-mcp/0.1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if authenticated:
            headers["X-API-KEY"] = self.settings.read_api_key()
        request = urllib.request.Request(
            self.settings.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.settings.request_timeout_seconds
            ) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise PocketIdError("Pocket ID response exceeded the 2 MiB safety limit")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            raw = error.read(4096)
            message = self._safe_error_message(raw)
            raise PocketIdError(
                f"Pocket ID API returned HTTP {error.code}" + (f": {message}" if message else "")
            ) from None
        except urllib.error.URLError as error:
            reason = str(error.reason)[:256]
            raise PocketIdError(f"Pocket ID API request failed: {reason}") from None
        except TimeoutError:
            raise PocketIdError("Pocket ID API request timed out") from None
        except json.JSONDecodeError:
            raise PocketIdError("Pocket ID API returned invalid JSON") from None

    @staticmethod
    def _safe_error_message(raw: bytes) -> str:
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""
        if not isinstance(value, dict):
            return ""
        for key in ("message", "error", "detail", "title"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return " ".join(candidate.split())[:512]
        return ""

    def list_paginated(self, path: str, *, search: str | None = None) -> list[dict[str, Any]]:
        page = 1
        result: list[dict[str, Any]] = []
        while True:
            query: dict[str, str | int] = {
                "pagination[page]": page,
                "pagination[limit]": 100,
            }
            if search:
                query["search"] = search
            separator = "&" if "?" in path else "?"
            response = self.request("GET", path + separator + urllib.parse.urlencode(query))
            if not isinstance(response, dict) or not isinstance(response.get("data"), list):
                raise PocketIdError("Pocket ID list response has an unexpected shape")
            for item in response["data"]:
                if isinstance(item, dict):
                    result.append(item)
            pagination = response.get("pagination")
            if not isinstance(pagination, dict):
                break
            total_pages = pagination.get("totalPages", 1)
            if not isinstance(total_pages, int) or page >= total_pages:
                break
            page += 1
            if page > 100:
                raise PocketIdError("Pocket ID pagination exceeded 100 pages")
        return result
