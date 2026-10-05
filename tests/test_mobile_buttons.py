"""Mobile discovery, stateless entities and exact trigger write requests."""
from copy import deepcopy
from dataclasses import replace
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import aiohttp
import pytest
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.siemens_ozw672.api import (
    SiemensOzw672ApiClient, SiemensOzw672ApiError, SiemensOzw672ConnectionError,
)
from custom_components.siemens_ozw672.button import SiemensOzw672TriggerButton
from custom_components.siemens_ozw672.const import DOMAIN
from custom_components.siemens_ozw672.mobile import async_discover_mobile_triggers
from .test_setup import _entry, POLLED

SUCCESS = {"Result": {"Success": "true"}}
PUSH_TV = {
    "Id": "mobile-widget-runtime",
    "WidgetId": "3212659",
    "Area": "2",
    "Type": "1",
    "Text": {"Long": "Push TV", "CatId": "2", "GroupId": "2", "Id": "800"},
    "Datapoint": {"Id": "9721"},
    "PressedValue": "1",
}
DESCRIPTION = {
    "Type": "Enumeration", "Name": "Push TV",
    "Enums": [{"Text": ". . .", "Value": "0"}, {"Text": "Dobíjení", "Value": "1"}],
}


def client_with_response(response):
    """Use the real wrapper with a mocked HTTP session, not a real device."""
    session = SimpleNamespace(get=AsyncMock(return_value=SimpleNamespace(
        json=AsyncMock(return_value=response)
    )))
    client = SiemensOzw672ApiClient("192.0.2.10", "http", "user-secret", "pwd-secret", session, 1, 3)
    client._sessionid = "session-secret"
    return client, session


async def test_mobile_root_request():
    client, session = client_with_response({"TreeItem": {"Id": "922"}, **SUCCESS})
    assert await client.async_get_mobile_root("controller-serial") == "922"
    url = session.get.call_args.args[0]
    assert urlsplit(url).path == "/api/menutree/device_root.json"
    assert parse_qs(urlsplit(url).query) == {
        "SessionId": ["session-secret"], "SerialNumber": ["controller-serial"],
        "TreeName": ["Mobile"],
    }


@pytest.mark.parametrize("response", [
    {"Result": {"Success": "false", "Error": {"Nr": "9"}}},
    {**SUCCESS}, {"TreeItem": {}, **SUCCESS}, {"TreeItem": {"Id": {}}, **SUCCESS},
])
async def test_missing_mobile_root(response):
    client, _ = client_with_response(response)
    assert await client.async_get_mobile_root("serial") is None


async def test_direct_description_request():
    client, session = client_with_response({"Description": DESCRIPTION, **SUCCESS})
    assert await client.async_get_datapoint_description("9721") == DESCRIPTION
    url = session.get.call_args.args[0]
    assert urlsplit(url).path == "/api/menutree/datapoint_desc.json"
    assert parse_qs(urlsplit(url).query)["Id"] == ["9721"]


@pytest.mark.parametrize("response", [
    {"Result": {"Success": "false", "Error": {"Nr": "9"}}},
    {"Description": None, **SUCCESS}, {"Description": [], **SUCCESS},
])
async def test_bad_description_response_is_reported(response):
    client, _ = client_with_response(response)
    with pytest.raises(SiemensOzw672ApiError):
        await client.async_get_datapoint_description("9721")


def discovery_client(widgets=None):
    """Create a controllable recursive menu fixture."""
    return SimpleNamespace(
        async_get_mobile_root=AsyncMock(return_value="root"),
        async_get_menutree=AsyncMock(return_value={"WidgetItems": [PUSH_TV] if widgets is None else widgets}),
        async_get_datapoint_description=AsyncMock(return_value=DESCRIPTION),
    )


async def test_recursive_discovery_metadata_cycles_and_duplicates():
    client = discovery_client()
    trees = {
        "root": {"MenuItems": [{"Id": "child"}, None, {"Id": []}]},
        "child": {"MenuItems": [{"Id": "deep"}, {"Id": "root"}]},
        "deep": {"WidgetItems": [PUSH_TV, PUSH_TV]},
    }
    client.async_get_menutree.side_effect = lambda menu_id: trees[menu_id]
    triggers = await async_discover_mobile_triggers(client, "serial")
    client.async_get_mobile_root.assert_awaited_once_with("serial")
    assert [call.args[0] for call in client.async_get_menutree.await_args_list] == ["root", "child", "deep"]
    client.async_get_datapoint_description.assert_awaited_once_with("9721")
    assert len(triggers) == 1
    trigger = triggers[0]
    assert trigger.widget_id == "mobile-widget-runtime"
    assert trigger.stable_widget_id == trigger.identifier == "3212659"
    assert trigger.name == "Push TV"
    assert trigger.datapoint_id == "9721"
    assert trigger.datapoint_type == "Enumeration"
    assert trigger.pressed_value == "1"


@pytest.mark.parametrize("change", [
    {"Area": "1"}, {"Type": "0"}, {"Type": "2"}, {"Type": "3"}, {"Type": "4"},
    {"Datapoint": None}, {"Datapoint": {}}, {"Datapoint": {"Id": []}},
    {"PressedValue": None}, {"PressedValue": {}}, {"PressedValue": ""},
    {"Text": None}, {"Text": {"Long": ""}}, {"Text": {"Long": 3}},
    {"WidgetId": None, "Text": {"Long": "Push TV"}},
])
async def test_invalid_or_non_trigger_widget_is_ignored(change):
    bad = {**deepcopy(PUSH_TV), **change}
    client = discovery_client([None, [], bad, PUSH_TV])
    assert len(await async_discover_mobile_triggers(client, "serial")) == 1
    client.async_get_datapoint_description.assert_awaited_once_with("9721")


async def test_generic_name_numeric_values_and_stable_text_fallback():
    widget = {**PUSH_TV, "Area": 2, "Type": 1, "WidgetId": None, "PressedValue": 0,
              "Text": {**PUSH_TV["Text"], "Long": "Other action"}}
    trigger, = await async_discover_mobile_triggers(discovery_client([widget]), "serial")
    assert trigger.name == "Other action"
    assert trigger.pressed_value == "0"
    assert trigger.identifier == "text_2_2_800"


@pytest.mark.parametrize("tree", [{}, {"WidgetItems": None}, {"WidgetItems": {}}, None])
async def test_empty_or_malformed_tree(tree):
    client = discovery_client()
    client.async_get_menutree.return_value = tree
    assert await async_discover_mobile_triggers(client, "serial") == []


@pytest.mark.parametrize("root", [None, SiemensOzw672ConnectionError("offline")])
async def test_unavailable_mobile_tree(root):
    client = discovery_client()
    if isinstance(root, Exception):
        client.async_get_mobile_root.side_effect = root
    else:
        client.async_get_mobile_root.return_value = root
    assert await async_discover_mobile_triggers(client, "serial") == []
    client.async_get_menutree.assert_not_awaited()


async def test_missing_controller_serial_skips_discovery():
    client = discovery_client()
    assert await async_discover_mobile_triggers(client, None) == []
    client.async_get_mobile_root.assert_not_awaited()


@pytest.mark.parametrize("bad_description", [None, {}, {"Type": "Scheduler"},
    {"Type": []}, SiemensOzw672ApiError("failed")])
async def test_bad_description_does_not_block_good_widget(bad_description):
    client = discovery_client([{**PUSH_TV, "WidgetId": "bad", "Datapoint": {"Id": "bad"}}, PUSH_TV])
    client.async_get_datapoint_description.side_effect = [bad_description, DESCRIPTION]
    triggers = await async_discover_mobile_triggers(client, "serial")
    assert [trigger.identifier for trigger in triggers] == ["3212659"]


async def test_bad_branch_does_not_block_sibling():
    client = discovery_client()
    client.async_get_menutree.side_effect = [
        {"MenuItems": [{"Id": "good"}, {"Id": "bad"}]},
        SiemensOzw672ApiError("bad branch"), {"WidgetItems": [PUSH_TV]},
    ]
    assert len(await async_discover_mobile_triggers(client, "serial")) == 1


@pytest.mark.parametrize("dp_type", ["Enumeration", "RadioButton", "Numeric"])
async def test_supported_description_types(dp_type):
    client = discovery_client()
    client.async_get_datapoint_description.return_value = {"Type": dp_type}
    trigger, = await async_discover_mobile_triggers(client, "serial")
    assert trigger.datapoint_type == dp_type


async def test_button_identity_device_and_one_stateless_press():
    trigger, = await async_discover_mobile_triggers(discovery_client(), "serial")
    coordinator = MagicMock()
    coordinator.api.async_write_datapoint = AsyncMock(return_value=SUCCESS)
    coordinator.async_request_refresh = AsyncMock()
    entry = _entry()
    button = SiemensOzw672TriggerButton(coordinator, entry, trigger)
    assert isinstance(button, ButtonEntity)
    assert button.name == "Push TV"
    assert button.unique_id == "test_setup_entry_mobile_trigger_3212659"
    assert button.device_info["identifiers"] == {(DOMAIN, entry.entry_id)}
    assert button.device_info["name"] == entry.data["devicename"]
    assert button.device_info["manufacturer"] == "Siemens"
    renamed_runtime = replace(trigger, widget_id="new-runtime-widget", datapoint_id="12345")
    assert SiemensOzw672TriggerButton(coordinator, entry, renamed_runtime).unique_id == button.unique_id
    assert not hasattr(button, "is_on")
    assert button.state is None
    await button.async_press()
    coordinator.api.async_write_datapoint.assert_awaited_once_with("9721", "Enumeration", "1")
    coordinator.async_request_refresh.assert_not_awaited()
    assert not hasattr(button, "is_on")
    assert button.state is None


async def test_button_write_failure_is_reported():
    trigger, = await async_discover_mobile_triggers(discovery_client(), "serial")
    coordinator = MagicMock()
    coordinator.api.async_write_datapoint = AsyncMock(side_effect=SiemensOzw672ApiError("failed"))
    button = SiemensOzw672TriggerButton(coordinator, _entry(), trigger)
    with pytest.raises(HomeAssistantError, match="trigger write failed"):
        await button.async_press()
    coordinator.api.async_write_datapoint.assert_awaited_once()


@pytest.mark.parametrize("dp_type", ["Enumeration", "RadioButton", "Numeric"])
async def test_exact_write_request(dp_type):
    client, session = client_with_response(SUCCESS)
    assert await client.async_write_datapoint("9721", dp_type, "1") == SUCCESS
    session.get.assert_awaited_once()
    url = session.get.call_args.args[0]
    assert urlsplit(url).path == "/api/menutree/write_datapoint.json"
    expected = {"SessionId": ["session-secret"], "Id": ["9721"], "Type": [dp_type], "Value": ["1"]}
    if dp_type == "Numeric":
        expected["IsValid"] = ["true"]
    assert parse_qs(urlsplit(url).query) == expected


async def test_write_values_are_url_encoded():
    client, session = client_with_response(SUCCESS)
    await client.async_write_datapoint("123", "Enumeration", "a&b + c")
    assert parse_qs(urlsplit(session.get.call_args.args[0]).query)["Value"] == ["a&b + c"]


@pytest.mark.parametrize("dp_type", ["Enumeration", "Numeric"])
async def test_existing_datapoint_write_keeps_behavior(dp_type):
    client, session = client_with_response(SUCCESS)
    assert await client.async_write_data({"Id": "1438", "DPDescr": {"Type": dp_type}}, "1") == SUCCESS
    query = parse_qs(urlsplit(session.get.call_args.args[0]).query)
    assert query["Id"] == ["1438"]
    assert query["Type"] == [dp_type]
    assert query["Value"] == ["1"]
    assert ("IsValid" in query) == (dp_type == "Numeric")


@pytest.mark.parametrize("failure", [
    TimeoutError(), aiohttp.ClientError("session-secret"),
    {"Result": {"Success": "false", "Error": {"Nr": "1"}}},
    {"Result": {"Success": "false", "Error": {"Nr": "2"}}},
    {"Result": {"Success": "false", "Error": {"Nr": "9"}}}, {}, None,
])
async def test_failed_write_is_never_replayed(failure, caplog):
    client, session = client_with_response(failure)
    if isinstance(failure, Exception):
        session.get.side_effect = failure
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(SiemensOzw672ApiError):
            await client.async_write_datapoint("9721", "Enumeration", "1")
    session.get.assert_awaited_once()
    assert "session-secret" not in caplog.text
    assert "pwd-secret" not in caplog.text
    assert "user-secret" not in caplog.text


async def test_normal_reads_still_retry():
    client, session = client_with_response(SUCCESS)
    good_response = session.get.return_value
    session.get.side_effect = [TimeoutError(), good_response]
    assert await client.api_wrapper("get", client._menutree_url("list", Id="root")) == SUCCESS
    assert session.get.await_count == 2


async def test_authentication_does_not_log_session_or_credentials(caplog):
    client, _ = client_with_response({"SessionId": "session-secret", **SUCCESS})
    with caplog.at_level(logging.DEBUG):
        assert await client.async_get_sessionid()
    assert "session-secret" not in caplog.text
    assert "pwd-secret" not in caplog.text
    assert "user-secret" not in caplog.text


async def test_full_setup_button_service_and_shared_device(hass):
    """Exercise real discovery, platform forwarding, registry and button service."""
    entry = _entry()
    entry.add_to_hass(hass)
    write = AsyncMock(return_value=SUCCESS)
    with (
        patch("custom_components.siemens_ozw672.async_discover_mobile_triggers", new=async_discover_mobile_triggers),
        patch.object(SiemensOzw672ApiClient, "async_get_data", new=AsyncMock(return_value=POLLED)),
        patch.object(SiemensOzw672ApiClient, "async_get_mobile_root", new=AsyncMock(return_value="root")) as root,
        patch.object(SiemensOzw672ApiClient, "async_get_menutree", new=AsyncMock(return_value={"WidgetItems": [None, PUSH_TV]})) as tree,
        patch.object(SiemensOzw672ApiClient, "async_get_datapoint_description", new=AsyncMock(return_value=DESCRIPTION)),
        patch.object(SiemensOzw672ApiClient, "async_write_datapoint", new=write),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        root.assert_awaited_once_with("008600004EBF")
        buttons = hass.states.async_all("button")
        assert len(buttons) == 1
        button = buttons[0]
        assert button.state == "unknown"
        assert "Push TV" in button.attributes["friendly_name"]
        registry = er.async_get(hass)
        button_entry = registry.async_get(button.entity_id)
        sensor = registry.async_get(hass.states.async_all("sensor")[0].entity_id)
        assert button_entry.unique_id == "test_setup_entry_mobile_trigger_3212659"
        assert button_entry.device_id == sensor.device_id
        assert dr.async_get(hass).async_get(button_entry.device_id).manufacturer == "Siemens"
        await hass.services.async_call("button", "press", {"entity_id": button.entity_id}, blocking=True)
        write.assert_awaited_once_with("9721", "Enumeration", "1")
        assert hass.states.get(button.entity_id).state not in {"on", "off", "unknown"}
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(button.entity_id).state == "unavailable"
        tree.return_value = {"WidgetItems": [{**PUSH_TV, "Id": "new-widget-runtime", "Datapoint": {"Id": "12345"}}]}
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(hass.states.async_all("button")) == 1
        assert registry.async_get(button.entity_id).id == button_entry.id
        assert registry.async_get(button.entity_id).unique_id == button_entry.unique_id
        await hass.services.async_call("button", "press", {"entity_id": button.entity_id}, blocking=True)
        assert write.await_args.args == ("12345", "Enumeration", "1")
        assert write.await_count == 2
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
