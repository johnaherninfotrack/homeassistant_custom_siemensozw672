"""Binary sensor platform for Siemens OZW672."""
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import BINARY_SENSOR
from .const import BINARY_SENSOR_DEVICE_CLASS
from .const import DEFAULT_NAME
from .const import DOMAIN
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
    """Setup binary sensor platform."""
    coordinator = entry.runtime_data
    configs = build_datapoint_configs(entry, coordinator, "binarysensor")
    async_add_entities(
        SiemensOzw672BinarySensor(coordinator, dp_config) for dp_config in configs
    )

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

