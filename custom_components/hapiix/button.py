"""Door-opening buttons for Hapiix."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HapiixConfigEntry
from .api import HapiixApiError, HapiixAuthenticationError, HapiixConnectionError
from .entity import HapiixEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HapiixConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create buttons and track doors discovered on later refreshes."""
    coordinator = entry.runtime_data.coordinator
    known_ids: set[str] = set()

    @callback
    def async_add_new_doors() -> None:
        entities: list[HapiixDoorButton] = []
        for door in coordinator.data.doors:
            door_id = str(door.get("id", ""))
            if door_id and door_id not in known_ids:
                known_ids.add(door_id)
                entities.append(HapiixDoorButton(entry, door_id))
        if entities:
            async_add_entities(entities)

    async_add_new_doors()
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_doors))


class HapiixDoorButton(HapiixEntity, ButtonEntity):
    """Button that opens one authorized Hapiix door."""

    _attr_icon = "mdi:door-open"

    def __init__(self, entry: HapiixConfigEntry, door_id: str) -> None:
        super().__init__(entry)
        self._door_id = door_id
        self._attr_unique_id = f"{entry.entry_id}_door_{door_id}"

    @property
    def _door(self) -> dict[str, Any]:
        return next(
            (
                door
                for door in self.coordinator.data.doors
                if str(door.get("id", "")) == self._door_id
            ),
            {},
        )

    @property
    def name(self) -> str:
        """Return the door name."""
        return str(self._door.get("name") or self._door.get("number") or "Door")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return non-sensitive door information."""
        return {
            "door_number": self._door.get("number"),
            "favorite": bool(self._door.get("isFavorite", False)),
        }

    async def async_press(self) -> None:
        """Open the selected door."""
        try:
            await self._entry.runtime_data.client.open_door(self._door_id)
        except HapiixAuthenticationError:
            await self._entry.async_start_reauth(self.hass)
            raise
        except (HapiixConnectionError, HapiixApiError):
            raise
