"""Switch platform for Siemens OZW672."""
from homeassistant.components.switch import SwitchEntity

from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON_SWITCH
from .const import SWITCH
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE
from .entity import SiemensOzw672Entity

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
    _LOGGER.debug(f"SWITCH - Setup_Entry.  DATA: {hass.data[DOMAIN]}")  
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"SWITCH ***** Data: {coordinator.data}")
    _LOGGER.debug(f"SWITCH ***** Config: {entry.as_dict()}")

    datapoints = coordinator.data
    # Add sensors
    entities=[]
    entityconfig=""
    for item in datapoints:
        _LOGGER.debug(f"SWITCH Data Point Item: {datapoints[item]}")
        for dp_data in entry.data["datapoints"]:
            if dp_data["Id"] == item :
                dp_config=dp_data
                if int(dp_data["OpLine"]) > 1:
                    identifier = dp_data["OpLine"] 
                else:
                    identifier="00"+item
                ### Will use the OpLine as the identifier if it exists. If not - we will use the API ID.  
                #   Note: the API datapoint ID can change if the tree is re-created.  
                #   I am hoping that by using the OpLine as the identifier - we will avoid duplicate sensors
                dp_config.update({'entry_id': entry.entry_id + "_" + identifier}) 
                dp_config.update({'device_id': entry.entry_id})
                dp_config.update({'device_name': entry.data["devicename"]})
                prefix=""
                if entry.data[CONF_PREFIX_FUNCTION] == True: 
                    prefix=f'{dp_data["MenuItem"]} - '
                if entry.data[CONF_PREFIX_OPLINE] == True: 
                    prefix=prefix + f'{dp_data["OpLine"]} '
                dp_config.update({'entity_prefix': prefix})
                break
        # At this point - the config for the datapoint is in dp_config
        #               - the data is in dp_data
        if not dp_config == "":
            if dp_config["DPDescr"]["HAType"] == "switch":
                _LOGGER.debug(f"SWITCH Adding Entity with config: {dp_config} and data: {dp_data}")
                entities.append(dp_config)
                async_add_entities([SiemensOzw672BinarySwitch(coordinator,dp_config)])
            else:
                # DO nothing - unknown datapoint types will be added in the sensor domain.
                continue


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
        _LOGGER.debug(f'SiemensOzw672BinarySwitch - Will update ID: {item} to Value: 1')
        output = await self.coordinator.api.async_write_data(self.config_entry,'1')
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        item=self.config_entry["Id"]
        _LOGGER.debug(f'SiemensOzw672BinarySwitch - Will update ID: {item} to Value: 0')
        output = await self.coordinator.api.async_write_data(self.config_entry,'0')
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return
