"""DataUpdateCoordinator for Siemens OZW672.

Lives in its own module rather than __init__.py so the shape of the integration
matches what Home Assistant expects (the `common-modules` convention): api.py
for the client, coordinator.py for the coordinator, entity.py for the base
entity.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SiemensOzw672ApiClient,
    SiemensOzw672ApiError,
    SiemensOzw672AuthError,
)
from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

# The coordinator is stored on the config entry itself via runtime_data, rather
# than in hass.data[DOMAIN][entry_id]. This alias gives platforms a typed handle
# on it. The name must match ^[A-Za-z][A-Za-z0-9]+ConfigEntry$.
type SiemensOzw672ConfigEntry = ConfigEntry["SiemensOzw672DataUpdateCoordinator"]


class SiemensOzw672DataUpdateCoordinator(DataUpdateCoordinator):
    """Poll the OZW672 for the datapoints this config entry is watching."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SiemensOzw672ApiClient,
        datapoints,
        scaninterval: timedelta,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.datapoints = datapoints
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=scaninterval)

    async def _async_update_data(self):
        """Update all data via the OZW672 Web API."""
        try:
            return await self.api.async_get_data(self.datapoints)
        except SiemensOzw672AuthError as exception:
            # Credentials are wrong or have been revoked. Retrying forever
            # against a password that will never work is pointless; this asks
            # the user to re-enter them instead.
            raise ConfigEntryAuthFailed(str(exception)) from exception
        except SiemensOzw672ApiError as exception:
            raise UpdateFailed(str(exception)) from exception
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.debug("Unexpected error polling the OZW672: %r", exception)
            raise UpdateFailed(f"Unexpected error polling the OZW672: {exception}") from exception

    async def _async_update_data_forid(self, id):
        """Update data for one DataPoint via the OZW672 Web API."""
        for dp in self.datapoints:
            if dp["Id"] == id:
                try:
                    return await self.api.async_get_data([dp])
                except SiemensOzw672ApiError as exception:
                    raise UpdateFailed(str(exception)) from exception
        return None
