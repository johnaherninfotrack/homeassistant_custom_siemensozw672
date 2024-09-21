"""Adds config flow for Siemens OZW672."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers import selector
from datetime import timedelta

from .api import SiemensOzw672ApiClient
from .const import CONF_HOST
from .const import CONF_DEVICE
from .const import CONF_DEVICE_LONGNAME
from .const import CONF_DEVICE_ID
from .const import CONF_PROTOCOL
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import CONF_MENUITEMS
from .const import CONF_DATAPOINTS
from .const import CONF_PREFIX_FUNCTION
from .const import CONF_PREFIX_OPLINE
from .const import CONF_SCANINTERVAL
from .const import CONF_HTTPTIMEOUT
from .const import CONF_HTTPRETRIES
from .const import DOMAIN
from .const import PLATFORMS
from .const import DEFAULT_HTTPTIMEOUT
from .const import DEFAULT_HTTPRETRIES
from .const import DEFAULT_SCANINTERVAL
from .const import DEFAULT_PREFIX_FUNCTION
from .const import DEFAULT_PREFIX_OPLINE
from .const import DEFAULT_USE_DEVICE_LONGNAME
from .const import CONF_USE_DEVICE_LONGNAME

import json

PROTOCOL_OPTIONS = [
    selector.SelectOptionDict(value="http", label="HTTP"),
    selector.SelectOptionDict(value="https", label="HTTPS")
]

DEFAULT_OPTIONS = {'httptimeout': DEFAULT_HTTPTIMEOUT, 
    'httpretries': DEFAULT_HTTPRETRIES, 
    'scaninterval': DEFAULT_SCANINTERVAL, 
    CONF_PREFIX_FUNCTION: DEFAULT_PREFIX_FUNCTION, 
    CONF_PREFIX_OPLINE: DEFAULT_PREFIX_OPLINE, 
    CONF_USE_DEVICE_LONGNAME: DEFAULT_USE_DEVICE_LONGNAME, 
    'switch': True, 'select': True, 'number': True, 'binary_sensor': True, 'sensor': True
}

import logging
_LOGGER: logging.Logger = logging.getLogger(__package__)

class SiemensOzw672FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for siemens_ozw672."""

    VERSION = 1
    MINOR_VERSION = 3
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._session = None
        self._client = None
        self._discovereddevices = dict()
        self._devicemenuitems = None
        self._sysinfo = None
        self._datapoints = []
        self._datapoints_descr = []
        self._deviceid = None
        self._data = None
        self._devserialnumber = ""
        self.alldevices = None
        self._options = dict(DEFAULT_OPTIONS)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        """ First Screen - Protocol, Hostname/IP, Username, Password, and some options"""
        self._errors = {}
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_HOST], user_input[CONF_PROTOCOL], user_input[CONF_USERNAME], user_input[CONF_PASSWORD], DEFAULT_HTTPTIMEOUT, DEFAULT_HTTPRETRIES
            )
            if valid:
                # Get the list of devices:
                self._discovereddevices = (await self._get_menutree(""))["MenuItems"]
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
            self._data[CONF_DEVICE]=device["Name"]
            self._data[CONF_DEVICE_LONGNAME]=device["LongName"]
            self._options[CONF_PREFIX_FUNCTION]=user_input[CONF_PREFIX_FUNCTION]
            self._options[CONF_PREFIX_OPLINE]=user_input[CONF_PREFIX_OPLINE]
            self._options[CONF_USE_DEVICE_LONGNAME]=user_input[CONF_USE_DEVICE_LONGNAME]
            self._data[CONF_PREFIX_FUNCTION]=user_input[CONF_PREFIX_FUNCTION]
            self._data[CONF_PREFIX_OPLINE]=user_input[CONF_PREFIX_OPLINE]
            self._data[CONF_USE_DEVICE_LONGNAME]=user_input[CONF_USE_DEVICE_LONGNAME]
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
                self._options = dict(existing_entry.options)
                self._datapoints = existing_entry.data.get(CONF_DATAPOINTS)
                _LOGGER.debug(f'Found existing options: {self._options}')
                _LOGGER.debug(f'Found existing options: {self._datapoints}')
            await self.async_set_unique_id(self._devserialnumber)
            ### Now get a list of Functions/MenuItems (ignore datapoints at this level) for this device to enable the user to select what to monitor.
            self._devicemenuitems = (await self._get_menutree(menutreeid))["MenuItems"]
            return await self.async_step_mainmenu()
        else:
            return await self._show_device_selection_form(user_input)
        return await self._show_device_selection_form(user_input)

    async def async_step_mainmenu(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._data[CONF_MENUITEMS]=user_input[CONF_MENUITEMS]
            self._alldevicemenuitems=user_input[CONF_MENUITEMS]
            _LOGGER.debug(f"Found: CONF_MENUITEMS: {self._data[CONF_MENUITEMS]}")
            ### Now we have selected a list of Functions/MenuItems/DataPointItmes to monitor, recursively call a function to enable the user to select entities to monitor.
            return await self.async_step_submenu()
        else:
            return await self._show_mainmenu_selection_form(user_input)
        return await self._show_mainmenu_selection_form(user_input)
    

    async def async_step_submenu(self, user_input=None):
        _LOGGER.debug(f"async_step_submenu - user_input: {user_input}")
        self._errors = {}
        if user_input is not None:
            ###### WE NEED TO PROCESS SELECTED SUBMENUS HERE
            if CONF_MENUITEMS in user_input:
                for submenu in user_input[CONF_MENUITEMS]:
                    _LOGGER.debug(f'Appending {submenu} in MenuItems to discover')
                    self._alldevicemenuitems.append(submenu)
            if CONF_DATAPOINTS in user_input:
                # Get DP Data as we need this to determine type.
                all_dpdata = await self._get_data(user_input[CONF_DATAPOINTS])
                _LOGGER.debug(f'async_step_submenu **** Intial DP Data: {all_dpdata}')
                all_dpdescr = await self._get_data_descr(user_input[CONF_DATAPOINTS], all_dpdata)
                _LOGGER.debug(f'async_step_submenu **** Initial DP Descriptions: {all_dpdescr}')
                for dp in user_input[CONF_DATAPOINTS]:
                    dpjson=json.loads(dp)
                    dpdescr = all_dpdescr[dpjson["Id"]]["Description"]
                    _LOGGER.debug(f'async_step_submenu - "Id": {dpjson["Id"]},"WriteAccess": {dpjson["WriteAccess"]},"OpLine": {dpjson["Text"]["Id"]}, "Name": {dpjson["Text"]["Long"]},"MenuItem": {dpjson["MenuItem"]}, "DPDescr": {dpdescr} ')
                    self._datapoints.append({"Id": dpjson["Id"],"WriteAccess": dpjson["WriteAccess"],"OpLine": dpjson["Text"]["Id"], "Name": dpjson["Text"]["Long"],"MenuItem": dpjson["MenuItem"], "DPDescr": dpdescr })
            self._data[CONF_DATAPOINTS]=self._datapoints
            _LOGGER.debug(f"DATAPOINTS: {self._data[CONF_DATAPOINTS]}")
            if len(self._alldevicemenuitems) > 0:
                ### Recursively traverse through all menu items.
                _LOGGER.debug("****** Recursing further through menu ******")
                return await self.async_step_submenu()
            else: ### FINALLY... Create our discovered entities. ###
                self._data["options"]=self._options
                _LOGGER.debug(f'Addind Entities now...Data: {self._data}')
                use_device_longname = self._options.get(CONF_USE_DEVICE_LONGNAME)
                if (use_device_longname == True):
                    _LOGGER.debug(f'Options: {self._options} -- Will use Device Long Name')
                    dev_title=self._data[CONF_DEVICE_LONGNAME]
                else:
                    dev_title=self._data[CONF_DEVICE]
                return self.async_create_entry(    
                    title=dev_title, data=self._data, options=self._options
                )
        else:
            if len(self._alldevicemenuitems) > 0:
                item = self._alldevicemenuitems.pop(0)
                _LOGGER.debug(f"Generating Config Form for item: {item} ")
                ### For each Function/MenuItem selected, list the entities available and allow the user to select what to monitor/poll
                ### Note - these could be submenus
                return await self._show_submenu_selection_form(item,user_input)
            else:
                # We are done
                return
        return await self._show_submenu_selection_form(item,user_input)


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
                vol.Required(CONF_PASSWORD): str
            }
            ),
            errors=self._errors,
        )

    async def _show_device_selection_form(self, user_input):  # pylint: disable=unused-argument
        """Show the device selection form. """
        _LOGGER.debug("Building device list from: " + str(self._discovereddevices))
        device_list_selector = []
        for device in self._discovereddevices:
            devchannel=str(device["Text"]["Long"]).split(' ',1)[0]
            devname=str(device["Text"]["Long"]).split(' ',1)[1]
            for dev in self.alldevices:
                if dev['Addr'] == devchannel:
                    device["Name"]=dev['Name']
                else:
                    device["Name"]=devname
            device["LongName"]=str(device["Text"]["Long"])
            device_list_selector.append(selector.SelectOptionDict(value=json.dumps(device), label="Address+Device: "+str(device["Text"]["Long"] +" (Name:"+device["Name"]+")")))
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_DEVICE): selector.SelectSelector(selector.SelectSelectorConfig(options=device_list_selector)),
                vol.Required(CONF_USE_DEVICE_LONGNAME, default=self._options[CONF_USE_DEVICE_LONGNAME]): bool,
                vol.Required(CONF_PREFIX_FUNCTION, default=self._options[CONF_PREFIX_FUNCTION]): bool,
                vol.Required(CONF_PREFIX_OPLINE, default=self._options[CONF_PREFIX_OPLINE]): bool
            }
            ),
            errors=self._errors,
        )

    async def _show_mainmenu_selection_form(self, user_input):  # pylint: disable=unused-argument
        """Show the menu item selection form. """
        _LOGGER.debug("Building Menu Item list from " + str(self._devicemenuitems))
        menuitem_list_selector = []
        for menuitem in self._devicemenuitems:
            menuitem_list_selector.append(selector.SelectOptionDict(value=json.dumps(menuitem), label=menuitem["Text"]["Long"]))
        return self.async_show_form(
            step_id="mainmenu",
            data_schema=vol.Schema(
            {
                vol.Required(CONF_MENUITEMS,default=False): selector.SelectSelector(selector.SelectSelectorConfig(options=menuitem_list_selector, multiple=True))
            }
            ),
            errors=self._errors,
        )

    async def _show_submenu_selection_form(self, item, user_input):  # pylint: disable=unused-argument
        """Show the Sub Menu Itme and Data Point item selection form. """
        _LOGGER.debug(f"Building SubMenu list for item: {item} ")
        datapoint_list_selector = []
        menuitem_list_selector = []
        
        menutree_item=json.loads(item)
        menutree_id=menutree_item["Id"]
        menutree_name=menutree_item["Text"]["Long"]
        if "MenuItem" not in item:
            menutree_menulocation = menutree_name
        else:
            menutree_menulocation = menutree_item["MenuItem"] + "->" + menutree_name
        existing_menu_items = self._devicemenuitems
        existing_dp_items = self._datapoints
        
        new_all_items = await self._get_menutree(menutree_id)
        new_dp_items = new_all_items["DatapointItems"]
        new_menu_items = new_all_items["MenuItems"]

        _LOGGER.debug(f'Generating form for Submenus: {new_menu_items} and DataPoints: {new_dp_items} at menulocation: {menutree_menulocation} ')
        for menu in new_menu_items:
            menu["MenuItem"]=menutree_menulocation
            menuitem_list_selector.append(selector.SelectOptionDict(value=json.dumps(menu), label=menu["Text"]["Long"]) )

        for dp in new_dp_items:
            ### If we are already polling a variable - don't list it.
            already_exists=False
            for edp in existing_dp_items:
                if edp["Id"] == dp["Id"]:
                    already_exists=True
                    break
            ### If this is something new to monitor - add it to our Dict.
            if not already_exists:
                dp["MenuItem"]=menutree_menulocation
                datapoint_list_selector.append(selector.SelectOptionDict(value=json.dumps(dp), label=dp["Text"]["Long"]))
        this_data_schema=vol.Schema({vol.Optional(CONF_DATAPOINTS): "",vol.Optional(CONF_DATAPOINTS): ""})
        
        if len(datapoint_list_selector) == 0 and len(menuitem_list_selector) == 0:
            this_data_schema=vol.Schema(
            {
                vol.Optional(CONF_MENUITEMS): "",
                vol.Optional(CONF_DATAPOINTS): "" 
            }
            )
        elif len(datapoint_list_selector) == 0 and len(menuitem_list_selector) > 0:
            this_data_schema=vol.Schema(
            {
                vol.Optional(CONF_MENUITEMS, default=[]): selector.SelectSelector(selector.SelectSelectorConfig(options=menuitem_list_selector, multiple=True)),
                vol.Optional(CONF_DATAPOINTS): "" 
            }
            )
        elif len(datapoint_list_selector) > 0 and len(menuitem_list_selector) == 0:
            this_data_schema=vol.Schema(
                {
                vol.Optional(CONF_MENUITEMS): "",
                vol.Required(CONF_DATAPOINTS, default=[]): selector.SelectSelector(selector.SelectSelectorConfig(options=datapoint_list_selector, multiple=True))
                }
            )
        elif len(datapoint_list_selector) > 0 and len(menuitem_list_selector) > 0:
            this_data_schema=vol.Schema(
                {
                vol.Optional(CONF_MENUITEMS, default=[]): selector.SelectSelector(selector.SelectSelectorConfig(options=menuitem_list_selector, multiple=True)),
                vol.Required(CONF_DATAPOINTS, default=[]): selector.SelectSelector(selector.SelectSelectorConfig(options=datapoint_list_selector, multiple=True))
                }
            )
        _LOGGER.debug(f'Data schema: {this_data_schema}')
        return self.async_show_form(
            step_id="submenu",
            data_schema=this_data_schema,
            description_placeholders={"item_name": menutree_menulocation},
            errors=self._errors,
        )


    async def _test_credentials(self, host, protocol, username, password, timeout, retries):
        """Return true if credentials are valid."""
        try:
            self._session = async_create_clientsession(self.hass)
            self._client = SiemensOzw672ApiClient(host, protocol, username, password, self._session, timeout, retries)
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
        except Exception as err: # pylint: disable=broad-except
            _LOGGER.debug(f'Exception: {repr(err)}')
            pass
        return devices

    async def _get_menutree(self,id):
        try:
            output = await self._client.async_get_menutree(id)
        except Exception as err: # pylint: disable=broad-except
            _LOGGER.debug(f'Exception: {repr(err)}')
            pass
        return output

    async def _get_datapoints(self,id):
        try:
            output = await self._client.async_get_datapoints(id)
        except Exception as err: # pylint: disable=broad-except
            _LOGGER.debug(f'Exception: {repr(err)}')
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
    """Config flow options handler for siemens_ozw672."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        _LOGGER.debug(f'OptionsFlow - Existing options: {self.options}')
        self.conf_httptimeout = self.options.get(CONF_HTTPTIMEOUT)
        self.conf_httpretries = self.options.get(CONF_HTTPRETRIES)
        self.conf_scaninterval = self.options.get(CONF_SCANINTERVAL)
        self.conf_use_device_longname = self.options.get(CONF_USE_DEVICE_LONGNAME) 
        if self.conf_httptimeout == None: self.conf_httptimeout=DEFAULT_HTTPTIMEOUT
        if self.conf_httpretries == None: self.conf_httpretries=DEFAULT_HTTPRETRIES
        if self.conf_scaninterval == None: self.conf_scaninterval=DEFAULT_SCANINTERVAL
        if self.conf_use_device_longname ==None: self.conf_use_device_longname=DEFAULT_USE_DEVICE_LONGNAME

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            _LOGGER.debug(f'Updating Options.  New Options: {self.options}')
            return await self._update_options()
            

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HTTPTIMEOUT, default=self.conf_httptimeout): int,
                    vol.Required(CONF_HTTPRETRIES, default=self.conf_httpretries): int,
                    vol.Required(CONF_SCANINTERVAL, default=self.conf_scaninterval): int,
                    vol.Required(CONF_USE_DEVICE_LONGNAME, default=self.conf_use_device_longname): bool,
                    vol.Required("switch", default=self.options.get("switch", True)): bool,
                    vol.Required("select", default=self.options.get("select", True)): bool,
                    vol.Required("number", default=self.options.get("number", True)): bool,
                    vol.Required("binary_sensor", default=self.options.get("binary_sensor", True)): bool,
                    vol.Required("sensor", default=self.options.get("sensor", True)): bool
                }
            )
        )

    async def _update_options(self):
        """Update config entry options."""
        _LOGGER.debug(
            "Recreating entry %s due to configuration change",
            self.config_entry.title
        )
        return self.async_create_entry(title="", data=self.options)



