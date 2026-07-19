"""Base entity for Siemens OZW672."""
import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_PREFIX_FUNCTION,
    CONF_PREFIX_OPLINE,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def build_datapoint_configs(entry, coordinator, hatype):
    """Return the entity configs this platform should create.

    Every platform used to carry its own copy of this loop - five near-identical
    blocks differing only in the HAType string. That duplication is why fixes
    landed in one file and missed the other four: the NameError in
    binary_sensor.py and the truncation bug in sensor.py were both single-file
    copies of a shared mistake.

    Yields a dict per matching datapoint, annotated with the identity and naming
    fields the entity classes expect.
    """
    configs = []
    stored = entry.data.get("datapoints") or []
    prefix_function = entry.data.get(CONF_PREFIX_FUNCTION, False)
    prefix_opline = entry.data.get(CONF_PREFIX_OPLINE, False)

    for item in coordinator.data or {}:
        dp_config = next(
            (dp for dp in stored if dp.get("Id") == item),
            None,
        )
        # A polled datapoint with no stored config is skipped. Previously the
        # loop variable simply kept its previous value, so an unmatched item
        # silently produced a duplicate of the entity before it.
        if dp_config is None:
            _LOGGER.debug("No stored config for polled datapoint %s; skipping", item)
            continue
        if (dp_config.get("DPDescr") or {}).get("HAType") != hatype:
            continue

        # Prefer the Operating Line from the manual as the identifier: unlike the
        # API's datapoint Id it survives the OZW menu tree being regenerated.
        opline = str(dp_config.get("OpLine", "") or "")
        identifier = opline if opline.isdigit() and int(opline) > 1 else f"00{item}"

        prefix = ""
        if prefix_function:
            prefix = f'{dp_config.get("MenuItem", "")} - '
        if prefix_opline:
            prefix = f"{prefix}{opline} "

        dp_config.update(
            {
                "entry_id": f"{entry.entry_id}_{identifier}",
                "device_id": entry.entry_id,
                "device_name": entry.data["devicename"],
                "entity_prefix": prefix,
            }
        )
        configs.append(dp_config)

    return configs


class SiemensOzw672Entity(CoordinatorEntity):
    """Common behaviour for every entity this integration creates."""

    # Home Assistant composes the displayed name as "<device> <entity>", so the
    # name property below carries only the datapoint part. Without this, every
    # entity had to repeat the device name itself.
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity.

        Deliberately unchanged in 0.4.0. The churn reported in #33/#35/#37 comes
        from a second config entry being created when datapoints are added, not
        from the format itself - so the reconfigure flow fixes the cause without
        rewriting anyone's registry entries and losing their history.
        """
        return self.config_entry["entry_id"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for the monitored device.

        Previously reported the integration's own version as the hardware model
        and "Siemens OZW672" as the manufacturer, so every device page showed
        model "0.3.7" made by "Siemens OZW672".
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry["device_id"])},
            name=self.config_entry["device_name"],
            manufacturer=MANUFACTURER,
            model=self.config_entry.get("device_model")
            or self.config_entry["device_name"],
        )
