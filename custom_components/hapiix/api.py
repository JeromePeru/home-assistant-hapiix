"""Asynchronous client for the Hapiix occupant API."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import API_BASE_URL

TokenCallback = Callable[[str, str | None], Awaitable[None] | None]


class HapiixError(Exception):
    """Base exception for Hapiix failures."""


class HapiixConnectionError(HapiixError):
    """The Hapiix cloud could not be reached."""


class HapiixAuthenticationError(HapiixError):
    """Hapiix rejected the authentication credentials."""


class HapiixApiError(HapiixError):
    """The Hapiix cloud returned an unexpected response."""

    def __init__(self, status: int, message: str = "") -> None:
        super().__init__(f"Hapiix API returned HTTP {status}")
        self.status = status
        self.message = message


class HapiixClient:
    """Small, fully asynchronous Hapiix API client."""

    def __init__(
        self,
        session: ClientSession,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_callback: TokenCallback | None = None,
    ) -> None:
        self._session = session
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._token_callback = token_callback
        self._refresh_lock = asyncio.Lock()

    async def request_login_code(self, email: str) -> None:
        """Ask Hapiix to send a one-time login code."""
        await self._request("POST", "authenticate/request", json={"email": email})

    async def authenticate(self, code: str) -> tuple[str, str | None]:
        """Exchange the one-time code for access and refresh tokens."""
        payload = await self._request(
            "POST", "authenticate", json={"token": code.strip()}
        )
        token = payload.get("token") if isinstance(payload, dict) else None
        if not token:
            raise HapiixAuthenticationError("The authentication response had no token")
        await self._set_tokens(token, payload.get("refreshToken"))
        return self.access_token or token, self.refresh_token

    async def get_all_doors(self) -> list[dict[str, Any]]:
        """Return every door visible to the account."""
        return await self._get_all_pages("doors/all")

    async def get_all_members(self) -> list[dict[str, Any]]:
        """Return every member visible to the account."""
        return await self._get_all_pages("members")

    async def get_all_messages(self) -> list[dict[str, Any]]:
        """Return every received voicemail/video message."""
        return await self._get_all_pages("voicemails")

    async def open_door(self, door_id: str) -> None:
        """Open a door using the same mode as the official application."""
        await self._request(
            "POST", f"doors/{quote(door_id, safe='')}/open?open_type=app", auth=True
        )

    async def _get_all_pages(
        self, endpoint: str, page_size: int = 50
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        start = 0
        for _page in range(100):
            end = start + page_size - 1
            payload = await self._request(
                "GET",
                f"{endpoint}?start_index={start}&end_index={end}",
                auth=True,
            )
            if not isinstance(payload, dict):
                raise HapiixApiError(200, "Expected a JSON object")
            page_items = payload.get("items", [])
            if not isinstance(page_items, list):
                raise HapiixApiError(200, "Expected an items array")
            items.extend(item for item in page_items if isinstance(item, dict))
            total = int(payload.get("total", len(items)))
            if not page_items or len(items) >= total:
                return items
            returned_end = int(payload.get("endIndex", end))
            next_start = max(returned_end + 1, start + len(page_items))
            if next_start <= start:
                raise HapiixApiError(200, "Pagination did not advance")
            start = next_start
        raise HapiixApiError(200, "Pagination exceeded 100 pages")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        auth: bool = False,
        retry: bool = True,
    ) -> Any:
        headers: dict[str, str] = {}
        token_used = self.access_token
        if auth:
            if not token_used:
                raise HapiixAuthenticationError("No Hapiix access token is available")
            # This intentionally matches the Android application. "Bearer" is the
            # header name; it is not an Authorization header with a Bearer scheme.
            headers["Bearer"] = token_used

        try:
            response = await self._session.request(
                method,
                API_BASE_URL + path,
                json=json,
                headers=headers,
                allow_redirects=False,
                timeout=ClientTimeout(total=60, connect=30, sock_read=30),
            )
        except (ClientError, TimeoutError) as err:
            raise HapiixConnectionError(str(err)) from err

        if response.status == 401 and auth and retry and self.refresh_token:
            response.release()
            async with self._refresh_lock:
                if self.access_token == token_used:
                    await self._refresh_access_token()
            return await self._request(method, path, json=json, auth=True, retry=False)

        return await self._read_response(response)

    async def _refresh_access_token(self) -> None:
        refresh_token = self.refresh_token
        if not refresh_token:
            raise HapiixAuthenticationError("No Hapiix refresh token is available")
        headers = {"Bearer": self.access_token} if self.access_token else {}
        try:
            response = await self._session.post(
                API_BASE_URL + "authenticate/refresh",
                json={"refreshToken": refresh_token},
                headers=headers,
                allow_redirects=False,
                timeout=ClientTimeout(total=60, connect=30, sock_read=30),
            )
        except (ClientError, TimeoutError) as err:
            raise HapiixConnectionError(str(err)) from err
        payload = await self._read_response(response)
        token = payload.get("token") if isinstance(payload, dict) else None
        if not token:
            raise HapiixAuthenticationError("Token refresh returned no access token")
        await self._set_tokens(token, payload.get("refreshToken") or refresh_token)

    async def _set_tokens(self, access_token: str, refresh_token: str | None) -> None:
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if self._token_callback is not None:
            result = self._token_callback(self.access_token, self.refresh_token)
            if result is not None:
                await result

    @staticmethod
    async def _read_response(response: ClientResponse) -> Any:
        async with response:
            if response.status == 401:
                raise HapiixAuthenticationError("Hapiix rejected the credentials")
            if response.status < 200 or response.status >= 300:
                body = (await response.text())[:500]
                raise HapiixApiError(response.status, body)
            if response.status == 204 or response.content_length == 0:
                return None
            try:
                return await response.json(content_type=None)
            except (ValueError, ClientError) as err:
                raise HapiixApiError(response.status, "Invalid JSON response") from err

