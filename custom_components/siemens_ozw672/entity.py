"""SiemensOzw672Entity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION

import json
import logging
_LOGGER: logging.Logger = logging.getLogger(__package__)


class SiemensOzw672Entity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.coordinator = coordinator
        _LOGGER.debug(f"SiemensOzw672Entity - config_entry: {config_entry}")

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry["entry_id"]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.config_entry["device_id"])},
            "name": self.config_entry["device_name"],
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        _LOGGER.debug(f'SiemensOzw672Entity - device_state_attributes - id: {self.coordinator.data.get("id")}')
        return {
            "attribution": ATTRIBUTION,
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
