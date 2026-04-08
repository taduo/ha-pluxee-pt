"""Data update coordinator for Pluxee Portugal."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import (
    PluxeeBalanceData,
    PluxeePtAuthError,
    PluxeePtClient,
    PluxeePtConnectionError,
    PluxeePtParseError,
)
from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PluxeePtDataUpdateCoordinator(DataUpdateCoordinator[PluxeeBalanceData]):
    """Coordinate data updates for a Pluxee account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: PluxeePtClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self.config_entry = entry
        self.client = client

    async def _async_update_data(self) -> PluxeeBalanceData:
        """Fetch data from Pluxee."""
        try:
            return await self.client.async_fetch_balance()
        except PluxeePtAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (PluxeePtConnectionError, PluxeePtParseError) as err:
            raise UpdateFailed(str(err)) from err
