"""Stateless Home Assistant buttons for Siemens Mobile trigger widgets."""
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .api import SiemensOzw672ApiError
from .const import CONF_DEVICE
from .entity import SiemensOzw672Entity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add automatically discovered buttons to the existing device."""
    coordinator = entry.runtime_data
    async_add_entities(
        SiemensOzw672TriggerButton(coordinator, entry, trigger)
        for trigger in coordinator.mobile_triggers
    )


class SiemensOzw672TriggerButton(SiemensOzw672Entity, ButtonEntity):
    """Send one event without polling or restoring the trigger value."""

    def __init__(self, coordinator, entry, trigger):
        super().__init__(coordinator, {
            "entry_id": f"{entry.entry_id}_mobile_trigger_{trigger.identifier}",
            "device_id": entry.entry_id,
            "device_name": entry.data[CONF_DEVICE],
        })
        self.trigger = trigger
        self._attr_name = trigger.name

    async def async_press(self):
        """Perform exactly one write; never restore or refresh the datapoint."""
        try:
            await self.coordinator.api.async_write_datapoint(
                self.trigger.datapoint_id,
                self.trigger.datapoint_type,
                self.trigger.pressed_value,
            )
        except SiemensOzw672ApiError as err:
            raise HomeAssistantError("The OZW672 trigger write failed") from err
