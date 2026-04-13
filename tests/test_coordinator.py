"""Unit tests for the Pluxee Portugal coordinator helpers."""

from datetime import timedelta

from custom_components.pluxee_pt.const import (
    CONF_UPDATE_INTERVAL_MINUTES,
    get_update_interval_from_options,
)


def test_get_config_entry_update_interval_defaults_to_60_minutes() -> None:
    """Existing entries without options should keep the default cadence."""
    assert get_update_interval_from_options({}) == timedelta(minutes=60)


def test_get_config_entry_update_interval_uses_selected_option() -> None:
    """The configured options value should drive the coordinator interval."""
    assert get_update_interval_from_options(
        {CONF_UPDATE_INTERVAL_MINUTES: 60}
    ) == timedelta(minutes=60)
