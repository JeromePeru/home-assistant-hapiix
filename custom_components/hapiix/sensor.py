"""Summary sensors for Hapiix members and messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HapiixConfigEntry
from .entity import HapiixEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HapiixConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Hapiix summary sensors."""
    async_add_entities([HapiixMembersSensor(entry), HapiixMessagesSensor(entry)])


class HapiixMembersSensor(HapiixEntity, SensorEntity):
    """Number and directory of Hapiix members."""

    _attr_translation_key = "members"
    _attr_icon = "mdi:account-group"

    def __init__(self, entry: HapiixConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_members"

    @property
    def native_value(self) -> int:
        """Return the number of members."""
        return len(self.coordinator.data.members)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return a privacy-conscious member directory."""
        members = []
        for member in self.coordinator.data.members:
            full_name = " ".join(
                part
                for part in (member.get("firstName"), member.get("lastName"))
                if part
            ).strip()
            members.append(
                {
                    "name": full_name or "Member",
                    "role": member.get("role"),
                    "state": member.get("state"),
                    "current_user": bool(member.get("isCurrentUser", False)),
                }
            )
        return {"members": members}


class HapiixMessagesSensor(HapiixEntity, SensorEntity):
    """Number and metadata of Hapiix messages."""

    _attr_translation_key = "messages"
    _attr_icon = "mdi:message-badge"

    def __init__(self, entry: HapiixConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_messages"

    @property
    def native_value(self) -> int:
        """Return the number of messages."""
        return len(self.coordinator.data.messages)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return message metadata without media URLs or credentials."""
        messages = []
        for message in self.coordinator.data.messages:
            messages.append(
                {
                    "id": message.get("id"),
                    "date": _parse_date(message.get("date")),
                    "type": message.get("type"),
                    "state": message.get("state"),
                }
            )
        return {
            "unread": sum(
                str(message.get("state", "")).upper() == "NEW"
                for message in self.coordinator.data.messages
            ),
            "messages": messages,
        }


def _parse_date(value: Any) -> str | None:
    """Return a stable ISO date representation."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

