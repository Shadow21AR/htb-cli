"""
HTTP client for HTB API.

Handles authentication, error handling, retries, and response parsing.
"""

import atexit
import html as html_mod
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
            # Prefer the server-provided message when present; some endpoints
            # return 403 with a specific rejection reason (e.g. "Incorrect flag")
            # that is not an authentication problem.
            message = (
                data.get("message")
                or data.get("error")
                or data.get("msg")
                or f"HTTP {response.status_code}"
            )
            if response.status_code in (401, 403) and message.startswith("HTTP"):
                message = "Authentication failed. Run `htb auth set` or set HTB_TOKEN."
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

                # Retry on 5xx errors, but try to extract a message from the body
                if response.status_code >= 500:
                    try:
                        body = response.json()
                        msg = body.get("message") or body.get("error") or f"Server error: {response.status_code}"
                    except Exception:
                        msg = f"Server error: {response.status_code}"
                    raise httpx.HTTPStatusError(
                        msg,
                        request=response.request,
                        response=response,
                    )

                return response

            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    if not isinstance(e, httpx.HTTPStatusError):
                        time.sleep(2 ** attempt)
                    continue
                msg = str(e)
                status_code = None
                if isinstance(e, httpx.HTTPStatusError):
                    msg = e.args[0] if e.args else f"Server error: {e.response.status_code}"
                    status_code = e.response.status_code
                raise HTBError(msg, status_code=status_code) from e

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

    def _follow_redirect(self, response: httpx.Response) -> httpx.Response:
        """Follow HTTP redirect and decode HTML entities in the Location URL."""
        location = response.headers.get("Location") or response.headers.get("location")
        if not location:
            return response
        location = html_mod.unescape(location)
        # CDN URLs reject HTB auth headers; use an anonymous request
        follow_resp = httpx.get(location, follow_redirects=True)
        if follow_resp.status_code >= 400:
            msg = self._extract_error(follow_resp)
            raise HTBError(msg or f"Download redirect failed: HTTP {follow_resp.status_code}", follow_resp.status_code)
        return follow_resp

    @staticmethod
    def _extract_error(response: httpx.Response) -> str | None:
        """Extract error message from a response body."""
        try:
            body = response.json()
            return body.get("message") or body.get("error") or body.get("msg")
        except Exception:
            return None

    def download(self, path: str) -> str:
        """Download raw content (e.g., VPN files)."""
        url = self.config.url(path)
        response = self._request_with_retry("GET", url)
        if response.is_redirect:
            response = self._follow_redirect(response)
        if response.status_code >= 400:
            msg = self._extract_error(response)
            raise HTBError(msg or f"Download failed: HTTP {response.status_code}", response.status_code)
        return response.text

    def download_bytes(self, path: str) -> bytes:
        """Download binary content."""
        url = self.config.url(path)
        response = self._request_with_retry("GET", url)
        if response.is_redirect:
            response = self._follow_redirect(response)
        if response.status_code >= 400:
            msg = self._extract_error(response)
            raise HTBError(msg or f"Download failed: HTTP {response.status_code}", response.status_code)
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
        try:
            _client = HTBClient()
            atexit.register(_client.close)
        except FileNotFoundError as e:
            raise HTBError(str(e)) from e
    return _client


def api_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """Convenience function for GET requests."""
    return get_client().get(path, params)


def api_post(path: str, data: dict | None = None) -> dict[str, Any]:
    """Convenience function for POST requests."""
    return get_client().post(path, data)


def api_get_v5(path: str, params: dict | None = None) -> dict[str, Any]:
    """GET request to a v5 endpoint (prepends /v5 to path)."""
    return get_client().get(f"/v5{path}", params)


def api_get_experience(path: str, params: dict | None = None) -> dict[str, Any]:
    """GET request to the experience/v1 API (prepends /api/experience/v1)."""
    return get_client().get(f"/api/experience/v1{path}", params)


def api_post_v5(path: str, data: dict | None = None) -> dict[str, Any]:
    """POST request to a v5 endpoint (prepends /v5 to path)."""
    return get_client().post(f"/v5{path}", data)


def api_download(path: str) -> str:
    """Convenience function for text downloads."""
    return get_client().download(path)


def api_download_bytes(path: str) -> bytes:
    """Convenience function for binary downloads."""
    return get_client().download_bytes(path)


# ─────────────────────────────────────────────────────────────────────────────
# Health / Infra status (status.hackthebox.com - separate from HTB API)
# ─────────────────────────────────────────────────────────────────────────────


import re as _re


def fetch_infra_status() -> list[dict]:
    """Scrape https://status.hackthebox.com/ for component statuses and active incidents.

    Returns a list of dicts with keys:
      group  — component group name (e.g. "Platforms", "Backend Services")
      name   — component name (e.g. "HTB Labs", "VPN Services")
      status — one of "operational", "partial_outage", "major_outage",
               "degraded_performance"
    """
    resp = httpx.get("https://status.hackthebox.com/", timeout=15)
    resp.raise_for_status()
    html = resp.text

    results: list[dict] = []
    incidents: list[dict] = []

    # Parse active incidents
    for m in _re.finditer(
        r'class="htb-text-primary text-xl pl-5">\s*Incident:\s*(.+?)</p>',
        html,
        _re.DOTALL,
    ):
        incidents.append({"title": m.group(1).strip(), "type": "incident"})

    # Parse group sections — walk through groups sequentially
    # Each group: <div wire:snapshot="..."> ... <p class="ml-1 htb-text-secondary">GroupName</p> ...
    # Components inside have <p class="pl-6">Name</p> + <p class="htb-status-text-xxx">Status</p>
    group_pattern = _re.compile(
        r'<p class="ml-1 htb-text-secondary">(.+?)</p>\s*'
        r'(.*?)(?=<p class="ml-1 htb-text-secondary">|$)',
        _re.DOTALL,
    )
    comp_pattern = _re.compile(
        r'<p class="pl-6">(.+?)</p>.*?'
        r'class="htb-status-text-(\w+)">(\w+(?:\s+\w+)?)</p>',
        _re.DOTALL,
    )

    for gm in group_pattern.finditer(html):
        group_name = gm.group(1).strip()
        group_html = gm.group(2)
        for cm in comp_pattern.finditer(group_html):
            results.append({
                "group": group_name,
                "name": html_mod.unescape(cm.group(1).strip()),
                "status": cm.group(2),
            })

    if incidents:
        for inc in incidents:
            results.insert(0, inc | {"type": "incident"})

    return results
