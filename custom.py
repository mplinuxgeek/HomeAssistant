"""
"""
from homeassistant.helpers.discovery import load_platform

def setup(hass, config):
    """Your controller/hub specific code."""

    #--- snip ---
    load_platform(hass, 'climate', 'skify')
    load_platform(hass, 'light', 'lazybone')



