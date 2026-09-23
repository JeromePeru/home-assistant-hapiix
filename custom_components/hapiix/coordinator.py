"""Data coordinator for the Hapiix integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    HapiixApiError,
    HapiixAuthenticationError,
    HapiixClient,
    HapiixConnectionError,
)
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HapiixData:
    """Data retrieved from Hapiix."""

    doors: tuple[dict[str, Any], ...]
    members: tuple[dict[str, Any], ...]
    messages: tuple[dict[str, Any], ...]


class HapiixCoordinator(DataUpdateCoordinator[HapiixData]):
    """Coordinate Hapiix cloud polling for all platforms."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: HapiixClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self.client = client

    async def _async_update_data(self) -> HapiixData:
        try:
            doors, members, messages = await asyncio.gather(
                self.client.get_all_doors(),
                self.client.get_all_members(),
                self.client.get_all_messages(),
            )
        except HapiixAuthenticationError as err:
            raise ConfigEntryAuthFailed("Hapiix authentication expired") from err
        except (HapiixConnectionError, HapiixApiError) as err:
            raise UpdateFailed(f"Error communicating with Hapiix: {err}") from err
        return HapiixData(tuple(doors), tuple(members), tuple(messages))

