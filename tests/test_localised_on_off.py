"""Tests for on/off state on devices with a non-English display language.

switch.py and binary_sensor.py compared the polled value to the literal 'On', so
a device reporting e.g. 'Zapnuto' always showed as off. The 'on' text is now taken
from the datapoint description's RadioButton TextOpt1, falling back to 'On'.
"""
from unittest.mock import MagicMock

import pytest

from custom_components.siemens_ozw672.binary_sensor import SiemensOzw672BinarySensor
from custom_components.siemens_ozw672.entity import is_on_value
from custom_components.siemens_ozw672.switch import SiemensOzw672BinarySwitch

CZECH = {"Type": "RadioButton", "Buttons": [{"TextOpt0": "Vypnuto", "TextOpt1": "Zapnuto"}]}
ENGLISH = {"Type": "RadioButton", "Buttons": [{"TextOpt0": "Off", "TextOpt1": "On"}]}


@pytest.mark.parametrize(
    "value, descr, expected",
    [
        ("Zapnuto", CZECH, True),
        ("Vypnuto", CZECH, False),
        (" Zapnuto ", CZECH, True),
        ("On", ENGLISH, True),
        ("Off", ENGLISH, False),
        (" On", ENGLISH, True),
        ("On", None, True),
        ("Off", None, False),
        ("On", {}, True),
        ("On", {"Type": "Enumeration"}, True),
        ("---", ENGLISH, False),
        ("", CZECH, False),
        (None, CZECH, False),
    ],
)
def test_is_on_value(value, descr, expected):
    assert is_on_value(value, descr) is expected


@pytest.mark.parametrize("cls", [SiemensOzw672BinarySwitch, SiemensOzw672BinarySensor])
@pytest.mark.parametrize(
    "value, expected", [("Zapnuto", True), ("Vypnuto", False)]
)
def test_entities_use_the_localised_label(cls, value, expected):
    coordinator = MagicMock()
    coordinator.data = {"4102": {"Data": {"Value": value}}}
    entity = cls(coordinator, {"Id": "4102", "DPDescr": CZECH})
    assert entity.is_on is expected


@pytest.mark.parametrize("cls", [SiemensOzw672BinarySwitch, SiemensOzw672BinarySensor])
def test_english_device_is_unchanged(cls):
    coordinator = MagicMock()
    coordinator.data = {"1966": {"Data": {"Value": "On"}}}
    entity = cls(coordinator, {"Id": "1966", "DPDescr": ENGLISH})
    assert entity.is_on is True
    coordinator.data = {"1966": {"Data": {"Value": "Off"}}}
    assert entity.is_on is False
