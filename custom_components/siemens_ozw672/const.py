"""Constants for Siemens OZW672."""
# Base component constants
NAME = "Siemens OZW672"
DOMAIN = "siemens_ozw672"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"

ATTRIBUTION = "Integration created by John"
ISSUE_URL = "https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672/issues"

# Icons
ICON = "mdi:bookmark"
ICON_THERMOMETER ="mdi:thermometer"
ICON_PERCENT ="mdi:percent"
ICON_ENUM="mdi:bookmark"
ICON_SWITCH="mdi:toggle-switch"
ICON_SELECT="mdi:gesture-tap"



# Device classes
BINARY_SENSOR_DEVICE_CLASS = "power"


# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
SELECT = "select"
NUMBER = "number"
PLATFORMS = [SWITCH, SELECT, NUMBER, BINARY_SENSOR, SENSOR]
#PLATFORMS = [NUMBER, SENSOR]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_HOST = "hostname"
CONF_DEVICE = "devicename"
CONF_DEVICE_ID = "deviceid"
CONF_PROTOCOL = "protocol"
CONF_MENUITEMS = "menuitems"
CONF_DATAPOINTS = "datapoints"
CONF_PREFIX_FUNCTION = "prefix_with_function"
CONF_PREFIX_OPLINE = "prefix_with_opline"


# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""


TESTDATA={}
TESTDATA["PREAUTH"]="""{"SessionId": "8ee67600-b4d8-4f66-b48e-ca2eabd1f2e7", "Result": {"Success": "true"}}"""
TESTDATA["DEVICELIST"]="""{"Devices": [{"Name": "OZW672.01", "Addr": "0.5", "Type": "OZW672.01", "SerialNr": "00FD3100033C", "TreeDate": "22.05.2023", "TreeTime": "16:19", "TreeGenerated": "true"}, {"Name": "RVS43.345/109a", "Addr": "0.1", "Type": "RVS43.345/109", "SerialNr": "008600004EBF", "TreeDate": "08.06.2023", "TreeTime": "20:15", "TreeGenerated": "true"}], "Result": {"Success": "true"}}"""
TESTDATA["MENUTREEDEVICELIST"]="""{"MenuItems": [{"Id": "1327", "Text": {"CatId": "2", "GroupId": "4", "Id": "106", "Long": "0.1 RVS43.345/109", "Short": "TSP 1"}}, {"Id": "2", "Text": {"CatId": "1", "GroupId": "4", "Id": "106", "Long": "0.5 OZW672.01", "Short": "Device"}}], "DatapointItems": [], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["SYSINFOLIST"]="""{"Device": {"Name": "OZW672.01", "Addr": "0.5", "Type": "OZW672.01", "FabNr": "021863", "SerialNr": "00FD3100033C", "FwVersion": "00.11.00", "SysDefVersion": "02.29.01"}, "Result": {"Success": "true"}}"""
TESTDATA["MENUITEMLIST"]="""{"MenuItems": [{"Id": "1437", "Text": {"CatId": "2", "GroupId": "4", "Id": "295", "Long": "DHW", "Short": "DHW"}},{"Id": "1959","Text": {"CatId": "2","GroupId": "4","Id": "315","Long": "Diagnostics consumer","Short": "Diagnostics consumer"}}], "DatapointItems": [], "WidgetItems": [], "Result": {"Success": "true"}}"""

TESTDATA["DATAPOINTLIST"]={}
TESTDATA["DATAPOINTLIST"]["1437"]="""{"MenuItems": [], "DatapointItems": [{"Id": "1438", "Address": "0x310571", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3514", "Long": "DHW operating mode", "Short": "DHW OptgMode"}}, {"Id": "1439", "Address": "0x3106b9", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3516", "Long": "DHW temperature nominal setpoint", "Short": "DHW NomSetp"}}, {"Id": "1441", "Address": "0x250722", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3522", "Long": "DHW release", "Short": "DHW Release"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1438"]="""{"MenuItems": [], "DatapointItems": [{"Id": "1438", "Address": "0x310571", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3514", "Long": "DHW operating mode", "Short": "DHW OptgMode"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1439"]="""{"MenuItems": [], "DatapointItems": [{"Id": "1439", "Address": "0x3106b9", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3516", "Long": "DHW temperature nominal setpoint", "Short": "DHW NomSetp"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1441"]="""{"MenuItems": [], "DatapointItems": [{"Id": "1441", "Address": "0x250722", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3522", "Long": "DHW release", "Short": "DHW Release"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1959"]="""{"MenuItems": [], "DatapointItems": [{"Id":"1960","Address":"0x50521","DpSubKey":"0","WriteAccess":"false","Text":{"CatId":"2","GroupId":"2","Id":"39","Long":"Outside temp","Short":"Outside temp"}},{"Id":"1966","Address":"0x509a5","DpSubKey":"0","WriteAccess":"false","Text":{"CatId":"2","GroupId":"2","Id":"5328","Long":"Status heat circuit pump 1","Short":"Heatcircuitpump1"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1960"]="""{"MenuItems": [], "DatapointItems": [{"Id":"1960","Address":"0x50521","DpSubKey":"0","WriteAccess":"false","Text":{"CatId":"2","GroupId":"2","Id":"39","Long":"Outside temp","Short":"Outside temp"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINTLIST"]["1966"]="""{"MenuItems": [], "DatapointItems": [{"Id":"1966","Address":"0x509a5","DpSubKey":"0","WriteAccess":"false","Text":{"CatId":"2","GroupId":"2","Id":"5328","Long":"Status heat circuit pump1","Short":"Heatcircuitpump1"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""

TESTDATA["DATAPOINT"]={}
TESTDATA["DATAPOINT"]["1438"]="""{"Data": {"Type": "Enumeration", "Value": "On", "Unit": ""}, "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINT"]["1439"]="""{"Data": {"Type": "Numeric", "Value": "        52", "Unit": "°C"}, "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINT"]["1441"]="""{"Data": {"Type": "Enumeration", "Value": "24h/day", "Unit": "", "EnumValue": "0"}, "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINT"]["1960"]="""{"Data": {"Type": "Numeric","Value": " 15.8","Unit": "°C"}, "Result": {"Success": "true"}}"""
TESTDATA["DATAPOINT"]["1966"]="""{"Data": {"Type": "RadioButton","Value": "On","Unit": ""},"Result": {"Success": "true"}}"""

TESTDATA["DATAPOINTDESCR"]={}
TESTDATA["DATAPOINTDESCR"]["1438"]="""{"Description":{"Type":"Enumeration","Name":"DHW operating mode","Enums":[{"Text":"Off","Value":"0","IsCurrentValue":"false"},{"Text":"On","Value":"1","IsCurrentValue":"true"},{"Text":"Eco","Value":"2","IsCurrentValue":"false"}]},"Result":{"Success":"true"}}"""
TESTDATA["DATAPOINTDESCR"]["1439"]="""{"Description":{"Type":"Numeric","Value":"52.000000","Unit":"°C","Name":"DHW temperature nominal setpoint","Min":"45.000000","Max":"60.000000","Resolution":"1.000000","FieldWitdh":"10","DecimalDigits":"0","HasValid":"false","IsValid":"true"},"Result":{"Success":"true"}}"""
TESTDATA["DATAPOINTDESCR"]["1441"]="""{"Description":{"Type":"Enumeration","Name":"DHW release","Enums":[{"Text":"24h\/day","Value":"0","IsCurrentValue":"true"},{"Text":"Heating programs with forward shift","Value":"1","IsCurrentValue":"false"},{"Text":"Time switch program 4","Value":"2","IsCurrentValue":"false"}]},"Result":{"Success":"true"}}"""
TESTDATA["DATAPOINTDESCR"]["1960"]="""{"Description":{"Type":"Numeric","Value":"15.859375","Unit":"°C","Name":"Outside temp","Min":"-50.000000","Max":"50.000000","Resolution":"0.100000","FieldWitdh":"12","DecimalDigits":"1","HasValid":"false","IsValid":"true"},"Result":{"Success":"true"}}"""
TESTDATA["DATAPOINTDESCR"]["1966"]="""{"Description":{"Type":"RadioButton","Name": "Status heat circuit pump 1","Buttons":[{"TextOpt0": "Off","TextOpt1": "On","Significance": "1","IsActive": "true"} ]},"Result": {"Success": "true"}}"""



