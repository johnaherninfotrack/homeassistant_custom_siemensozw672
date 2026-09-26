"""Config flow tests.

The central behaviour here is that a device which is already configured cannot
be added twice. Adding datapoints goes through Reconfigure, which updates the
existing entry in place so entity unique IDs - and therefore history - survive.

Before this, async_set_unique_id() was called but never paired with
_abort_if_unique_id_configured(), and the flow then called async_create_entry()
unconditionally. Re-running setup to add a datapoint created a second entry
sharing a unique ID, re-registering every entity under a new config entry ID
(#33, #35, #37).
"""
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_ozw672.const import (
    CONF_MINOR_VERSION,
    CONF_VERSION,
    DOMAIN,
)
from tests.test_setup import ENTRY_DATA

USER_INPUT = {
    "protocol": "https",
    "hostname": "192.0.2.10",
    "username": "someone",
    "password": "hunter2",
}


def _existing_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        options={"scaninterval": 60, "httptimeout": 30, "httpretries": 2},
        unique_id=ENTRY_DATA["deviceid"],
        entry_id="existing_entry",
        version=CONF_VERSION,
        minor_version=CONF_MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    return entry


async def test_user_step_shows_form(hass):
    """The flow opens on the credentials form with no errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_bad_credentials_show_an_error_and_stay_on_the_form(hass):
    """A rejected login re-shows the form rather than aborting."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with patch(
        "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._test_credentials",
        new=AsyncMock(return_value=False),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "auth"}


async def test_unreachable_device_reports_cannot_connect(hass):
    """Credentials accepted but discovery failing is not reported as bad auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with (
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._test_credentials",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._get_menutree",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._get_devices",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


DISCOVERED_DEVICE = {
    "Id": "1327",
    "Text": {"Long": "0.1 RVS43.345/109"},
    "Name": "RVS43.345/109",
    "LongName": "0.1 RVS43.345/109",
}

ALL_DEVICES = [
    {
        "Name": "RVS43.345/109",
        "Addr": "0.1",
        "Type": "RVS43.345/109",
        "SerialNr": "008600004EBF",
    }
]

SYSINFO = {"SerialNr": "00FD3100033C"}


def _discovery_patches():
    """Patch out every device call the first two flow steps make."""
    return (
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._test_credentials",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._get_menutree",
            new=AsyncMock(return_value={"MenuItems": [DISCOVERED_DEVICE]}),
        ),
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._get_devices",
            new=AsyncMock(return_value=ALL_DEVICES),
        ),
        patch(
            "custom_components.siemens_ozw672.config_flow.SiemensOzw672FlowHandler._get_sysinfo",
            new=AsyncMock(return_value=SYSINFO),
        ),
    )


async def test_adding_an_already_configured_device_aborts(hass):
    """The regression behind #35, and the reason HA 2026.3 warned.

    async_set_unique_id() was called but never paired with
    _abort_if_unique_id_configured(), so re-running "Add Integration" for a
    device that was already set up created a second entry sharing its unique
    ID - re-registering every entity and orphaning its history.
    """
    import json

    entry = _existing_entry(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    p1, p2, p3, p4 = _discovery_patches()
    with p1, p2, p3, p4:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
        assert result["step_id"] == "device"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "devicename": json.dumps(DISCOVERED_DEVICE),
                "use_device_longname": False,
                "prefix_with_function": False,
                "prefix_with_opline": False,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Crucially: still exactly one entry, and it is the original.
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.config_entries.async_entries(DOMAIN)[0].entry_id == entry.entry_id


async def test_reconfigure_starts_from_the_existing_entry(hass):
    """Reconfigure opens the same first screen, bound to the existing entry."""
    entry = _existing_entry(hass)

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_only_one_entry_exists_after_reconfigure_flow_starts(hass):
    """Reconfigure must not add a second entry for the same device.

    Guards the specific regression behind #33/#35/#37: two entries sharing a
    unique ID, which re-registers every entity under a new config entry ID.
    """
    entry = _existing_entry(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    await entry.start_reconfigure_flow(hass)

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.config_entries.async_entries(DOMAIN)[0].entry_id == entry.entry_id
