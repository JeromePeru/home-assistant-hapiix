"""Hapiix integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HapiixClient
from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, PLATFORMS
from .coordinator import HapiixCoordinator


@dataclass
class HapiixRuntimeData:
    """Runtime objects associated with one account."""

    client: HapiixClient
    coordinator: HapiixCoordinator


type HapiixConfigEntry = ConfigEntry[HapiixRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: HapiixConfigEntry) -> bool:
    """Set up Hapiix from a config entry."""

    async def async_save_tokens(
        access_token: str, refresh_token: str | None
    ) -> None:
        new_data = {
            **entry.data,
            CONF_ACCESS_TOKEN: access_token,
            CONF_REFRESH_TOKEN: refresh_token,
        }
        if new_data != entry.data:
            hass.config_entries.async_update_entry(entry, data=new_data)

    client = HapiixClient(
        async_get_clientsession(hass),
        entry.data[CONF_ACCESS_TOKEN],
        entry.data.get(CONF_REFRESH_TOKEN),
        async_save_tokens,
    )
    coordinator = HapiixCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = HapiixRuntimeData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HapiixConfigEntry) -> bool:
    """Unload a Hapiix config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

