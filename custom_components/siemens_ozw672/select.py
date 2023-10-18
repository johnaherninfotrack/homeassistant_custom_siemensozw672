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

from .entity import SiemensOzw672Entity
from .api import SiemensOzw672ApiClient
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.select import SelectEntity

from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
)

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup select platform."""
    _LOGGER.debug(f"SELECT - Setup_Entry.  DATA: {hass.data[DOMAIN]}")    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"SELECT ***** Data: {coordinator.data}")
    _LOGGER.debug(f"SELECT ***** Config: {entry.as_dict()}")

    datapoints = coordinator.data
    # Add sensors
    entities=[]
    entityconfig=""
    for item in datapoints:
        _LOGGER.debug(f"SELECT Data Point Item: {datapoints[item]}")
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
                ### Need to support prefixing our entites by Function and Operation Line (Referenced in the manual)
                prefix=""
                if entry.data[CONF_PREFIX_FUNCTION] == True: prefix=f'{dp_data["MenuItem"]} - '
                if entry.data[CONF_PREFIX_OPLINE] == True: prefix=prefix + f'{dp_data["OpLine"]} '
                dp_config.update({'entity_prefix': prefix})
                break
        ### Add our Select Entities        
        if not dp_config == "":
            if dp_config["DPDescr"]["HAType"] == "select":
                _LOGGER.debug(f"SELECT Adding Entity with config: {dp_config} and data: {dp_data}")
                entities.append(dp_config)
                async_add_entities([SiemensOzw672SelectControl(coordinator,dp_config)])
            else:
                # DO nothing - unknown datapoint types will be added in the sensor domain.
                continue

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
