"""End-to-end setup tests.

These exercise the path the restructure touched: the coordinator now lives on
ConfigEntry.runtime_data rather than hass.data[DOMAIN][entry_id], and setup
failure is signalled by async_config_entry_first_refresh() rather than by
checking last_update_success afterwards.
"""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_ozw672.api import (
    SiemensOzw672AuthError,
    SiemensOzw672ConnectionError,
)
from custom_components.siemens_ozw672.coordinator import (
    SiemensOzw672DataUpdateCoordinator,
)
from custom_components.siemens_ozw672.const import (
    VERSION,
    CONF_MINOR_VERSION,
    CONF_VERSION,
    DOMAIN,
)

DATAPOINT = {
    "Id": "1960",
    "WriteAccess": "false",
    "OpLine": "39",
    "Name": "Outside temp",
    "MenuItem": "Diagnostics consumer",
    "DPDescr": {
        "DecimalDigits": "1",
        "HAType": "sensor",
        "Name": "Outside temp",
        "Type": "Numeric",
        "Unit": "°C",
    },
}

POLLED = {
    "1960": {
        "Data": {"Type": "Numeric", "Value": "       19.8", "Unit": "°C"},
        "Result": {"Success": "true"},
    }
}

ENTRY_DATA = {
    "protocol": "https",
    "hostname": "192.0.2.10",
    "username": "someone",
    "password": "hunter2",
    "devicename": "RVS43.345/109",
    "devicelongname": "0.1 RVS43.345/109",
    "prefix_with_function": False,
    "prefix_with_opline": False,
    "use_device_longname": False,
    "deviceid": "00FD3100033C:008600004EBF",
    "menuitems": [],
    "datapoints": [DATAPOINT],
}


def _entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        options={"scaninterval": 60, "httptimeout": 30, "httpretries": 2},
        unique_id=ENTRY_DATA["deviceid"],
        entry_id="test_setup_entry",
        # Match the current schema, otherwise async_migrate_entry runs and tries
        # to re-fetch every datapoint description from the device.
        version=CONF_VERSION,
        minor_version=CONF_MINOR_VERSION,
    )


async def test_setup_stores_coordinator_on_runtime_data(hass):
    """Setup succeeds and the coordinator is reachable via runtime_data."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(return_value=POLLED),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert isinstance(entry.runtime_data, SiemensOzw672DataUpdateCoordinator)
    assert entry.runtime_data.data == POLLED


async def test_sensor_entity_is_created_with_full_precision(hass):
    """The datapoint becomes a sensor reporting the untruncated value."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(return_value=POLLED),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    states = [s for s in hass.states.async_all() if s.entity_id.startswith("sensor.")]
    assert states, "no sensor entity was created"
    assert float(states[0].state) == pytest.approx(19.8)


async def test_device_registry_reports_real_hardware(hass):
    """The device page shows the manufacturer and model, not the integration.

    device_info previously reported the integration's own version as the model
    ("0.3.7") and "Siemens OZW672" as the manufacturer of an RVS43.
    """
    from homeassistant.helpers import device_registry as dr

    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(return_value=POLLED),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    devices = dr.async_get(hass).devices.get_devices_for_config_entry_id(entry.entry_id)
    assert devices, "no device was registered"
    device = devices[0]
    assert device.manufacturer == "Siemens"
    # Not the integration version, which is what it used to be.
    assert device.model != VERSION
    assert device.model == ENTRY_DATA["devicename"]


async def test_entity_name_is_composed_from_device(hass):
    """has_entity_name means HA prefixes the device name itself."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(return_value=POLLED),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = next(s for s in hass.states.async_all() if s.entity_id.startswith("sensor."))
    friendly = state.attributes["friendly_name"]
    assert friendly.startswith(ENTRY_DATA["devicename"])
    assert "Outside temp" in friendly


async def test_connection_failure_is_retried_not_fatal(hass):
    """An unreachable device leaves the entry in SETUP_RETRY, not failed."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(side_effect=SiemensOzw672ConnectionError("unreachable")),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_bad_credentials_trigger_reauth_not_endless_retry(hass):
    """Rejected credentials ask the user to fix them.

    Previously every failure became ConfigEntryNotReady, so a wrong password was
    retried forever with no indication of what was wrong.
    """
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(side_effect=SiemensOzw672AuthError("rejected")),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_unload_leaves_nothing_behind(hass):
    """Unloading removes the entities and reports success honestly.

    async_unload_entry previously filtered on coordinator.platforms, which was
    always empty, so all([]) reported success while unloading nothing.
    """
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_ozw672.SiemensOzw672ApiClient.async_get_data",
        new=AsyncMock(return_value=POLLED),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        live = [s for s in hass.states.async_all() if s.entity_id.startswith("sensor.")]
        assert live, "no sensor entity was created"
        entity_id = live[0].entity_id
        assert hass.states.get(entity_id).state == "19.8"

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    # Home Assistant keeps the state object and marks it unavailable rather than
    # deleting it, so assert on that rather than on the entity disappearing.
    assert hass.states.get(entity_id).state == "unavailable"
