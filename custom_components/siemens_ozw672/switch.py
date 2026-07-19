"""Switch platform for Siemens OZW672."""
from homeassistant.components.switch import SwitchEntity

from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON_SWITCH
from .const import SWITCH
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE
from .entity import SiemensOzw672Entity, build_datapoint_configs

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup switch platform."""
    coordinator = entry.runtime_data
    configs = build_datapoint_configs(entry, coordinator, "switch")
    async_add_entities(
        SiemensOzw672BinarySwitch(coordinator, dp_config) for dp_config in configs
    )

class SiemensOzw672BinarySwitch(SiemensOzw672Entity, SwitchEntity):
    """siemens_ozw672 switch class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672BinarySwitch: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def icon(self):
        """Return the icon of this switch."""
        return ICON_SWITCH

    @property
    def is_on(self):
        """Return true if the switch is on."""
        item=self.config_entry["Id"]
        return self.coordinator.data[item]["Data"]["Value"] in ['On']

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        _LOGGER.info(f'SiemensOzw672BinarySwitch - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: 1')
        output = await self.coordinator.api.async_write_data(self.config_entry,'1')
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        _LOGGER.info(f'SiemensOzw672BinarySwitch - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: 0')
        output = await self.coordinator.api.async_write_data(self.config_entry,'0')
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return
