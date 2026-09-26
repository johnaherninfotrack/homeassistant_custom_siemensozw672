"""Tests for the '----' (no reading) sentinel.

api.async_get_data used to rewrite '----' to '0', so a datapoint with no reading
was recorded as a real zero. The value must now reach the entities untouched,
and number entities must turn it into "unknown" rather than raising in float().
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.siemens_ozw672.api import SiemensOzw672ApiClient
from custom_components.siemens_ozw672 import number as number_platform


def _client():
    return SiemensOzw672ApiClient("192.0.2.10", "https", "u", "p", MagicMock(), 30, 1)


async def test_api_does_not_rewrite_no_reading_to_zero():
    """'----' is passed through as-is, not coerced to '0'."""
    client = _client()
    reading = {
        "Data": {"Type": "Numeric", "Value": "----", "Unit": "°C"},
        "Result": {"Success": "true"},
    }
    with patch.object(client, "api_wrapper", new=AsyncMock(return_value=reading)):
        result = await client.async_get_data([{"Id": "1960"}])

    assert result["1960"]["Data"]["Value"] == "----"


def _control(cls, value):
    config = {"Id": "1960", "DPDescr": {"DecimalDigits": "1"}}
    coordinator = MagicMock()
    coordinator.data = {"1960": {"Data": {"Value": value, "Unit": "°C"}}}
    return cls(coordinator, config)


@pytest.mark.parametrize(
    "cls",
    [
        number_platform.SiemensOzw672TempControl,
        number_platform.SiemensOzw672PercentControl,
        number_platform.SiemensOzw672EnergyControl,
        number_platform.SiemensOzw672NumberControl,
    ],
)
@pytest.mark.parametrize("raw", ["----", "---", "", "   "])
def test_number_entities_are_unknown_without_a_reading(cls, raw):
    """No reading means None (unknown), not 0 and not a ValueError."""
    entity = _control(cls, raw)
    assert entity.native_value is None
    assert entity.state is None


@pytest.mark.parametrize(
    "cls",
    [
        number_platform.SiemensOzw672TempControl,
        number_platform.SiemensOzw672PercentControl,
        number_platform.SiemensOzw672EnergyControl,
        number_platform.SiemensOzw672NumberControl,
    ],
)
def test_number_entities_still_parse_padded_readings(cls):
    """A real, left-padded reading keeps its full precision."""
    entity = _control(cls, "       19.8")
    assert entity.native_value == pytest.approx(19.8)
    assert entity.state == pytest.approx(19.8)
