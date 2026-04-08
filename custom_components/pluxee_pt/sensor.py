"""Sensor platform for Pluxee Portugal."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PluxeePtRuntimeData
from .const import BALANCE_PAGE_URL, CONF_NIF, DOMAIN, SENSOR_KEY_AVAILABLE_BALANCE
from .coordinator import PluxeePtDataUpdateCoordinator


async def async_setup_entry(
    hass,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    runtime_data: PluxeePtRuntimeData = entry.runtime_data
    async_add_entities(
        [PluxeeAvailableBalanceSensor(runtime_data.coordinator, entry)],
    )


class PluxeeBaseEntity(
    CoordinatorEntity[PluxeePtDataUpdateCoordinator],
    SensorEntity,
):
    """Base entity shared by Pluxee Portugal sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PluxeePtDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        unique_id = entry.unique_id or entry.data[CONF_NIF]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Pluxee",
            model="Portugal Consumer Portal",
            name=entry.title,
            configuration_url=BALANCE_PAGE_URL,
        )


class PluxeeAvailableBalanceSensor(PluxeeBaseEntity):
    """Balance sensor for the configured Pluxee account."""

    _attr_icon = "mdi:wallet"
    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = SENSOR_KEY_AVAILABLE_BALANCE

    def __init__(
        self,
        coordinator: PluxeePtDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the balance sensor."""
        super().__init__(coordinator, entry)
        unique_id = entry.unique_id or entry.data[CONF_NIF]
        self._attr_unique_id = f"{unique_id}_{SENSOR_KEY_AVAILABLE_BALANCE}"

    @property
    def native_value(self):
        """Return the current balance."""
        return self.coordinator.data.balance

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional metadata for the card."""
        return {
            "balance_text": self.coordinator.data.balance_raw,
            "source_url": self.coordinator.data.source_url,
        }
