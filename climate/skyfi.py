"""
Daikin SkyFi platform that offers a climate device for Diakin A/C.
"""
import logging
import os
import sys
import select
import http.client
import time
import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate import (
    ClimateDevice, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, CONF_HOST, CONF_PASSWORD
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,})

_LOGGER = logging.getLogger(__name__)

SUPPORT_TARGET_TEMPERATURE = 1
SUPPORT_TARGET_TEMPERATURE_HIGH = 2
SUPPORT_TARGET_TEMPERATURE_LOW = 4
SUPPORT_TARGET_HUMIDITY = 8
SUPPORT_TARGET_HUMIDITY_HIGH = 16
SUPPORT_TARGET_HUMIDITY_LOW = 32
SUPPORT_FAN_MODE = 64
SUPPORT_OPERATION_MODE = 128
SUPPORT_HOLD_MODE = 256
SUPPORT_SWING_MODE = 512
SUPPORT_AWAY_MODE = 1024
SUPPORT_AUX_HEAT = 2048
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_FAN_MODE


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Demo climate devices."""
    host = config.get(CONF_HOST)
    password = config.get(CONF_PASSWORD)
    add_devices([
        SkyFiClimate('Daikin', TEMP_CELSIUS, host, password)
    ])



class SkyFiClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, name, unit_of_measurement, host, password):
        """Initialize the climate device."""
        self._name = name
        self._unit_of_measurement = unit_of_measurement
        self._host = host
        self._password = password
        self._fan_list = ['', 'Low', 'Medium', 'High']
        self._operation_list = [ 'Off', 'Auto', 'Heat', 'Cool', 'Dry' ]
        self._operation_dict = { 0:'Off', 1:'Auto', 2:'Heat', 8:'Cool', 16:'Dry' }
        self._operation_mode = { 'Off':0, 'Auto':1, 'Heat':2, 'Cool':8, 'Dry':16 }
        self._current_temperature = 21.0
        self._target_temperature = 21.0
        self._current_fan_mode = self._fan_list[1]
        self._current_operation = self._operation_list[0]

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    def update(self):
        payload = "/ac.cgi?pass={}".format(self._password)
        self.doQuery(payload)

    def set_props(self, data):
        plist = {}
        lst = data.split("&")
        for x in lst:
            v = x.split("=")
            plist[v[0]] = v[1]

        self._current_temperature = float(plist['roomtemp'])
        self._target_temperature = float(plist['settemp'])
        if int(plist['opmode']) == 0:
            self._current_operation = self._operation_list[0]
        else:
            self._current_operation = self._operation_dict[int(plist['acmode'])]
        self._current_fan_mode = self._fan_list[int(plist["fanspeed"])]

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._current_operation == self._operation_list[0]:
            return 0
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        # if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None and \
        #    kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
        #     self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        #     self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        self.set_state()

    def set_fan_mode(self, fan):
        """Set new target temperature."""
        self._current_fan_mode = fan
        self.set_state()

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation = operation_mode
        self.set_state()

    def set_state(self):
        """Set the new state of the ac"""
        mode = self._operation_mode[self._current_operation]
        if mode == 0:
            pstate = 0
        else:
            pstate = 1
        fan = self._fan_list.index(self.current_fan_mode)
        payload = "/set.cgi?pass={}&p={}&t={:.5f}&f={}".format(self._password, pstate, self._target_temperature, fan)
        self.doQuery(payload)

    def doQuery(self, payload):
        """send query to SkyFi"""
        retry_count = 5
        while retry_count > 0:
            retry_count = retry_count - 1
            try:
                conn = http.client.HTTPConnection(self._host, 2000)
                conn.request("GET", payload)
                resp = conn.getresponse()
                data = resp.read().decode()
                conn.close()
                self.set_props(data)
                retry_count = 0
            except Exception as ex:
                if retry_count == 0:
                    _LOGGER.warning("Query: {} failed {}: {}".format(self._name, payload, ex))
                conn.close()
                time.sleep(2)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS
