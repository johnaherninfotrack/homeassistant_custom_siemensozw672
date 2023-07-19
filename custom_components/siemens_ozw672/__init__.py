"""
Custom integration to integrate Siemens OZW672 with Home Assistant.
For more details about this integration, please refer to
https://github.com/jahern2502/siemens-ozw672
"""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import SiemensOzw672ApiClient
from .const import CONF_HOST
from .const import CONF_DEVICE
from .const import CONF_DEVICE_ID
from .const import CONF_PROTOCOL
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import CONF_DATAPOINTS
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    host = entry.data.get(CONF_HOST)
    protocol = entry.data.get(CONF_PROTOCOL)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    device = entry.data.get(CONF_DEVICE)
    deviceid = entry.data.get(CONF_DEVICE_ID)
    datapoints = entry.data.get(CONF_DATAPOINTS)

    session = async_get_clientsession(hass)
    client = SiemensOzw672ApiClient(host, protocol, username, password, session)
    coordinator = SiemensOzw672DataUpdateCoordinator(hass, client=client, datapoints=datapoints)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )
    entry.add_update_listener(async_reload_entry)
    return True


class SiemensOzw672DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""
    def __init__(
        self,
        hass: HomeAssistant,
        client: SiemensOzw672ApiClient,
        datapoints,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.datapoints = datapoints
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update all data via the OZW672 Web API."""
        try:
            return await self.api.async_get_data(self.datapoints)
            
        except Exception as exception:
            _LOGGER.debug(f'Exception: {repr(exception)}')
            raise UpdateFailed() from exception

    async def _async_update_data_forid(self,id):
        """Update data for one DataPoint via the OZW672 Web API."""
        for dp in self.datapoints:
            if dp["Id"] == id:
                try:
                    return await self.api.async_get_data([dp])
                    
                except Exception as exception:
                    _LOGGER.debug(f'Exception: {repr(exception)}')
                    raise UpdateFailed() from exception

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
