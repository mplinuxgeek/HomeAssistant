"""
Demo light platform that implements lights.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/demo/
"""
import logging
import socket

import voluptuous as vol

from homeassistant.const import CONF_HOST
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_EFFECT,
    ATTR_RGB_COLOR, ATTR_WHITE_VALUE, ATTR_XY_COLOR, SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP, SUPPORT_EFFECT, SUPPORT_RGB_COLOR, SUPPORT_WHITE_VALUE,
    Light)
from homeassistant.exceptions import TemplateError
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_HOST): cv.string
    })

SUPPORT_LAZYBONE = (SUPPORT_BRIGHTNESS)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Set up the Demo climate devices."""
    host = config.get(CONF_HOST)
    name = config.get("name")
    """Set up LazyBone light platform."""
    add_devices_callback([
        LazyBoneLight(name, host),
    ])


class LazyBoneLight(Light):
    """Representation of a demo light."""

    def __init__(self, name, host):
        """Initialize the light."""
        self._name = name
        self._state = False
        self._brightness = 128
        self._host = host

    @property
    def should_poll(self) -> bool:
        """No polling needed for a demo light."""
        return True

    @property
    def name(self) -> str:
        """Return the name of the light if any."""
        return self._name

    @property
    def available(self) -> bool:
        """Return availability."""
        # This demo light is always available, but well-behaving components
        # should implement this to inform Home Assistant accordingly.
        return True

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_LAZYBONE

    def turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        self._state = True

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        self.set_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        self._state = False

        self.set_state()

    def update(self):
        _LOGGER.info("GetState Lazybone: {} {}".format(self._state, self._brightness))

    def update_xx(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self._host, 2000))
                #readable, _, _ = select.select([sock], [], [], 2000)
                value = sock.recv(7)
                query = bytearray()
                query.append(0x5B)
                query.append(0x00)
                query.append(0x0D)
                #query = bytes.fromhex('6F000D')
                len = sock.send(query)
                value = sock.recv(2)
                sock.close()
                if value[0] == 0x00:
                    self._state = False;
                else:
                    self._state = True;
                self._brightness = 256 - value[1]
            _LOGGER.info("GetState Lazybone: {:d}", self._brightness)
        except:
            e = sys.exc_info()[0]
            _LOGGER.warning("Failed to get state: {}", e)
            self.set_state()        

    def set_state(self):
        _LOGGER.info("SetState Lazybone")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self._host, 2000))
                #readable, _, _ = select.select([sock], [], [], 2000)
                value = sock.recv(7)
                query = bytearray()
                query.append(0x67)
                query.append(256 - self._brightness)
                query.append(0x0D)
                #query = bytes.fromhex('6F000D')
                len = sock.send(query)
                if self._state:
                    query[0] = 0x65
                else:
                    query[0] = 0x6F
                len = sock.send(query)
                sock.close()
        except:
            e = sys.exc_info()[0]
            _LOGGER.warning("Failed to set state: {}", e)
            self.set_state()        
