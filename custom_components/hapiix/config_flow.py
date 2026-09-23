"""Config flow for Hapiix."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_EMAIL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    HapiixApiError,
    HapiixAuthenticationError,
    HapiixClient,
    HapiixConnectionError,
)
from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DOMAIN

CONF_CODE = "code"


class HapiixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Hapiix config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str | None = None
        self._client: HapiixClient | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Request the account e-mail and send its one-time code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip().lower()
            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()
            self._client = HapiixClient(async_get_clientsession(self.hass))
            try:
                await self._client.request_login_code(self._email)
            except HapiixConnectionError:
                errors["base"] = "cannot_connect"
            except HapiixApiError:
                errors["base"] = "request_failed"
            else:
                return await self.async_step_code()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_EMAIL): str}),
            errors=errors,
        )

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Exchange the code received by e-mail for API tokens."""
        if self._client is None or self._email is None:
            return self.async_abort(reason="flow_expired")
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                access_token, refresh_token = await self._client.authenticate(
                    user_input[CONF_CODE]
                )
                await self._client.get_all_doors()
            except HapiixAuthenticationError:
                errors["base"] = "invalid_auth"
            except HapiixConnectionError:
                errors["base"] = "cannot_connect"
            except HapiixApiError:
                errors["base"] = "request_failed"
            else:
                return self.async_create_entry(
                    title=self._email,
                    data={
                        CONF_EMAIL: self._email,
                        CONF_ACCESS_TOKEN: access_token,
                        CONF_REFRESH_TOKEN: refresh_token,
                    },
                )
        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema({vol.Required(CONF_CODE): str}),
            errors=errors,
            description_placeholders={"email": self._email},
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Begin reauthentication for an existing account."""
        self._email = entry_data[CONF_EMAIL]
        self._client = HapiixClient(async_get_clientsession(self.hass))
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Send a new code after user confirmation."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._client.request_login_code(self._email)  # type: ignore[arg-type]
            except HapiixConnectionError:
                errors["base"] = "cannot_connect"
            except HapiixApiError:
                errors["base"] = "request_failed"
            else:
                return await self.async_step_reauth_code()
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"email": self._email or ""},
        )

    async def async_step_reauth_code(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Complete reauthentication using the received code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                access_token, refresh_token = await self._client.authenticate(  # type: ignore[union-attr]
                    user_input[CONF_CODE]
                )
            except HapiixAuthenticationError:
                errors["base"] = "invalid_auth"
            except HapiixConnectionError:
                errors["base"] = "cannot_connect"
            except HapiixApiError:
                errors["base"] = "request_failed"
            else:
                entry = self._get_reauth_entry()
                await self.async_set_unique_id(self._email)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_ACCESS_TOKEN: access_token,
                        CONF_REFRESH_TOKEN: refresh_token,
                    },
                )
        return self.async_show_form(
            step_id="reauth_code",
            data_schema=vol.Schema({vol.Required(CONF_CODE): str}),
            errors=errors,
            description_placeholders={"email": self._email or ""},
        )
