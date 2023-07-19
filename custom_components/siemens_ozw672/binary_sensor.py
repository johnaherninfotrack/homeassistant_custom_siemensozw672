"""Binary sensor platform for Siemens OZW672."""
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import BINARY_SENSOR
from .const import BINARY_SENSOR_DEVICE_CLASS
from .const import DEFAULT_NAME
from .const import DOMAIN
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
    """Setup binary sensor platform."""
    _LOGGER.debug(f"BINARY SENSOR - Setup_Entry.  DATA: {hass.data[DOMAIN]}")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"BINARY SENSOR ***** Data: {coordinator.data}")
    _LOGGER.debug(f"BINARY SENSOR ***** Config: {entry.as_dict()}")

    datapoints = coordinator.data
    # Add sensors
    entities=[]
    entityconfig=""
    for item in datapoints:
        _LOGGER.debug(f"BINARY SENSOR Data Point Item: {datapoints[item]}")
        for dp_data in entry.data["datapoints"]:
            if dp_data["Id"] == item :
                dp_config=dp_data
                if int(dp_data["OpLine"]) > 1:
                    identifier = dp_data["OpLine"] 
                else:
                    identifier="00"+Item
                ### Will use the OpLine as the identifier if it exists. If not - we will use the API ID.  
                #   Note: the API datapoint ID can change if the tree is re-created.  
                #   I am hoping that by using the OpLine as the identifier - we will avoid duplicate sensors
                dp_config.update({'entry_id': entry.entry_id + "_" + identifier}) 
                dp_config.update({'device_id': entry.entry_id})
                dp_config.update({'device_name': entry.data["devicename"]})
                prefix=""
                if entry.data[CONF_PREFIX_FUNCTION] == True: prefix=f'{dp_data["MenuItem"]} - '
                if entry.data[CONF_PREFIX_OPLINE] == True: prefix=prefix + f'{dp_data["OpLine"]} '
                dp_config.update({'entity_prefix': prefix})
                break
        # At this point - the config for the datapoint is in dp_config
        #               - the data is in dp_data
        if not dp_config == "":
            if dp_config["DPDescr"]["HAType"] == "binarysensor":
                _LOGGER.debug(f"BINARY SENSOR Adding Entity with config: {dp_config} and data: {dp_data}")
                entities.append(dp_config)
                async_add_entities([SiemensOzw672BinarySensor(coordinator,dp_config)])
            else:
                # DO nothing - unknown datapoint types will be added in the sensor domain.
                continue

class SiemensOzw672BinarySensor(SiemensOzw672Entity, BinarySensorEntity):
    """siemens_ozw672 binary_sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672BinarySensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""
        return BINARY_SENSOR_DEVICE_CLASS

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        item=self.config_entry["Id"]
        return self.coordinator.data[item]["Data"]["Value"] in ['On']

