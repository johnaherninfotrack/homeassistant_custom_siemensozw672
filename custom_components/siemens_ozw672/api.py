"""Sample API Client."""
import asyncio
import logging
import socket
import time

import urllib.parse as Parse
import re
import json

import aiohttp
import async_timeout

from .const import TESTDATA

_LOGGER: logging.Logger = logging.getLogger(__package__)
HEADERS = {"Content-type": "application/json; charset=UTF-8"}

class SiemensOzw672ApiClient:
    def __init__(
        self, host: str, protocol: str, username: str, password: str, session: aiohttp.ClientSession, timeout: int, retries: int
    ) -> None:
        """Siemens OZW672 API Client."""
        _LOGGER.debug("OZW Init")
        self._host = host
        self._protocol = protocol
        self._username = username
        self._password = password
        self._session = session
        self._sessionid = "None"
        self._dpdata = None 
        self._timeout = timeout
        self._retries = retries

    async def async_get_sessionid(self) -> bool:
        """Login to the OZW672 and get a SessionID"""
        url=self._protocol + "://" + self._host + "/api/auth/login.json?user=" + self._username + "&pwd=" + Parse.quote(self._password)
        _LOGGER.debug(f"OZW Login to host: {self._host}")
        if (self._host == "test"):
            response=json.loads(TESTDATA["PREAUTH"])
        else:
            response = await self.api_wrapper("get_preauth", url)
        success = response["Result"]["Success"]
        if (success == "true"): 
            self._sessionid = response["SessionId"]
            return True
        _LOGGER.debug(f"Failed to Login: {response}")
        return False

    async def async_get_sysinfo(self) -> dict:
        """ Sample: ./api/device/info.json?SessionId=1278af3d-a62d-4def-938e-ae2df141500e """
        url=self._protocol + "://" + self._host + "/api/device/info.json?SessionId=" + self._sessionid
        if (self._host == "test"):
            response=json.loads(TESTDATA["SYSINFOLIST"])
        else:
            response = await self.api_wrapper("get", url)
        _LOGGER.debug(f'async_get_sysinfo - response: {response}')
        success = response["Result"]["Success"]
        if (success == "true"):
            return(response["Device"])
        return None

    async def async_get_devices(self) -> dict:
        """Get the device list from the OZW672. - IS THIS USED????"""
        """ Sample: ./api/devicelist/list.json?SessionId=af06e880-bd59-4fb7-873d-d7b3fbc9561f """
        url=self._protocol + "://" + self._host + "/api/devicelist/list.json?SessionId=" + self._sessionid
        if (self._host == "test"):
            response=json.loads(TESTDATA["DEVICELIST"])
        else:
            response = await self.api_wrapper("get", url)
        _LOGGER.debug(f'async_get_devices - response: {response}')
        success = response["Result"]["Success"]
        if (success == "true"):
            return(response["Devices"])
        return None

    async def async_get_menutree(self,id) -> dict:
        """Get the Menu Tree from the OZW672.  If Id="" - then it lists the devices"""
        """ Sample: ./api/menutree/list.json?SessionId=29090e86-3c9a-4eb3-9e95-d5c1729c41e3&Id="""
        url=self._protocol + "://" + self._host + "/api/menutree/list.json?SessionId=" + self._sessionid +"&Id=" + id
        if (self._host == "test") and (id==""):
            response=json.loads(TESTDATA["MENUTREEDEVICELIST"])
        elif (self._host == "test") and (int(id) > 0):
            response=json.loads(TESTDATA["MENUITEMLIST"][id])
        elif (self._host == "test"):
            response=json.loads(TESTDATA["MENUITEMLIST"])
        else:
            response = await self.api_wrapper("get", url)
        _LOGGER.debug(f"async_get_menutree reponse: {response}")
        success = response["Result"]["Success"]
        if (success == "true"):
            return(response)
        return None

    async def async_get_datapoints(self,id) -> dict:
        """Get the DataPoint(s) from the OZW672. """
        url=self._protocol + "://" + self._host + "/api/menutree/list.json?SessionId=" + self._sessionid +"&Id=" + id       
        _LOGGER.debug(f"async_get_datapoints: url={url} id={id}")
        if (self._host == "test"):
            response=json.loads(TESTDATA["DATAPOINTLIST"][id])
        else:
            response = await self.api_wrapper("get", url)
        _LOGGER.debug(f"async_get_datapoints Datapoint Data reponse: {response}")
        success = response["Result"]["Success"]
        if (success == "true"):
            return(response["DatapointItems"])
        return None
        #Sample response: {"MenuItems": [], "DatapointItems": [{"Id": "1438", "Address": "0x310571", "DpSubKey": "0", "WriteAccess": "true", "Text": {"CatId": "2", "GroupId": "2", "Id": "3514", "Long": "DHW operating mode", "Short": "DHW OptgMode"}}], "WidgetItems": [], "Result": {"Success": "true"}}"""

    async def async_get_data(self, datapoints) -> dict:
        """Get the Data for multiple datapoints from the OZW6722."""
        start_time = time.time()
        _LOGGER.debug(f"async_get_data Getting data for datapoints : {datapoints}")
        consolidated_response={}
        for dp in datapoints:
            if (type(dp) == str):
                dpdata = json.loads(dp)
            else:
                dpdata = dp
            id = dpdata["Id"]
            url=self._protocol + "://" + self._host + "/api/menutree/read_datapoint.json?SessionId=" + self._sessionid +"&Id=" + id
            if (self._host == "test"):
                response=json.loads(TESTDATA["DATAPOINT"][id])
            else:
                response = await self.api_wrapper("get", url)
            _LOGGER.debug(f"async_get_data response : {response}")
            if (response["Result"]["Success"] == "true"):
                if (response["Data"]["Value"] == '----'):
                    response["Data"]["Value"] = '0'
                consolidated_response[id]=response
        elapsed_time = time.time() - start_time
        if elapsed_time > 60:
            _LOGGER.warn(f"OZW672 Data Poll time exceeding 60 seconds. Last Poll Time: {round(elapsed_time)} seconds")
        _LOGGER.debug(f"OZW672 Data Poll time: {round(elapsed_time)} seconds")
        return consolidated_response
        # Sample response {"Data": {"Type": "Enumeration", "Value": "On", "Unit": ""}, "Result": {"Success": "true"}}

    async def async_write_data(self, datapoint, value) -> dict:
        """Write the Data for a single datapoints to the OZW6722."""
        _LOGGER.debug(f"async_get_data Writing data for datapoint : {datapoint}")
        if (type(datapoint) == str):
            dpdata = json.loads(datapoint)
        else:
            dpdata = datapoint
        id = dpdata["Id"]
        dptype = dpdata["DPDescr"]["Type"]
        hasValid = dpdata["DPDescr"]["HasValid"]
        url=self._protocol + "://" + self._host + "/api/menutree/write_datapoint.json?SessionId=" + self._sessionid +"&Id=" + id + "&Type=" + dptype + "&Value=" + value
        if (hasValid == 'true'):
            url=url + '&IsValid=true'
        if (self._host == "test"):
            # I could do something here to make the test work using the DPDescr cached data
            response=json.loads(TESTDATA["DATAPOINT"][id])
        else:
            response = await self.api_wrapper("get", url)
        _LOGGER.debug(f"async_get_data Datapoint Data response : {response}")
        if (response["Result"]["Success"] == "true"):
            _LOGGER.debug(f"GetData Response: {response}")
            return response
        else:
            return {}


    async def async_get_data_descr(self,datapoints,all_dpdata) -> dict:
        """Get the DataPoint Descriptions for multiple datapoints from the OZW672. """
        _LOGGER.debug(f"async_get_data_descr Getting data descriptions for datapoints : {datapoints}")
        consolidated_response={}
        for dp in datapoints:
            dpjson = json.loads(dp)
            id = dpjson["Id"]
            dpdata=all_dpdata[id]
            writeable = dpjson["WriteAccess"]
            #_LOGGER.debug(f"GetDataDescr config: {dp}")
            #_LOGGER.debug(f"GetDataDescr data: {dpdata}")
            url=self._protocol + "://" + self._host + "/api/menutree/datapoint_desc.json?SessionId=" + self._sessionid +"&Id=" + id       
            if (self._host == "test"):
                response=json.loads(TESTDATA["DATAPOINTDESCR"][id])
            else:
                if writeable == "true":  #We only need descriptions for Writeable datapoints.
                    response = await self.api_wrapper("get", url)
                else:  #Just return the Type - save the OZW a load of queries.
                    response=json.loads("""{"Description":{"Type":\""""+dpdata['Data']['Type']+"""\"},"Result": {"Success": "true"}}""")
            if (response["Result"]["Success"] == "true"):
                _LOGGER.debug(f"DatapointItem description reponse: {response}")
                ### This is the main place where the sensors are categorised into domains
                ### Data Point Descriptions are only polled at the time of discovery
                ###
                # Enumeration + Writeable + NOT On/Off = Select Entity
                # Enumeration + Writeable + On/Off = Switch
                # RadioButton/Enumeration + NOT Writeable + On/Off = BinarySensor
                # Number + Writeable + Percent/Temp = Number
                # Number + NOT Writeable + Percent/Temp = Sensor
                # Number + Writeable/NOT Writeable + OtherType = Sensor
                # Everything Else = Sensor
                ###
                if response["Description"]["Type"] == "Enumeration":
                    if writeable == "true":
                        if dpdata["Data"]["Value"] in ['On', 'Off'] :
                            response["Description"]["HAType"] = "switch"
                        else:
                            response["Description"]["HAType"] = "select" 
                    else:
                        if dpdata["Data"]["Value"] in ['On', 'Off'] :
                            response["Description"]["HAType"] = "binarysensor"
                        else:
                            response["Description"]["Enums"] = []  #Some Enums are huge - don't need them for read only sensors.
                            response["Description"]["HAType"] = "sensor"
                elif response["Description"]["Type"] == "RadioButton":
                    if writeable == "true":
                        response["Description"]["HAType"] = "switch"
                    else:
                        response["Description"]["HAType"] = "binarysensor"
                elif response["Description"]["Type"] == "Numeric":
                    if writeable == "true" and response["Description"]["Unit"] in ['°C', '°F', 'K', '%']:
                        response["Description"]["HAType"] = "number"
                    else:
                        response["Description"]["HAType"] = "sensor"
                elif response["Description"]["Type"] == "TimeOfDay":
                    if writeable == "true":
                        response["Description"]["HAType"] = "time"
                    else:
                        response["Description"]["HAType"] = "sensor"
                else:   
                        response["Description"]["HAType"] = "sensor"
                consolidated_response[id]=response
        _LOGGER.debug(f"async_get_data_descr DatapointItem description reponse: {consolidated_response}")
        return consolidated_response

    async def api_wrapper(
        self, method: str, url: str, data: dict = {}, headers: dict = {}
    ) -> dict:
        """Get information from the OZW WebAPI."""

        for x in range(self._retries):  #### YES - WE NEED TO RETRY OCCASSIONALY
            try:
                async with async_timeout.timeout(self._timeout): #, loop=asyncio.get_event_loop()):
                    if method == "get_preauth":
                        response = await self._session.get(url, headers=headers,verify_ssl=False)
                        jsonresponse = await response.json()
                        _LOGGER.debug(f"PREAuth: {jsonresponse}")
                        return jsonresponse
                    elif method == "get":
                        cache_sessionid = self._sessionid
                        response = await self._session.get(url, headers=headers,verify_ssl=False)
                        jsonresponse = await response.json()
                        _LOGGER.debug(f"API GET: {jsonresponse}")
                        if (jsonresponse["Result"]["Success"] == "false"):
                            if (jsonresponse["Result"]["Error"]["Nr"] in ['1','2']):
                                await self.async_get_sessionid()
                                # Search and replace SessionId
                                newurl = url.replace(f"SessionId={cache_sessionid}", f"SessionId={self._sessionid}")
                                return await self.api_wrapper("get", newurl)
                            else :
                                url.replace(f"SessionId={cache_sessionid}", "SessionId=XXXXXX")
                                _LOGGER.error(f'Failed API call with error: {jsonresponse["Result"]["Error"]["Txt"]} for url:{url}')
                                return jsonresponse
                        else:
                            return jsonresponse

            except asyncio.TimeoutError as exception:
                _LOGGER.error(
                    "Timeout error fetching information from %s - %s",
                    url,
                    exception,
                )
                if x < self._retries:
                    _LOGGER.error("**** Module will retry ****")
                    pass

            except (KeyError, TypeError) as exception:
                _LOGGER.error(
                    "Error parsing information from %s - %s",
                    url,
                    exception,
                )
            except (aiohttp.ClientError, socket.gaierror) as exception:
                _LOGGER.error(
                    "Error fetching information from %s - %s",
                    url,
                    exception,
                )
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.error("Something really wrong happened! - %s", exception)
