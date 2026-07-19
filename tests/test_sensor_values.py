"""Tests for OZW672 sensor value parsing.

The previous implementation guarded on `str.isnumeric()`, which is False for
"19.8" (the decimal point disqualifies it) and for "-3". Decimal readings
therefore fell through to `int(float(...))` and were truncated, so 0.7 bar
displayed as 0.0 (#32). The same expression subscripted DPDescr["DecimalDigits"]
directly, raising KeyError for datapoints that do not report it (#23, #30).
"""
import pytest

from custom_components.siemens_ozw672.sensor import decimal_digits, parse_numeric


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The device left-pads its readings.
        ("       19.8", 19.8),
        ("        54", 54.0),
        # #32: water pressure of 0.7 bar used to read as 0.
        ("0.7", 0.7),
        ("       0.7", 0.7),
        # Decimals below 1 are the worst case: int(float("0.7")) == 0.
        ("0.4", 0.4),
        ("0.9", 0.9),
        # Negatives: "-3".isnumeric() is False, so these truncated toward zero.
        ("-3.5", -3.5),
        ("-3", -3.0),
        ("-0.5", -0.5),
        # Whole numbers still work.
        ("42", 42.0),
        ("0", 0.0),
    ],
)
def test_numeric_values_are_parsed_exactly(raw, expected):
    """Readings are returned at full precision, never truncated."""
    assert parse_numeric(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw", ["---", "----", "-----", "", "   ", None])
def test_no_data_sentinel_becomes_none(raw):
    """A run of dashes means 'no reading' and must not become a number.

    Coercing it to 0 would record a fabricated measurement into long-term
    statistics, which is worse than the entity being unknown.
    """
    assert parse_numeric(raw) is None


@pytest.mark.parametrize("raw", ["Boost heating", "On", "abc", "1.2.3"])
def test_non_numeric_text_becomes_none(raw):
    """Text that is not a number yields None rather than raising."""
    assert parse_numeric(raw) is None


def test_truncation_regression():
    """Guard the specific behaviour that caused #32.

    Fails loudly if anyone reintroduces an isnumeric()-style guard.
    """
    for raw in ("0.7", "15.8", "-3.5"):
        assert parse_numeric(raw) != int(float(raw))


@pytest.mark.parametrize(
    ("descr", "expected"),
    [
        ({"DecimalDigits": "1"}, 1),
        ({"DecimalDigits": "0"}, 0),
        ({"DecimalDigits": 2}, 2),
        # #23/#30: not every datapoint reports DecimalDigits. Subscripting it
        # directly raised KeyError inside the state machinery, which silently
        # froze the affected entities.
        ({}, None),
        ({"DecimalDigits": None}, None),
        ({"DecimalDigits": "not-a-number"}, None),
    ],
)
def test_decimal_digits_never_raises(descr, expected):
    """Missing or unparseable precision yields None instead of raising."""
    assert decimal_digits({"DPDescr": descr}) is expected


@pytest.mark.parametrize("config", [{}, {"DPDescr": None}])
def test_decimal_digits_tolerates_missing_description(config):
    """A datapoint with no description at all must not raise either."""
    assert decimal_digits(config) is None
