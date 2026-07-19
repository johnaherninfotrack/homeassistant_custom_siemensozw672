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
    UnitOfTemperature
)
from homeassistant.components.select import SelectEntity

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

def parse_numeric(raw):
    """Parse a numeric reading from the OZW672, or None if it carries no value.

    The device pads values ("       19.8") and reports a run of dashes ("---")
    when a datapoint has no reading. Returning None makes the entity unknown
    rather than inventing a number, which would otherwise be recorded as a real
    measurement in long-term statistics.

    Note this deliberately does not use str.isnumeric(): that returns False for
    "19.8" (the decimal point disqualifies it) and for "-3", which is how
    decimals ended up truncated and sub-1.0 values read as zero.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or set(text) == {"-"}:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def decimal_digits(config_entry):
    """Display precision from the datapoint description, or None if absent.

    Not every datapoint returns DecimalDigits, so this must not subscript it
    directly - doing so raised KeyError inside the state machinery and silently
    froze the affected entities.
    """
    raw = (config_entry.get("DPDescr") or {}).get("DecimalDigits")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = entry.runtime_data

    datapoints = coordinator.data
    # Add sensors
    entities=[]
    for item in datapoints:
        _LOGGER.debug(f"SENSOR Data Point Item: {datapoints[item]}")
        # Reset per datapoint so a non-matching item cannot reuse the previous config.
        dp_config=None
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
        if dp_config is not None:
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
                elif datapoints[item]["Data"]["Type"] == "Numeric" and datapoints[item]["Data"]["Unit"] in ['kW', 'W']:
                    entities.append(dp_config)
                    async_add_entities([SiemensOzw672PowerSensor(coordinator,dp_config)])
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
        """Return the state of the sensor.

        This is the fallback for datapoint types with no dedicated class, most
        of which are enumerations reporting text such as "Boost heating", so the
        value is passed through as-is. A run of dashes is the device's no-data
        sentinel and becomes None.
        """
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        if not data or set(data) == {"-"}:
            return None
        return data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return the device class of the sensor.

        None, because the datapoint type is unknown. The previous
        "siemens_ozw672__custom_device_class" was a legacy custom device class
        string, which modern Home Assistant rejects.
        """
        return None
    
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
    def native_value(self):
        """Return the temperature, or None when the device reports no data."""
        item=self.config_entry["Id"]
        return parse_numeric(self.coordinator.data[item]["Data"]["Value"])

    @property
    def suggested_display_precision(self):
        """Decimal places to display, taken from the datapoint description."""
        return decimal_digits(self.config_entry)

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
            return UnitOfTemperature.CELSIUS
        elif data == "°F":
            return UnitOfTemperature.FAHRENHEIT
        elif data == "K":
            return UnitOfTemperature.KELVIN
        else:
            return UnitOfTemperature.CELSIUS


class SiemensOzw672PercentSensor(SiemensOzw672Entity,SensorEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672PercentSensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def native_value(self):
        """Return the percentage, or None when the device reports no data.

        Previously returned a string like "42%", which is not a valid state for
        a MEASUREMENT sensor - the unit belongs in native_unit_of_measurement.
        """
        item=self.config_entry["Id"]
        return parse_numeric(self.coordinator.data[item]["Data"]["Value"])

    @property
    def native_unit_of_measurement(self):
        """Return the native_unit_of_measurement of the sensor."""
        return PERCENTAGE

    @property
    def suggested_display_precision(self):
        """Decimal places to display, taken from the datapoint description."""
        return decimal_digits(self.config_entry)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_PERCENT

    @property
    def device_class(self):
        """Return the device class of the sensor.

        There is no percentage device class; the unit alone is correct. The
        previous "siemens_ozw672__percent_device_class" was a legacy custom
        device class string, which modern Home Assistant rejects.
        """
        return None
    
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
    def native_value(self):
        """Return the reading, or None when the device reports no data."""
        item=self.config_entry["Id"]
        return parse_numeric(self.coordinator.data[item]["Data"]["Value"])

    @property
    def suggested_display_precision(self):
        """Decimal places to display, taken from the datapoint description."""
        return decimal_digits(self.config_entry)

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

class SiemensOzw672PowerSensor(SiemensOzw672Entity,SensorEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672PowerSensor: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'
        

    @property
    def native_value(self):
        """Return the reading, or None when the device reports no data."""
        item=self.config_entry["Id"]
        return parse_numeric(self.coordinator.data[item]["Data"]["Value"])

    @property
    def suggested_display_precision(self):
        """Decimal places to display, taken from the datapoint description."""
        return decimal_digits(self.config_entry)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_POWER

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return SensorDeviceClass.POWER
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.MEASUREMENT
    
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
    def native_value(self):
        """Return the reading, or None when the device reports no data."""
        item=self.config_entry["Id"]
        return parse_numeric(self.coordinator.data[item]["Data"]["Value"])

    @property
    def suggested_display_precision(self):
        """Decimal places to display, taken from the datapoint description."""
        return decimal_digits(self.config_entry)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_NUMERIC

    @property
    def device_class(self):
        """Return the device class of the sensor.

        None, because a generic numeric datapoint has no specific class. The
        previous "siemens_ozw672__number_device_class" was a legacy custom
        device class string, which modern Home Assistant rejects.
        """
        return None
    
    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SensorStateClass.MEASUREMENT
    
