#!/usr/bin/env python3
"""Minimal client for the Apify REST API.


Design rules this file follows:

* The API token is read from the ``APIFY_API_TOKEN`` environment variable and
  from nowhere else. There is no flag, no config key and no file fallback, so
  the token cannot end up in shell history, a process list or a committed file.
* The token goes in an ``Authorization`` header, never in a query string, so it
  does not land in proxy or server logs.
* The token is never printed. Response bodies are scrubbed before they reach an
  exception message, because an error body that echoes the request would
  otherwise leak it.
* Nothing in here asks for confirmation. Gating the runs that cost money is the
  caller's job; see ``cli.py``.

Written against the Apify REST API as documented at https://docs.apify.com/api/v2
on 2026-09-29. The endpoint shapes were taken from that documentation and have
not been re-run against a live account since.

Why raw REST rather than the ``apify-client`` package: one fewer dependency, no
model validation that can break when Apify adds a field, and the request being
made is visible in this file.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, List, Optional

import requests

TOKEN_ENV = "APIFY_API_TOKEN"
DEFAULT_BASE_URL = "https://api.apify.com/v2"

# Apify pages dataset items; 1000 per request is the documented maximum.
DATASET_PAGE_SIZE = 1000

# Terminal run statuses, per the Apify run lifecycle documentation.
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


class ApifyError(RuntimeError):
    """Any failure talking to Apify."""


class MissingCredential(ApifyError):
    """The API token environment variable is absent or empty."""


class ActorRunFailed(ApifyError):
    """An actor run finished in a status other than SUCCEEDED."""


def get_api_token() -> str:
    """Return the Apify API token from the environment, or fail loudly.

    The error names the variable but never its value.
    """
    token = (os.environ.get(TOKEN_ENV) or "").strip()
    if not token:
        raise MissingCredential(
            f"{TOKEN_ENV} is not set. Create a token in the Apify console "
            f"(Settings, Integrations, API tokens), then export it in your "
            f"shell or put it in a gitignored .env / .envrc that your shell "
            f"loads, and re-run. Do not pass the token as a command-line flag "
            f"and do not paste it into a chat."
        )
    return token


def _scrub(text: str, secret: str) -> str:
    """Remove the API token from text that is about to be shown to a human."""
    if not text:
        return ""
    cleaned = text.replace(secret, "[REDACTED]")
    # Catch the header and query-string forms, in case an error body echoes
    # the request back at us.
    cleaned = cleaned.replace(f"Bearer {secret}", "[REDACTED]")
    return cleaned.replace(f"token={secret}", "token=[REDACTED]")


class ApifyClient:
    """Thin wrapper over the Apify endpoints this CLI needs."""

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self._token = token or get_api_token()
        self.base_url = (
            base_url or os.environ.get("APIFY_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    # -- transport ---------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self._session.request(
                method,
                url,
                headers=self._headers(),
                params=params or None,
                json=json_body,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ApifyError(
                f"{method} {path} failed: {_scrub(str(exc), self._token)}"
            ) from None

        if resp.status_code == 429:
            raise ApifyError(
                f"{method} {path} -> HTTP 429: Apify rate-limited this request. "
                f"Wait and retry; this tool does not retry for you."
            )
        if resp.status_code >= 400:
            body = _scrub(resp.text[:2000], self._token)
            raise ApifyError(f"{method} {path} -> HTTP {resp.status_code}: {body}")

        if resp.status_code == 204 or not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            raise ApifyError(f"{method} {path} returned a non-JSON body") from None

    @staticmethod
    def _data(payload: Any) -> Any:
        """Apify wraps most responses in a ``data`` envelope; dataset items
        are returned as a bare array."""
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    # -- actor runs --------------------------------------------------------

    def start_run(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Start an actor run and return the run object immediately.

        This costs money on the caller's Apify account. Everything that calls
        it must have been through the confirmation gate in cli.py first.
        """
        payload = self._request(
            "POST", f"acts/{actor_id}/runs", json_body=run_input
        )
        run = self._data(payload)
        if not isinstance(run, dict) or not run.get("id"):
            raise ApifyError(f"actor {actor_id} did not return a run id")
        return run

    def get_run(self, run_id: str) -> Dict[str, Any]:
        run = self._data(self._request("GET", f"actor-runs/{run_id}"))
        if not isinstance(run, dict):
            raise ApifyError(f"run {run_id} returned an unexpected body")
        return run

    def wait_for_run(
        self,
        run_id: str,
        poll_interval: float = 5.0,
        timeout_s: int = 900,
    ) -> Dict[str, Any]:
        """Poll until the run reaches a terminal status.

        A run that is still going when this gives up is NOT aborted. It keeps
        running and keeps costing credits; abort it in the Apify console.
        """
        deadline = time.time() + timeout_s
        while True:
            run = self.get_run(run_id)
            status = run.get("status")
            if status in TERMINAL_STATUSES:
                if status != "SUCCEEDED":
                    raise ActorRunFailed(
                        f"actor run {run_id} ended with status {status}. "
                        f"Its log is in the Apify console."
                    )
                return run
            if time.time() >= deadline:
                raise ApifyError(
                    f"actor run {run_id} did not finish within {timeout_s}s. "
                    f"It is still running and still consuming credits; check "
                    f"or abort it in the Apify console."
                )
            time.sleep(poll_interval)

    def run_actor(
        self,
        actor_id: str,
        run_input: Dict[str, Any],
        poll_interval: float = 5.0,
        timeout_s: int = 900,
    ) -> Dict[str, Any]:
        """Start an actor, wait for it, and return the finished run object."""
        started = self.start_run(actor_id, run_input)
        return self.wait_for_run(
            started["id"], poll_interval=poll_interval, timeout_s=timeout_s
        )

    # -- datasets ----------------------------------------------------------

    def iter_dataset_items(self, dataset_id: str) -> Iterator[Dict[str, Any]]:
        offset = 0
        while True:
            page = self._request(
                "GET",
                f"datasets/{dataset_id}/items",
                params={
                    "offset": offset,
                    "limit": DATASET_PAGE_SIZE,
                    "clean": "false",
                    "format": "json",
                },
            )
            items = page if isinstance(page, list) else []
            for item in items:
                if isinstance(item, dict):
                    yield item
            if len(items) < DATASET_PAGE_SIZE:
                return
            offset += len(items)

    def dataset_items(self, dataset_id: str) -> List[Dict[str, Any]]:
        return list(self.iter_dataset_items(dataset_id))
