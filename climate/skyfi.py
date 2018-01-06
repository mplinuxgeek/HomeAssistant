"""
Daikin SkyFi platform that offers a climate device for Diakin A/C.
"""
import logging
import os
import sys
import select
import http.client
import sys, traceback

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate import (
    ClimateDevice, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, SUPPORT_FAN_MODE, SUPPORT_OPERATION_MODE, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, CONF_HOST, CONF_PASSWORD
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_OPERATION_MODE)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,})

_LOGGER = logging.getLogger(__name__)

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
        self._fan_list = ['Low', 'Medium', 'High' ]
        self._operation_list = ['Off', 'Auto', 'Heat', 'Cool', 'Fan']
        self._operation_list_full = ['Off', 'Auto', 'Heat', 'Heat/Auto', 'Dry', '5', '6', '7', 'Cool', 'Cool/Auto', '10', '11', '12', '13', '14', '15', 'Fan']
        self._current_temperature = 21.0
        self._target_temperature = 21.0
        self._current_fan_mode = self._fan_list[1]
        self._current_operation = self._operation_list_full[0]

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    def update(self):
        try:
            conn = http.client.HTTPConnection(self._host, 2000)
            conn.request("GET", "/ac.cgi?pass={}".format(self._password))
            resp = conn.getresponse()
            data = resp.read().decode()
            conn.close()
            self.set_props(data)
        except Exception as e:
            _LOGGER.warning("update: {}".format(e))

    def set_props(self, data):
        try:
          md = {}
          lst = data.split("&")
          for x in lst:
              v = x.split("=")
              md[v[0]] = v[1]

          _LOGGER.debug("roomtemp: {}".format(md["roomtemp"]))
          self._current_temperature = float(md['roomtemp'])
          _LOGGER.debug("settemp: {}".format(md["settemp"]))
          self._target_temperature = float(md['settemp'])

          _LOGGER.debug("acmode: {}".format(md["acmode"]))
          if int(md['opmode']) == 0:
              self._current_operation = self._operation_list_full[0]
          else:
              self._current_operation = self._operation_list_full[int(md['acmode'])]

          _LOGGER.debug("fanspeed: {}".format(md["fanspeed"]))
          self._current_fan_mode = self._fan_list[int(md["fanspeed"]) - 1]
        except Exception as e:
            _LOGGER.warning("set_props: {}".format(e))

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
        if self._current_operation == self._operation_list_full[0]:
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
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None and \
           kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
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
        try:
            conn = http.client.HTTPConnection(self._host, 2000)
            if self._current_operation == "False":
                mode = 0
            else:
                mode = self._operation_list.index(self._current_operation)
            _LOGGER.debug("mode = {}".format(mode))
            opmode = 0
            pstate = 1
            if mode == 0:
                pstate = 0;
            elif mode == 1:
                opmode = 1;
            elif mode == 2:
                opmode = 2;
            elif mode == 3:
                opmode = 8;
            elif mode == 4:
                opmode = 16;
            fan = self._fan_list.index(self.current_fan_mode) + 1
            payload = "/set.cgi?pass={}&p={}&t={:.0f}&f={}&m={}".format(self._password, pstate, self._target_temperature, fan, opmode)
            _LOGGER.info("payload = {}".format(payload))
            conn.request("GET", payload)
            resp = conn.getresponse()
            data = resp.read().decode()
            conn.close()
            self.set_props(data)
            #self.schedule_update_ha_state()
#        except:
        except Exception as e:
            _LOGGER.warning("set_state: {}".format(e))
