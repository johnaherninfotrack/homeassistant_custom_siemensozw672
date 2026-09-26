"""SelectEntity platform for Siemens OZW672."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import ICON_SELECT
from .const import SENSOR
from .const import CONF_MENUITEMS
from .const import CONF_DATAPOINTS
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE

from .entity import SiemensOzw672Entity, build_datapoint_configs
from .api import SiemensOzw672ApiClient
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.select import SelectEntity

from homeassistant.const import (
    PERCENTAGE
)

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup select platform."""
    coordinator = entry.runtime_data
    configs = build_datapoint_configs(entry, coordinator, "select")
    async_add_entities(
        SiemensOzw672SelectControl(coordinator, dp_config) for dp_config in configs
    )

class SiemensOzw672SelectControl(SiemensOzw672Entity, SelectEntity):
    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672SelectControl: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    async def async_select_option(self, option: str, **kwargs):
        """Change the selected option."""
        _LOGGER.debug(f'SiemensOzw672SelectControl - select_option String: {option}')
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        enums=self.config_entry["DPDescr"]["Enums"]
        for enum in enums:
            if enum["Text"].encode('unicode_escape').decode() == option.encode('unicode_escape').decode():
                _LOGGER.info(f'SiemensOzw672SelectControl - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: {enum["Value"]}')
                output = await self.coordinator.api.async_write_data(self.config_entry,enum["Value"])
                await self.coordinator._async_update_data_forid(item)
                await self.coordinator.async_request_refresh()
        return 

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return data

    @property
    def options(self):
        """Return the option list from the Enums discovered from the datapoint description."""
        data_options={}
        for enum in self.config_entry["DPDescr"]["Enums"]:
            idx = int(enum["Value"])
            val = enum["Text"]
            data_options[idx] = val
        return list(data_options.values())
        
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_SELECT
