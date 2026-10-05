"""Fixtures for testing siemens_ozw672."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in every test.

    Without this Home Assistant refuses to load anything from custom_components/,
    so async_setup_entry never runs.
    """
    yield


@pytest.fixture(autouse=True)
def mock_optional_mobile_discovery():
    """Existing setup tests must not contact a gateway for optional discovery."""
    with patch(
        "custom_components.siemens_ozw672.async_discover_mobile_triggers",
        new=AsyncMock(return_value=[]),
    ):
        yield
