"""The Pluxee Portugal integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .const import CONF_NIF, PLATFORMS

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .client import PluxeePtClient
    from .coordinator import PluxeePtDataUpdateCoordinator


@dataclass(slots=True)
class PluxeePtRuntimeData:
    """Runtime objects stored on the config entry."""

    client: "PluxeePtClient"
    coordinator: "PluxeePtDataUpdateCoordinator"


async def async_setup(hass: "HomeAssistant", config: dict[str, Any]) -> bool:
    """Set up the integration from YAML."""
    return True


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Set up Pluxee Portugal from a config entry."""
    from homeassistant.const import CONF_PASSWORD
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .client import PluxeePtClient
    from .coordinator import PluxeePtDataUpdateCoordinator

    session = async_get_clientsession(hass)
    client = PluxeePtClient(
        session,
        entry.data[CONF_NIF],
        entry.data[CONF_PASSWORD],
    )
    coordinator = PluxeePtDataUpdateCoordinator(hass, entry, client)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = PluxeePtRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
