"""The Pluxee Portugal integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any

from .const import CONF_NIF, PLATFORMS, is_valid_nif, normalize_nif

_LOGGER = logging.getLogger(__name__)

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


async def async_migrate_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Migrate older config entries to the latest normalized NIF format."""
    if entry.version > 1:
        return False

    if entry.version == 1 and entry.minor_version < 2:
        from .client import title_for_nif

        normalized_nif = normalize_nif(entry.data.get(CONF_NIF, ""))
        updates: dict[str, Any] = {
            "version": 1,
            "minor_version": 2,
        }

        if is_valid_nif(normalized_nif):
            updates["data"] = {
                **entry.data,
                CONF_NIF: normalized_nif,
            }
            updates["unique_id"] = normalized_nif
            updates["title"] = title_for_nif(normalized_nif)
        else:
            _LOGGER.warning(
                "Skipping Pluxee NIF normalization for entry %s because the stored value is invalid.",
                entry.entry_id,
            )

        hass.config_entries.async_update_entry(entry, **updates)

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
