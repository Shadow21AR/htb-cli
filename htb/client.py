"""
HTTP client for HTB API.

Handles authentication, error handling, retries, and response parsing.
"""

import time
from typing import Any

import httpx

from .config import Config, get_config


class HTBError(Exception):
    """Base exception for HTB API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class HTBClient:
    """HTTP client for HTB Labs API with retry support."""

    def __init__(self, config: Config | None = None):
        self.config = config or get_config()
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=self.config.timeout,
        )

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse response and handle errors."""
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}

        if response.status_code >= 400:
            message = (
                data.get("message")
                or data.get("error")
                or data.get("msg")
                or f"HTTP {response.status_code}"
            )
            raise HTBError(message, response.status_code, data)

        return data

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Execute request with exponential backoff retry."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                response = self._client.request(method, url, **kwargs)

                # Retry on 5xx errors
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                return response

            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s...
                    time.sleep(2 ** attempt)
                    continue
                raise

        raise last_error or HTBError("Request failed after retries")

    def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """GET request to API endpoint."""
        url = self.config.url(path)
        response = self._request_with_retry("GET", url, params=params)
        return self._handle_response(response)

    def post(self, path: str, data: dict | None = None) -> dict[str, Any]:
        """POST request to API endpoint."""
        url = self.config.url(path)
        response = self._request_with_retry("POST", url, json=data or {})
        return self._handle_response(response)

    def download(self, path: str) -> str:
        """Download raw content (e.g., VPN files)."""
        url = self.config.url(path)
        response = self._request_with_retry("GET", url)
        if response.status_code >= 400:
            raise HTBError(f"Download failed: HTTP {response.status_code}", response.status_code)
        return response.text

    def download_bytes(self, path: str) -> bytes:
        """Download binary content."""
        url = self.config.url(path)
        response = self._request_with_retry("GET", url)
        if response.status_code >= 400:
            raise HTBError(f"Download failed: HTTP {response.status_code}", response.status_code)
        return response.content

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# Global client instance (lazy loaded)
_client: HTBClient | None = None


def get_client() -> HTBClient:
    """Get or create the global client."""
    global _client
    if _client is None:
        _client = HTBClient()
    return _client


def api_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """Convenience function for GET requests."""
    return get_client().get(path, params)


def api_post(path: str, data: dict | None = None) -> dict[str, Any]:
    """Convenience function for POST requests."""
    return get_client().post(path, data)


def api_download(path: str) -> str:
    """Convenience function for text downloads."""
    return get_client().download(path)


def api_download_bytes(path: str) -> bytes:
    """Convenience function for binary downloads."""
    return get_client().download_bytes(path)
