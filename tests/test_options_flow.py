"""Tests for the siemens_ozw672 options flow.

Home Assistant made OptionsFlow.config_entry a read-only property, so the previous
pattern of assigning `self.config_entry = config_entry` in __init__ raised

    AttributeError: property 'config_entry' of 'SiemensOzw672OptionsFlowHandler'
    object has no setter

which made the options dialog impossible to open.
"""
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_ozw672.const import (
    CONF_HTTPRETRIES,
    CONF_HTTPTIMEOUT,
    CONF_SCANINTERVAL,
    CONF_USE_DEVICE_LONGNAME,
    DEFAULT_HTTPRETRIES,
    DEFAULT_HTTPTIMEOUT,
    DEFAULT_SCANINTERVAL,
    DOMAIN,
)

EXISTING_OPTIONS = {
    CONF_HTTPTIMEOUT: 30,
    CONF_HTTPRETRIES: 4,
    CONF_SCANINTERVAL: 120,
    CONF_USE_DEVICE_LONGNAME: True,
    "switch": True,
    "select": True,
    "number": True,
    "binary_sensor": True,
    "sensor": True,
}


def _add_entry(hass, options):
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, options=options, entry_id="test_options_entry"
    )
    entry.add_to_hass(hass)
    return entry


async def test_options_flow_opens(hass):
    """The options dialog opens instead of raising AttributeError."""
    entry = _add_entry(hass, EXISTING_OPTIONS)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_options_flow_saves_changes(hass):
    """Submitting the form writes the new options back to the entry."""
    entry = _add_entry(hass, EXISTING_OPTIONS)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    new_options = {**EXISTING_OPTIONS, CONF_SCANINTERVAL: 300}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=new_options
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SCANINTERVAL] == 300


async def test_options_flow_with_no_existing_options(hass):
    """An entry saved before options existed falls back to the defaults.

    This is the path that reads self.config_entry, so it also guards the property
    access that previously happened in __init__.
    """
    entry = _add_entry(hass, {})

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    schema_defaults = {
        str(key): key.default() for key in result["data_schema"].schema
    }
    assert schema_defaults[CONF_HTTPTIMEOUT] == DEFAULT_HTTPTIMEOUT
    assert schema_defaults[CONF_HTTPRETRIES] == DEFAULT_HTTPRETRIES
    assert schema_defaults[CONF_SCANINTERVAL] == DEFAULT_SCANINTERVAL
