"""Sensor platform for Siemens OZW672."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .const import CONF_MENUITEMS
from .const import CONF_DATAPOINTS
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE
from .const import ICON_THERMOMETER
from .const import ICON_PERCENT
from .const import ICON_NUMERIC
from .const import ICON_POWER

from .entity import SiemensOzw672Entity
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TEMP_KELVIN
)
from homeassistant.components.select import SelectEntity

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

def is_float(string):
    if "." in string:
        if string.replace(".", "").isnumeric():
            return True
    else:
        return False

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    _LOGGER.debug(f"SENSOR - Setup_Entry.  DATA: {hass.data[DOMAIN]}")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"SENSOR ***** Data: {coordinator.data}")
    _LOGGER.debug(f"SENSOR ***** Config: {entry.as_dict()}")

    datapoints = coordinator.data
    # Add sensors
    entities=[]
    entityconfig=""
    for item in datapoints:
        _LOGGER.debug(f"SENSOR Data Point Item: {datapoints[item]}")
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
                if entry.data[CONF_PREFIX_FUNCTION] == True: prefix=f'{dp_data["MenuItem"]} - '
                if entry.data[CONF_PREFIX_OPLINE] == True: prefix=prefix + f'{dp_data["OpLine"]} '
                dp_config.update({'entity_prefix': prefix})
                break
        # At this point - the config for the datapoint is in dp_config
        #               - the data is in dp_data
        if not dp_config == "":
            if dp_config["DPDescr"]["HAType"] == "sensor":
                _LOGGER.debug(f"SENSOR Adding Entity with config: {dp_config} and data: {dp_data}")
                if datapoints[item]["Data"]["Type"] == "Numeric" and datapoints[item]["Data"]["Unit"] in ['°C', '°F', 'K']:
                    entities.append(dp_config)
                    async_add_entities([SiemensOzw672TempSensor(coordinator,dp_config)])
                elif datapoints[item]["Data"]["Type"] == "Numeric" and datapoints[item]["Data"]["Unit"] in ['%']:
                    entities.append(dp_config)
                    async_add_entities([SiemensOzw672PercentSensor(coordinator,dp_config)])
                elif datapoints[item]["Data"]["Type"] == "Numeric" and datapoints[item]["Data"]["Unit"] in ['kWh', 'Wh']:
                    entities.append(dp_config)
                    async_add_entities([SiemensOzw672EnergySensor(coordinator,dp_config)])
                elif datapoints[item]["Data"]["Type"] == "Numeric":
                    entities.append(dp_config)
                    async_add_entities([SiemensOzw672NumberSensor(coordinator,dp_config)])
                else:
                    # All unknown data types will produce a read only sensor
                    async_add_entities([SiemensOzw672Sensor(coordinator,dp_config)])
                continue


class SiemensOzw672Sensor(SiemensOzw672Entity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672Sensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672Sensor: Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            return int(data)
        return data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672Sensor: Native Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            return int(data)
        return data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "siemens_ozw672__custom_device_class"
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return None
    
    @property
    def native_unit_of_measurement(self):
        """Return the native_unit_of_measurement of the sensor."""
        return None


class SiemensOzw672TempSensor(SiemensOzw672Entity,SensorEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672Sensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'
        

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672Sensor: Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672Sensor: Native Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_THERMOMETER

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return SensorDeviceClass.TEMPERATURE
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.MEASUREMENT
    
    @property
    def native_unit_of_measurement(self):
        """Return the native_unit_of_measurement of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Unit"].strip()
        if data == "°C":
            return TEMP_CELSIUS
        elif data == "°F":
            return TEMP_FAHRENHEIT
        elif data == "K":
            return TEMP_KELVIN
        else:
            return TEMP_CELSIUS


class SiemensOzw672PercentSensor(SiemensOzw672Entity,SensorEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672PercentSensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672PercentSensor: Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return f'{data}%'

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_PERCENT

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "siemens_ozw672__percent_device_class"
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.MEASUREMENT

class SiemensOzw672EnergySensor(SiemensOzw672Entity,SensorEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672EnergySensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'
        

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672EnergySensor: Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672EnergySensor: Native Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_POWER

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return SensorDeviceClass.ENERGY
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.TOTAL_INCREASING
    
    @property
    def native_unit_of_measurement(self):
        """Return the native_unit_of_measurement of the sensor."""
        item=self.config_entry["Id"]
        return self.coordinator.data[item]["Data"]["Unit"].strip()



class SiemensOzw672NumberSensor(SiemensOzw672Entity,SensorEntity):
    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672GenericNumberSensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'
        
    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672GenericNumberSensor: Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f'SiemensOzw672GenericNumberSensor: Native Data: {self.coordinator.data}')
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if data.isnumeric() :
            if is_float(data):
                return float(data)
            else:
                return int(data)
        return data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_NUMERIC

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "siemens_ozw672__number_device_class"
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.MEASUREMENT
    
    #@property
    #def suggested_display_precision(self):
    #    """Return the suggested_display_precision of the sensor."""
    #    _LOGGER.debug(f'SiemensOzw672GenericNumberSensor: suggested_display_precision: {self.config_entry["DPDescr"]["DecimalDigits"]}')
    #    return int(self.config_entry["DPDescr"]["DecimalDigits"])