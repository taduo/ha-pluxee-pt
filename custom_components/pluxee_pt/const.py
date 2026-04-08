"""Constants for the Pluxee Portugal integration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta

DOMAIN = "pluxee_pt"
NAME = "Pluxee Portugal"
VERSION = "0.3.0"

CONF_NIF = "nif"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

LOGIN_PAGE_URL = "https://portal.admin.pluxee.pt/"
LOGIN_PROCESSING_URL = "https://portal.admin.pluxee.pt/login_processing.php"
BALANCE_PAGE_URL = "https://consumidores.pluxee.pt/"

REQUEST_TIMEOUT_SECONDS = 20
DEFAULT_UPDATE_INTERVAL_MINUTES = 30
UPDATE_INTERVAL_MINUTES_OPTIONS: tuple[int, ...] = (15, 30, 60, 120)
UPDATE_INTERVAL_OPTION_LABELS = {
    str(minutes): f"{minutes} min" for minutes in UPDATE_INTERVAL_MINUTES_OPTIONS
}

PLATFORMS: list[str] = ["sensor"]

SENSOR_KEY_AVAILABLE_BALANCE = "available_balance"


def normalize_update_interval_minutes(value: object) -> int:
    """Normalize the configured update interval."""
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return DEFAULT_UPDATE_INTERVAL_MINUTES

    if minutes not in UPDATE_INTERVAL_MINUTES_OPTIONS:
        return DEFAULT_UPDATE_INTERVAL_MINUTES

    return minutes


def get_update_interval_from_options(options: Mapping[str, object]) -> timedelta:
    """Build the polling interval from config-entry options."""
    minutes = normalize_update_interval_minutes(
        options.get(
            CONF_UPDATE_INTERVAL_MINUTES,
            DEFAULT_UPDATE_INTERVAL_MINUTES,
        )
    )
    return timedelta(minutes=minutes)
