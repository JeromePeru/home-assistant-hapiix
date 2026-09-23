"""Base entity for Hapiix."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HapiixConfigEntry
from .const import DOMAIN
from .coordinator import HapiixCoordinator


class HapiixEntity(CoordinatorEntity[HapiixCoordinator]):
    """Common entity properties for one Hapiix account."""

    _attr_has_entity_name = True

    def __init__(self, entry: HapiixConfigEntry) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Hapiix",
            name=f"Hapiix ({entry.title})",
            entry_type=DeviceEntryType.SERVICE,
        )
