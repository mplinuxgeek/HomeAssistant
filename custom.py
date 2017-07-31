"""
"""
from homeassistant.helpers.discovery import load_platform
DOMAIN = 'skyfi'

def setup(hass, config):
    """Your controller/hub specific code."""

    #--- snip ---
    load_platform(hass, 'climate', DOMAIN)

