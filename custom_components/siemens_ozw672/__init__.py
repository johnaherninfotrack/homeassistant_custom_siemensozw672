"""
Custom integration to integrate Siemens OZW672 with Home Assistant.
For more details about this integration, please refer to
https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672
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
from .const import CONF_SCANINTERVAL
from .const import CONF_HTTPTIMEOUT
from .const import CONF_HTTPRETRIES
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE
from .const import DEFAULT_HTTPTIMEOUT
from .const import DEFAULT_HTTPRETRIES
from .const import DEFAULT_SCANINTERVAL
from .const import CONF_VERSION
from .const import CONF_MINOR_VERSION


#SCAN_INTERVAL = timedelta(seconds=60)

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
    conf_scaninterval = entry.options.get(CONF_SCANINTERVAL)
    conf_httptimeout = entry.options.get(CONF_HTTPTIMEOUT)
    conf_httpretries = entry.options.get(CONF_HTTPRETRIES)
    if conf_scaninterval == None: conf_scaninterval = DEFAULT_SCANINTERVAL
    if conf_httptimeout == None: conf_httptimeout = DEFAULT_HTTPTIMEOUT
    if conf_httpretries == None: conf_httpretries = DEFAULT_HTTPRETRIES

    session = async_get_clientsession(hass)
    client = SiemensOzw672ApiClient(host, protocol, username, password, session, timeout=conf_httptimeout, retries=conf_httpretries)
    coordinator = SiemensOzw672DataUpdateCoordinator(hass, client=client, datapoints=datapoints, scaninterval=(timedelta(seconds = conf_scaninterval)))
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
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_migrate_entry(hass, entry: ConfigEntry):                                                                                               
    if entry.version == CONF_VERSION and entry.minor_version == CONF_MINOR_VERSION:                                                                    
        return True                                                                                                                                    
    _LOGGER.debug("Upgrading OZW Configuration")                                                                               
    try:                                                                                                                                               
        host = entry.data.get(CONF_HOST)                                                                                                               
        protocol = entry.data.get(CONF_PROTOCOL)                                                                                                       
        username = entry.data.get(CONF_USERNAME)                                                                                                       
        password = entry.data.get(CONF_PASSWORD)                                                                                                       
        session = async_get_clientsession(hass)                                                                                                        
        conf_httptimeout = entry.options.get(CONF_HTTPTIMEOUT)                                                                                         
        conf_httpretries = entry.options.get(CONF_HTTPRETRIES)                                                                                         
        if conf_httptimeout == None: conf_httptimeout = DEFAULT_HTTPTIMEOUT                                                                            
        if conf_httpretries == None: conf_httpretries = DEFAULT_HTTPRETRIES                                                                            
        client = SiemensOzw672ApiClient(host, protocol, username, password, session, timeout=conf_httptimeout, retries=conf_httpretries)               
        datapoints = entry.data.get(CONF_DATAPOINTS)                                                                                                   
        all_dpdata = await client.async_get_data(datapoints)                                                                                                                                                                                         
        all_dpdescr = await client.async_get_data_descr(datapoints, all_dpdata, True)                                                                                                                                                                 
        newdatapoints=[]                                                                                                                               
        for dpjson in datapoints:                                                                                                                      
            dpdescr = all_dpdescr[dpjson["Id"]]["Description"]                                                                                         
            dpdata = all_dpdata[dpjson["Id"]]["Data"]                                                                                   
            newdatapoints.append({"Id": dpjson["Id"],"WriteAccess": dpjson["WriteAccess"],"OpLine": dpjson["OpLine"], "Name": dpdescr["Name"],"MenuItem": dpjson["MenuItem"], "DPDescr": dpdescr })
        _data={**entry.data}                                                                                                                                                                       
        _data[CONF_DATAPOINTS]=newdatapoints                                                                                                                                                       
        hass.config_entries.async_update_entry(entry, data=_data,minor_version=CONF_MINOR_VERSION, version=CONF_VERSION)                                                                           
        _LOGGER.debug("Config Check Complete")                                                                                                                                                     
        return True                                                                                                                                                                                
    except Exception as exception:                                                                                                                                                                 
        _LOGGER.error(f'Config Check Failed: {repr(exception)}')                                                                                                                                   
        return False                      

class SiemensOzw672DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""
    def __init__(
        self,
        hass: HomeAssistant,
        client: SiemensOzw672ApiClient,
        datapoints,
        scaninterval
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
    await hass.config_entries.async_reload(entry.entry_id)
