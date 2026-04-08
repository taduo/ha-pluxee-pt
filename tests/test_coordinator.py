"""Unit tests for the Pluxee Portugal coordinator helpers."""

from datetime import timedelta
from types import SimpleNamespace

from custom_components.pluxee_pt.const import CONF_UPDATE_INTERVAL_MINUTES
from custom_components.pluxee_pt.coordinator import get_config_entry_update_interval


def test_get_config_entry_update_interval_defaults_to_30_minutes() -> None:
    """Existing entries without options should keep the default cadence."""
    entry = SimpleNamespace(options={})

    assert get_config_entry_update_interval(entry) == timedelta(minutes=30)


def test_get_config_entry_update_interval_uses_selected_option() -> None:
    """The configured options value should drive the coordinator interval."""
    entry = SimpleNamespace(options={CONF_UPDATE_INTERVAL_MINUTES: 60})

    assert get_config_entry_update_interval(entry) == timedelta(minutes=60)
