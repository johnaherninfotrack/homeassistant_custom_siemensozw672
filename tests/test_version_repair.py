"""Tests for the issue #39 string-version repair.

Releases 0.3.6/0.3.7 briefly shipped CONF_VERSION/CONF_MINOR_VERSION as strings, so
config entries created in that window are persisted with string versions. Home
Assistant's ConfigEntry.async_migrate() evaluates `self.version > handler.VERSION`
before async_migrate_entry() is ever called, which raises

    TypeError: '>' not supported between instances of 'str' and 'int'

leaving affected users unable to load the integration at all.
"""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_ozw672 import _async_repair_string_entry_versions
from custom_components.siemens_ozw672.const import DOMAIN


def _entry_with_versions(hass, version, minor_version):
    """Add an entry to hass, forcing version/minor_version to raw values.

    MockConfigEntry coerces its arguments, so the corrupted string state is written
    directly onto the entry the way the old code persisted it to .storage.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_entry")
    entry.add_to_hass(hass)
    object.__setattr__(entry, "version", version)
    object.__setattr__(entry, "minor_version", minor_version)
    return entry


async def test_string_versions_are_repaired(hass):
    """String versions are coerced back to int."""
    entry = _entry_with_versions(hass, "1", "5")

    _async_repair_string_entry_versions(hass)

    assert entry.version == 1
    assert entry.minor_version == 5
    assert isinstance(entry.version, int)
    assert isinstance(entry.minor_version, int)


async def test_repair_prevents_the_reported_typeerror(hass):
    """After repair, HA's own version comparison no longer raises.

    This is the exact expression from config_entries.async_migrate() that produced the
    traceback in issue #39.
    """
    entry = _entry_with_versions(hass, "1", "5")

    # Reproduce the reported crash first, so this test fails loudly if the scenario
    # it is guarding against ever stops being reachable.
    with pytest.raises(TypeError):
        entry.version > 1

    _async_repair_string_entry_versions(hass)

    # The same expression must now evaluate cleanly.
    assert (entry.version > 1) is False


async def test_already_int_entries_are_untouched(hass):
    """Healthy entries are left alone, so the repair is safe to run every startup."""
    entry = _entry_with_versions(hass, 1, 5)

    _async_repair_string_entry_versions(hass)

    assert entry.version == 1
    assert entry.minor_version == 5


async def test_repair_is_idempotent(hass):
    """Running twice is a no-op the second time."""
    entry = _entry_with_versions(hass, "1", "5")

    _async_repair_string_entry_versions(hass)
    _async_repair_string_entry_versions(hass)

    assert entry.version == 1
    assert entry.minor_version == 5


async def test_unparseable_version_does_not_raise(hass, caplog):
    """A version we cannot parse is logged rather than crashing setup."""
    entry = _entry_with_versions(hass, "not-a-number", "5")

    _async_repair_string_entry_versions(hass)

    assert entry.version == "not-a-number"
    assert "cannot be repaired automatically" in caplog.text
