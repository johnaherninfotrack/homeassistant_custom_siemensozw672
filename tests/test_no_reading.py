"""Tests for datapoints that report no reading ('----').

async_get_data used to rewrite '----' to '0', which turned "no reading" into a
fabricated zero (undoing the unknown-when-no-reading behaviour of parse_numeric).
The number entities also called float() directly, which would raise on '----'
once the rewrite was removed.
"""
import asyncio
from types import SimpleNamespace

import pytest

from custom_components.siemens_ozw672.api import SiemensOzw672ApiClient
from custom_components.siemens_ozw672.number import (
    SiemensOzw672EnergyControl,
    SiemensOzw672NumberControl,
    SiemensOzw672PercentControl,
    SiemensOzw672TempControl,
)


def _response(value):
    return {
        "Data": {"Type": "Numeric", "Value": value, "Unit": "°C"},
        "Result": {"Success": "true"},
    }


def _client(monkeypatch, value):
    client = SiemensOzw672ApiClient("ozw.local", "https", "user", "pw", None, 10, 1)

    async def fake_wrapper(method, url, *args, **kwargs):
        return _response(value)

    monkeypatch.setattr(client, "api_wrapper", fake_wrapper)
    return client


@pytest.mark.parametrize("value", ["----", "       19.8", "0"])
def test_get_data_returns_value_unchanged(monkeypatch, value):
    """The raw device value is passed through, including the no-reading marker."""
    client = _client(monkeypatch, value)
    result = asyncio.run(client.async_get_data([{"Id": "1438"}]))
    assert result["1438"]["Data"]["Value"] == value


@pytest.mark.parametrize(
    "entity_class",
    [
        SiemensOzw672TempControl,
        SiemensOzw672PercentControl,
        SiemensOzw672EnergyControl,
        SiemensOzw672NumberControl,
    ],
)
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("----", None), ("       19.8", 19.8), ("0", 0.0), ("-3.5", -3.5)],
)
def test_number_entities_handle_no_reading(entity_class, raw, expected):
    """No reading is unknown (None); real readings, including 0, are kept."""
    coordinator = SimpleNamespace(data={"1438": {"Data": {"Value": raw, "Unit": "°C"}}})
    entity = entity_class(coordinator, {"Id": "1438"})
    if expected is None:
        assert entity.native_value is None
        assert entity.state is None
    else:
        assert entity.native_value == pytest.approx(expected)
        assert entity.state == pytest.approx(expected)
