"""Discover stateless triggers in the selected device's Mobile tree."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from .api import SiemensOzw672ApiError

_LOGGER = logging.getLogger(__package__)
TRIGGER_TYPES = frozenset({"Enumeration", "RadioButton", "Numeric"})


def _scalar(value):
    """Normalize API strings and numbers, rejecting malformed containers."""
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return str(value) if str(value).strip() else None
    return None


@dataclass(frozen=True)
class MobileTrigger:
    """Metadata needed for one button, separate from polled datapoints."""

    widget_id: str | None
    stable_widget_id: str | None
    identifier: str
    name: str
    datapoint_id: str
    datapoint_type: str
    pressed_value: str


async def async_discover_mobile_triggers(client, serial_number):
    """Walk the Mobile tree without letting a bad branch block other entities."""
    if not serial_number:
        return []
    try:
        root_id = await client.async_get_mobile_root(serial_number)
    except (SiemensOzw672ApiError, KeyError, TypeError, ValueError):
        _LOGGER.debug("Mobile tree root unavailable")
        return []
    if not root_id:
        _LOGGER.debug("No Mobile tree for selected device")
        return []
    _LOGGER.debug("Mobile tree root obtained: %s", root_id)

    pending = [root_id]
    visited = set()
    triggers = {}
    descriptions = {}
    while pending:
        menu_id = pending.pop()
        if menu_id in visited:
            continue
        visited.add(menu_id)
        try:
            tree = await client.async_get_menutree(menu_id)
        except (SiemensOzw672ApiError, KeyError, TypeError, ValueError):
            _LOGGER.debug("Skipping unavailable Mobile branch %s", menu_id)
            continue
        if not isinstance(tree, dict):
            continue
        menus = tree.get("MenuItems")
        for menu in menus if isinstance(menus, list) else []:
            child_id = _scalar(menu.get("Id")) if isinstance(menu, dict) else None
            if child_id:
                pending.append(child_id)
        widgets = tree.get("WidgetItems")
        for widget in widgets if isinstance(widgets, list) else []:
            if not isinstance(widget, dict):
                continue
            if str(widget.get("Area")) != "2" or str(widget.get("Type")) != "1":
                continue
            datapoint = widget.get("Datapoint")
            text = widget.get("Text")
            dp_id = _scalar(datapoint.get("Id")) if isinstance(datapoint, dict) else None
            name = text.get("Long") if isinstance(text, dict) else None
            pressed = _scalar(widget.get("PressedValue"))
            if not dp_id or pressed is None or not isinstance(name, str) or not name.strip():
                _LOGGER.debug("Skipping malformed Mobile trigger")
                continue
            stable_id = _scalar(widget.get("WidgetId"))
            # Text catalog references survive runtime menu IDs and localization.
            # Without either stable identity, skip rather than create a new entity
            # every time the gateway regenerates its menu tree.
            text_ref = [_scalar(text.get(key)) for key in ("CatId", "GroupId", "Id")]
            identifier = stable_id
            if identifier is None and all(text_ref):
                identifier = "text_" + "_".join(text_ref)
            if identifier is None:
                _LOGGER.debug("Skipping Mobile trigger without stable identity: %s", name)
                continue
            if identifier in triggers:
                continue
            try:
                if dp_id not in descriptions:
                    descriptions[dp_id] = await client.async_get_datapoint_description(dp_id)
                description = descriptions[dp_id]
                dp_type = description.get("Type") if isinstance(description, dict) else None
            except (SiemensOzw672ApiError, KeyError, TypeError, ValueError):
                _LOGGER.debug("Skipping Mobile trigger with unavailable description: %s", name)
                continue
            if not isinstance(dp_type, str) or dp_type not in TRIGGER_TYPES:
                _LOGGER.debug("Skipping Mobile trigger with unsupported type: %s", name)
                continue
            triggers[identifier] = MobileTrigger(
                widget_id=_scalar(widget.get("Id")),
                stable_widget_id=stable_id,
                identifier=identifier,
                name=name,
                datapoint_id=dp_id,
                datapoint_type=dp_type,
                pressed_value=pressed,
            )
            _LOGGER.debug(
                "Mobile trigger %s / WidgetId=%s / datapoint=%s / type=%s",
                name, stable_id, dp_id, dp_type,
            )
    _LOGGER.debug("Discovered %d Mobile trigger widgets", len(triggers))
    return list(triggers.values())
