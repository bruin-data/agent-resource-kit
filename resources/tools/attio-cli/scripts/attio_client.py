"""Minimal client for the Attio API v2.


Design rules this file follows:

* The API key is read from the ``ATTIO_API_KEY`` environment variable and from
  nowhere else. There is no flag, no config key and no file fallback, so the key
  cannot end up in shell history, a process list or a committed file.
* The key is never printed. Response bodies are scrubbed before they are put in
  an exception message, because a request echo in an error body would otherwise
  leak the Authorization header.
* Nothing in here asks for confirmation. Gating writes is the caller's job; see
  ``cli.py``.

Written against Attio API v2 as documented at https://docs.attio.com/ .
Endpoint shapes were taken from that documentation, not from a live call.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterator, List, Optional

import requests

API_KEY_ENV = "ATTIO_API_KEY"
DEFAULT_BASE_URL = "https://api.attio.com/v2"

# Attio rejects oversized pages; 500 is a conservative ceiling for one request.
MAX_PAGE_SIZE = 500


class AttioError(RuntimeError):
    """Any failure talking to Attio."""


class MissingCredential(AttioError):
    """The API key environment variable is absent or empty."""


def get_api_key() -> str:
    """Return the Attio API key from the environment, or fail loudly.

    The error names the variable but never its value.
    """
    key = (os.environ.get(API_KEY_ENV) or "").strip()
    if not key:
        raise MissingCredential(
            f"{API_KEY_ENV} is not set. Export it in your shell, or put it in a "
            f"gitignored .env / .envrc that your shell loads, then re-run. "
            f"Do not pass the key as a command-line flag and do not paste it "
            f"into a chat."
        )
    return key


def _scrub(text: str, secret: str) -> str:
    """Remove the API key from text that is about to be shown to a human."""
    if not text:
        return ""
    cleaned = text.replace(secret, "[REDACTED]")
    # Also catch the header form, in case an error body echoes the request.
    return cleaned.replace(f"Bearer {secret}", "[REDACTED]")


class AttioClient:
    """Thin wrapper over the Attio v2 REST endpoints used by the CLI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._api_key = api_key or get_api_key()
        self.base_url = (base_url or os.environ.get("ATTIO_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    # -- transport ---------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
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
            raise AttioError(f"{method} {path} failed: {_scrub(str(exc), self._api_key)}") from None

        if resp.status_code >= 400:
            body = _scrub(resp.text[:2000], self._api_key)
            raise AttioError(f"{method} {path} -> HTTP {resp.status_code}: {body}")

        if resp.status_code == 204 or not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            raise AttioError(f"{method} {path} returned a non-JSON body") from None

    @staticmethod
    def _data(payload: Any, default: Any = None) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload if payload is not None else default

    # -- schema discovery --------------------------------------------------

    def list_objects(self) -> List[Dict[str, Any]]:
        """Every object in the workspace, standard and custom.

        Use this instead of assuming which objects exist: workspaces rename and
        add objects freely.
        """
        return self._data(self._request("GET", "objects"), []) or []

    def list_attributes(self, object_slug: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        payload = self._request(
            "GET", f"objects/{object_slug}/attributes", params={"limit": limit, "offset": offset}
        )
        return self._data(payload, []) or []

    def list_lists(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        payload = self._request("GET", "lists", params={"limit": limit, "offset": offset})
        return self._data(payload, []) or []

    def list_list_attributes(self, list_slug: str) -> List[Dict[str, Any]]:
        return self._data(self._request("GET", f"lists/{list_slug}/attributes"), []) or []

    # -- records (read) ----------------------------------------------------

    def query_records(
        self,
        object_slug: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        body: Dict[str, Any] = {"limit": min(limit, MAX_PAGE_SIZE), "offset": offset}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        payload = self._request("POST", f"objects/{object_slug}/records/query", json_body=body)
        return self._data(payload, []) or []

    def iter_records(
        self,
        object_slug: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
        max_records: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Page through a record query.

        Attio pages with limit/offset and gives no next-page cursor, so a short
        page is the only end-of-results signal.
        """
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))
        offset = 0
        yielded = 0
        while True:
            want = page_size
            if max_records is not None:
                want = min(page_size, max_records - yielded)
                if want <= 0:
                    return
            page = self.query_records(object_slug, filter, sorts, limit=want, offset=offset)
            for record in page:
                yield record
                yielded += 1
            if len(page) < want:
                return
            offset += len(page)

    def get_record(self, object_slug: str, record_id: str) -> Dict[str, Any]:
        return self._data(self._request("GET", f"objects/{object_slug}/records/{record_id}"), {})

    def search_records(
        self,
        object_slug: str,
        query: str,
        search_attribute: str = "name",
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Substring search on one attribute.

        Attio has no general full-text record search in v2, so "search" here is
        a ``$contains`` filter. Which attribute makes sense is per workspace and
        per object, hence ``search_attribute``.
        """
        return self.query_records(
            object_slug,
            filter={search_attribute: {"$contains": query}},
            limit=limit,
            offset=offset,
        )

    # -- list entries (read) -----------------------------------------------

    def query_entries(
        self,
        list_slug: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        body: Dict[str, Any] = {"limit": min(limit, MAX_PAGE_SIZE), "offset": offset}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        payload = self._request("POST", f"lists/{list_slug}/entries/query", json_body=body)
        return self._data(payload, []) or []

    # -- writes ------------------------------------------------------------
    # None of these confirm anything. cli.py gates them behind --yes.

    def create_record(self, object_slug: str, values: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._request(
            "POST", f"objects/{object_slug}/records", json_body={"data": {"values": values}}
        )
        return self._data(payload, {})

    def update_record(self, object_slug: str, record_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._request(
            "PATCH",
            f"objects/{object_slug}/records/{record_id}",
            json_body={"data": {"values": values}},
        )
        return self._data(payload, {})

    def assert_record(
        self, object_slug: str, matching_attribute: str, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update a record, matched on a unique attribute ("upsert").

        The documented call passes ``matching_attribute`` as a query parameter.
        Older clients passed it inside the body, so if the query-parameter form
        is rejected as a bad request, retry the body form once before giving up.
        """
        try:
            payload = self._request(
                "PUT",
                f"objects/{object_slug}/records",
                params={"matching_attribute": matching_attribute},
                json_body={"data": {"values": values}},
            )
        except AttioError as exc:
            if "HTTP 400" not in str(exc):
                raise
            payload = self._request(
                "PUT",
                f"objects/{object_slug}/records",
                json_body={
                    "data": {"matching_attribute": matching_attribute, "values": values}
                },
            )
        return self._data(payload, {})

    def delete_record(self, object_slug: str, record_id: str) -> None:
        self._request("DELETE", f"objects/{object_slug}/records/{record_id}")

    def update_list_entry(
        self, list_slug: str, entry_id: str, entry_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = self._request(
            "PATCH",
            f"lists/{list_slug}/entries/{entry_id}",
            json_body={"data": {"entry_values": entry_values}},
        )
        return self._data(payload, {})

    def add_to_list(
        self,
        list_slug: str,
        parent_object: str,
        parent_record_id: str,
        entry_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add an existing record to a list.

        ``parent_object`` is the slug of the object the record belongs to; a
        list can be parented to more than one object, so Attio needs both.
        """
        data: Dict[str, Any] = {
            "parent_object": parent_object,
            "parent_record_id": parent_record_id,
        }
        if entry_values:
            data["entry_values"] = entry_values
        return self._data(self._request("POST", f"lists/{list_slug}/entries", json_body={"data": data}), {})

    def delete_list_entry(self, list_slug: str, entry_id: str) -> None:
        self._request("DELETE", f"lists/{list_slug}/entries/{entry_id}")
