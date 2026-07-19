"""Fixtures for testing siemens_ozw672."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in every test.

    Without this Home Assistant refuses to load anything from custom_components/,
    so async_setup_entry never runs.
    """
    yield
