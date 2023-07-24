"""Adds config flow for Siemens OZW672."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers import selector

from .api import SiemensOzw672ApiClient
from .const import CONF_HOST
from .const import CONF_DEVICE
from .const import CONF_DEVICE_ID
from .const import CONF_PROTOCOL
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import CONF_MENUITEMS
from .const import CONF_DATAPOINTS
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE
from .const import CONF_SCANINTERVAL
from .const import DOMAIN
from .const import PLATFORMS

import json

PROTOCOL_OPTIONS = [
    selector.SelectOptionDict(value="http", label="HTTP"),
    selector.SelectOptionDict(value="https", label="HTTPS")
]

import logging
_LOGGER: logging.Logger = logging.getLogger(__package__)

class SiemensOzw672FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for siemens_ozw672."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._session = None
        self._client = None
        self._discovereddevices = None
        self._devicemenuitems = None
        self._sysinfo = None
        self._datapoints = []
        self._datapoints_descr = []
        self._deviceid = None
        self._data = None
        self._lastitemname = ""
        self._devserialnumber = ""
        self.alldevices = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        """ First Screen - Protocol, Hostname/IP, Username, Password, and some options"""
        self._errors = {}
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_HOST], user_input[CONF_PROTOCOL], user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                # Get the list of devices:
                self._discovereddevices = await self._get_menutree("")
                # Get the device menutTrue ID
                self.alldevices=await self._get_devices()
                self._data=user_input
                return await self.async_step_device()
            else:
                self._errors["base"] = "auth"
            return await self._show_config_form(user_input)
        return await self._show_config_form(user_input)

    async def async_step_device(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            device=json.loads(user_input[CONF_DEVICE])
            ### Support a Customized name for the Device being monitored.
            self._data[CONF_DEVICE]=device["custom_name"]
            ### Each device has a MenuTree root ID
            menutreeid=device["Id"]
            ### Get the System Info as discovery used Serial Number of the OZW672 and Serial Number of the Device.
            self._sysinfo = await self._get_sysinfo()
            self._data[CONF_DEVICE_ID]=f'{self._sysinfo["SerialNr"]}:{device["Text"]["Long"]}' #Redundant code - used as a default
            for d in self.alldevices:
                d_ident = f'{d["Addr"]} {d["Type"]}'
                if d_ident == device["Text"]["Long"]:
                    self._data[CONF_DEVICE_ID]=f'{self._sysinfo["SerialNr"]}:{d["SerialNr"]}'
            self._devserialnumber = self._data[CONF_DEVICE_ID]
            ### Support updating an existing device
            existing_entry = self.async_entry_for_existingdevice(self._data[CONF_DEVICE_ID])
            if existing_entry:
                self._datapoints = existing_entry.data.get(CONF_DATAPOINTS)
            await self.async_set_unique_id(self._devserialnumber)
            ### Now get a list of Functions/MenuItems for this device to enable the user to select what to monitor.
            self._devicemenuitems = await self._get_menutree(menutreeid)
            return await self.async_step_menuitem()
        else:
            return await self._show_device_selection_form(user_input)
        return await self._show_device_selection_form(user_input)

    async def async_step_menuitem(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._data[CONF_MENUITEMS]=user_input[CONF_MENUITEMS]
            self._devicemenuitems=user_input[CONF_MENUITEMS]
            _LOGGER.debug(f"CONF_MENUITEMS: {self._data[CONF_MENUITEMS]}")
            ### Now we have selected a list of Functions/MenuItems to monitor, recursively call a function to enable the user to select entities to monitor.
            return await self.async_step_menuitemenum()
        else:
            return await self._show_menuitem_selection_form(user_input)
        return await self._show_menuitem_selection_form(user_input)
    
    async def async_step_menuitemenum(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            if CONF_DATAPOINTS in user_input:
                # Get DP Data as we need this to determine type.
                all_dpdata = await self._get_data(user_input[CONF_DATAPOINTS])
                _LOGGER.debug(f'async_step_menuitemenum **** Intial DP Data: {all_dpdata}')
                all_dpdescr = await self._get_data_descr(user_input[CONF_DATAPOINTS], all_dpdata)
                _LOGGER.debug(f'async_step_menuitemenum **** Initial DP Descriptions: {all_dpdescr}')
                for dp in user_input[CONF_DATAPOINTS]:
                    dpjson=json.loads(dp)
                    dpdescr = all_dpdescr[dpjson["Id"]]["Description"]
                    _LOGGER.debug(f'async_step_menuitemenum - "Id": {dpjson["Id"]},"WriteAccess": {dpjson["WriteAccess"]},"OpLine": {dpjson["Text"]["Id"]}, "Name": {dpjson["Text"]["Long"]},"MenuItem": {self._lastitemname}, "DPDescr": {dpdescr} ')
                    self._datapoints.append({"Id": dpjson["Id"],"WriteAccess": dpjson["WriteAccess"],"OpLine": dpjson["Text"]["Id"], "Name": dpjson["Text"]["Long"],"MenuItem": self._lastitemname, "DPDescr": dpdescr })
            self._data[CONF_DATAPOINTS]=self._datapoints
            _LOGGER.debug(f"DATAPOINTS: {self._data[CONF_DATAPOINTS]}")
            if len(self._devicemenuitems) > 0:
                return await self.async_step_menuitemenum()
            else: ### FINALLY... Create our discovered entities. ###
                return self.async_create_entry(
                    title=self._data[CONF_DEVICE], data=self._data
                )
        else:
            if len(self._devicemenuitems) > 0:
                item = self._devicemenuitems.pop(0)
                _LOGGER.debug(f"Generating Config Form for item: {item}")
                ### For each Function/MenuItem selected, list the entities available and allow the user to select what to monitor/poll
                return await self._show_menuitemenum_selection_form(item,user_input)
            else:
                # We should never be here
                return
        return await self._show_menuitemenum_selection_form(item,user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SiemensOzw672OptionsFlowHandler(config_entry)

    def async_entry_for_existingdevice(self, deviceserialnumber):
        """Find an existing entry for a serialnumber."""
        for entry in self._async_current_entries():
            if entry.data.get(CONF_DEVICE_ID) == deviceserialnumber:
                return entry
        return None

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_PROTOCOL, default="http"): selector.SelectSelector(selector.SelectSelectorConfig(options=PROTOCOL_OPTIONS)),
                vol.Required(CONF_HOST): str, 
                vol.Required(CONF_USERNAME): str, 
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SCANINTERVAL, default=60): int,
                vol.Required(CONF_PREFIX_FUNCTION, default=True): bool,
                vol.Required(CONF_PREFIX_OPLINE, default=True): bool
            }
            ),
            errors=self._errors,
        )

    async def _show_device_selection_form(self, user_input):  # pylint: disable=unused-argument
        """Show the device selection form. """
        _LOGGER.debug("Building device list")
        device_list_selector = []
        for device in self._discovereddevices:
            devchannel=str(device["Text"]["Long"]).split(' ',1)[0]
            devname=str(device["Text"]["Long"]).split(' ',1)[1]
            for dev in self.alldevices:
                if dev['Addr'] == devchannel:
                    device["custom_name"]=dev['Name']
                else:
                    device["custom_name"]=devname
            device_list_selector.append(selector.SelectOptionDict(value=json.dumps(device), label=str(device["Text"]["Long"] +" (Name:"+device["custom_name"]+")")))
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_DEVICE): selector.SelectSelector(selector.SelectSelectorConfig(options=device_list_selector))
            }
            ),
            errors=self._errors,
        )

    async def _show_menuitem_selection_form(self, user_input):  # pylint: disable=unused-argument
        """Show the menu item selection form. """
        _LOGGER.debug("Building Menu Item list")
        menuitem_list_selector = []
        for menuitem in self._devicemenuitems:
            menuitem_list_selector.append(selector.SelectOptionDict(value=json.dumps(menuitem), label=menuitem["Text"]["Long"]))
        return self.async_show_form(
            step_id="menuitem",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_MENUITEMS): selector.SelectSelector(selector.SelectSelectorConfig(options=menuitem_list_selector, multiple=True))
            }
            ),
            errors=self._errors,
        )

    async def _show_menuitemenum_selection_form(self, item, user_input):  # pylint: disable=unused-argument
        """Show the Data Point item selection form. """
        _LOGGER.debug(f"Building Data Point list for item: {item}")
        datapoint_list_selector = []
        menutree_item=json.loads(item)
        menutree_id=menutree_item["Id"]
        menutree_name=menutree_item["Text"]["Long"]
        self._lastitemname=menutree_name
        existing_dp_items = self._datapoints
        new_dp_items = await self._get_datapoints(menutree_id)

        for dp in new_dp_items:
            ### If we are already polling a variable - don't list it.
            already_exists=False
            for edp in existing_dp_items:
                if edp["Name"] == dp["Text"]["Long"]:
                    already_exists=True
                    break
            ### If this is something new to monitor - add it to our Dict.
            if not already_exists:
                datapoint_list_selector.append(selector.SelectOptionDict(value=json.dumps(dp), label=dp["Text"]["Long"]))
        if len(datapoint_list_selector) == 0:
            return self.async_show_form(
                step_id="menuitemenum",
                data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DATAPOINTS): "" 
                }
                ),
                description_placeholders={"item_name": menutree_name},
                errors=self._errors,
            )
        return self.async_show_form(
            step_id="menuitemenum",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_DATAPOINTS): selector.SelectSelector(selector.SelectSelectorConfig(options=datapoint_list_selector, multiple=True))
            }
            ),
            description_placeholders={"item_name": menutree_name},
            errors=self._errors,
        )

    async def _test_credentials(self, host, protocol, username, password):
        """Return true if credentials are valid."""
        try:
            self._session = async_create_clientsession(self.hass)
            self._client = SiemensOzw672ApiClient(host, protocol, username, password, self._session)
            if (await self._client.async_get_sessionid()):
                return True
            return False
        except Exception:  # pylint: disable=broad-except
            pass
        return False

    async def _get_sysinfo(self):
        try:
            info = await self._client.async_get_sysinfo()
        except Exception:  # pylint: disable=broad-except
            pass
        return info

    async def _get_devices(self):
        try:
            devices = await self._client.async_get_devices()
        except Exception:  # pylint: disable=broad-except
            pass
        return devices

    async def _get_menutree(self,id):
        try:
            output = await self._client.async_get_menutree(id)
        except Exception:  # pylint: disable=broad-except
            pass
        return output

    async def _get_datapoints(self,id):
        try:
            output = await self._client.async_get_datapoints(id)
        except Exception:  # pylint: disable=broad-except
            pass
        return output


    async def _get_data(self, datapoints):
        """Update data via OZW API."""
        try:
            return await self._client.async_get_data(datapoints)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug(f'Exception: {repr(err)}')
            pass
            return ''


    async def _get_data_descr(self,datapoints,all_dpdata):
        try:
            return await self._client.async_get_data_descr(datapoints, all_dpdata)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug(f'Exception: {repr(err)}')
            pass
            return ''

class SiemensOzw672OptionsFlowHandler(config_entries.OptionsFlow):
    """NOT REALLY USEFUL YET: Config flow options handler for siemens_ozw672."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_HOST), data=self.options
        )




