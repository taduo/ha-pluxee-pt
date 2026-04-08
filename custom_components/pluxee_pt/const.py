"""Constants for the Pluxee Portugal integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "pluxee_pt"
NAME = "Pluxee Portugal"
VERSION = "0.1.0"

CONF_NIF = "nif"

LOGIN_PAGE_URL = "https://portal.admin.pluxee.pt/"
LOGIN_PROCESSING_URL = "https://portal.admin.pluxee.pt/login_processing.php"
BALANCE_PAGE_URL = "https://consumidores.pluxee.pt/"

REQUEST_TIMEOUT_SECONDS = 20
COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=30)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SENSOR_KEY_AVAILABLE_BALANCE = "available_balance"
