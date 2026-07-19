"""SelectEntity platform for Siemens OZW672."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import ICON_THERMOMETER
from .const import ICON_PERCENT
from .const import ICON_NUMERIC
from .const import SENSOR
from .const import CONF_MENUITEMS
from .const import CONF_DATAPOINTS
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE

from .entity import SiemensOzw672Entity, build_datapoint_configs
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.number import NumberEntity, NumberMode, NumberDeviceClass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature
)

import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)

def _control_class_for(reading):
    """Pick the number class for a polled reading.

    Built here rather than at module level because the classes are defined
    below.
    """
    by_unit = {
        "°C": SiemensOzw672TempControl,
        "°F": SiemensOzw672TempControl,
        "K": SiemensOzw672TempControl,
        "%": SiemensOzw672PercentControl,
        "kWh": SiemensOzw672EnergyControl,
        "Wh": SiemensOzw672EnergyControl,
        "kW": SiemensOzw672EnergyControl,
        "W": SiemensOzw672EnergyControl,
    }
    data = (reading or {}).get("Data") or {}
    return by_unit.get((data.get("Unit") or "").strip(), SiemensOzw672NumberControl)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup number platform."""
    coordinator = entry.runtime_data
    configs = build_datapoint_configs(entry, coordinator, "number")
    async_add_entities(
        _control_class_for(coordinator.data[dp_config["Id"]])(coordinator, dp_config)
        for dp_config in configs
    )


class SiemensOzw672TempControl(SiemensOzw672Entity,NumberEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672TempControl: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    async def async_set_native_value(self, value: float) -> None:
        """Update Temp ."""
        _LOGGER.debug(f'SiemensOzw672TempControl: Set_native_Value: {value}')
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        existing_value=self.coordinator.data[item]["Data"]["Value"].strip()
        decimals=self.config_entry["DPDescr"]["DecimalDigits"]
        if decimals == '0':
            new_value=round(float(value))
        else:
            new_value=round(float(value), int(decimals))
        _LOGGER.info(f'SiemensOzw672TempControl - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: {str(new_value)} from Value: {str(existing_value)}')
        output = await self.coordinator.api.async_write_data(self.config_entry,str(new_value))
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return 

    @property
    def native_value(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_THERMOMETER

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return NumberDeviceClass.TEMPERATURE
    
    @property
    def native_min_value(self) -> float:
        """Return min Temp."""
        val = float(self.config_entry["DPDescr"]["Min"])
        return val

    @property
    def native_max_value(self) -> float:
        """Return max Temp."""
        val = float(self.config_entry["DPDescr"]["Max"])
        return val

    @property
    def native_step(self) -> float:
        """Return step/resolution."""
        val = float(self.config_entry["DPDescr"]["Resolution"])
        return val

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


class SiemensOzw672PercentControl(SiemensOzw672Entity, NumberEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672PercentControl: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    async def async_set_native_value(self, value: float) -> None:
        """Update The Percentage ."""
        _LOGGER.debug(f'SiemensOzw672PercentControl: Set_native_Value: {value}')
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        existing_value=self.coordinator.data[item]["Data"]["Value"].strip()
        decimals=self.config_entry["DPDescr"]["DecimalDigits"]
        if decimals == '0':
            new_value=round(float(value))
        else:
            new_value=round(float(value), int(decimals))
        _LOGGER.info(f'SiemensOzw672PercentControl - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: {str(new_value)} from Value: {str(existing_value)}')
        output = await self.coordinator.api.async_write_data(self.config_entry,str(new_value))
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return 

    @property
    def native_value(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_PERCENT

    #@property
    #def device_class(self):
    #    """Return de device class of the sensor."""
    #    return NumberDeviceClass.PERCENTAGE

    @property
    def native_min_value(self) -> float:
        """Return min Temp."""
        val = float(self.config_entry["DPDescr"]["Min"])
        return val

    @property
    def native_max_value(self) -> float:
        """Return max Temp."""
        val = float(self.config_entry["DPDescr"]["Max"])
        return val

    @property
    def native_step(self) -> float:
        """Return step/resolution."""
        val = float(self.config_entry["DPDescr"]["Resolution"])
        return val

    @property
    def native_unit_of_measurement(self) -> str:
        """Return percentage."""
        return PERCENTAGE



class SiemensOzw672EnergyControl(SiemensOzw672Entity,NumberEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672EnergyControl: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    async def async_set_native_value(self, value: float) -> None:
        """Update Temp ."""
        _LOGGER.debug(f'SiemensOzw672EnergyControl: Set_native_Value: {value}')
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        existing_value=self.coordinator.data[item]["Data"]["Value"].strip()
        decimals=self.config_entry["DPDescr"]["DecimalDigits"]
        if decimals == '0':
            new_value=round(float(value))
        else:
            new_value=round(float(value), int(decimals))
        _LOGGER.info(f'SiemensOzw672EnergyControl - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: {str(new_value)} from Value: {str(existing_value)}')
        output = await self.coordinator.api.async_write_data(self.config_entry,str(new_value))
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return 

    @property
    def native_value(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

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
    def native_min_value(self) -> float:
        """Return min Temp."""
        val = float(self.config_entry["DPDescr"]["Min"])
        return val

    @property
    def native_max_value(self) -> float:
        """Return max Temp."""
        val = float(self.config_entry["DPDescr"]["Max"])
        return val

    @property
    def native_step(self) -> float:
        """Return step/resolution."""
        val = float(self.config_entry["DPDescr"]["Resolution"])
        return val

    @property
    def native_unit_of_measurement(self):
        """Return the native_unit_of_measurement of the sensor."""
        item=self.config_entry["Id"]
        return self.coordinator.data[item]["Data"]["Unit"].strip()



class SiemensOzw672NumberControl(SiemensOzw672Entity, NumberEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug(f"SiemensOzw672NumberControl: Config: {self.config_entry}")
        return f'{self.config_entry["entity_prefix"]}{self.config_entry["Name"]}'

    @property
    def state(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    async def async_set_native_value(self, value: float) -> None:
        """Update The Percentage ."""
        _LOGGER.debug(f'SiemensOzw672NumberControl: Set_native_Value: {value}')
        item=self.config_entry["Id"]
        opline=self.config_entry["OpLine"]
        name=self.config_entry["Name"]
        existing_value=self.coordinator.data[item]["Data"]["Value"].strip()
        decimals=self.config_entry["DPDescr"]["DecimalDigits"]
        if decimals == '0':
            new_value=round(float(value))
        else:
            new_value=round(float(value), int(decimals))
        _LOGGER.info(f'SiemensOzw672NumberControl - Will update ID/Opline/Name: {item}/{opline}/{name} to Value: {str(new_value)} from Value: {str(existing_value)}')
        output = await self.coordinator.api.async_write_data(self.config_entry,str(new_value))
        await self.coordinator._async_update_data_forid(item)
        await self.coordinator.async_request_refresh()
        return 

    @property
    def native_value(self):
        """Return the state of the sensor."""
        item=self.config_entry["Id"]
        data=self.coordinator.data[item]["Data"]["Value"].strip()
        return float(data)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_NUMERIC

    @property
    def native_min_value(self) -> float:
        """Return min Temp."""
        val = float(self.config_entry["DPDescr"]["Min"])
        return val

    @property
    def native_max_value(self) -> float:
        """Return max Temp."""
        val = float(self.config_entry["DPDescr"]["Max"])
        return val

    @property
    def native_step(self) -> float:
        """Return step/resolution."""
        val = float(self.config_entry["DPDescr"]["Resolution"])
        return val


