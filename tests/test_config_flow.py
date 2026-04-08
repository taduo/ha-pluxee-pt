"""Tests for the Pluxee Portugal config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pluxee_pt.const import CONF_NIF, DOMAIN


pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_user_step_normalizes_nif_and_preserves_password(hass) -> None:
    """User setup should normalize the NIF before creating the entry."""
    with patch(
        "custom_components.pluxee_pt.config_flow.async_validate_input",
        AsyncMock(return_value={"title": "Pluxee PT 6789"}),
    ) as mock_validate:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NIF: " 123456789 ",
                CONF_PASSWORD: " secret ",
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Pluxee PT 6789"
    assert result["data"] == {
        CONF_NIF: "123456789",
        CONF_PASSWORD: " secret ",
    }
    mock_validate.assert_awaited_once_with(
        hass,
        {
            CONF_NIF: "123456789",
            CONF_PASSWORD: " secret ",
        },
    )


async def test_user_step_rejects_invalid_nif_before_network_call(hass) -> None:
    """Malformed NIF values should fail before credentials are validated online."""
    with patch(
        "custom_components.pluxee_pt.config_flow.async_validate_input",
        AsyncMock(),
    ) as mock_validate:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NIF: "12 34",
                CONF_PASSWORD: "secret",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_nif_format"}
    mock_validate.assert_not_awaited()


async def test_reauth_uses_normalized_nif_for_same_account(hass) -> None:
    """Reauth should treat whitespace-only NIF differences as the same account."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Pluxee PT 6789",
        data={
            CONF_NIF: "123456789",
            CONF_PASSWORD: "old-password",
        },
        unique_id="123456789",
    )
    entry.add_to_hass(hass)

    with (
        patch.object(
            hass.config_entries,
            "async_reload",
            AsyncMock(return_value=True),
        ) as mock_reload,
        patch(
            "custom_components.pluxee_pt.config_flow.async_validate_input",
            AsyncMock(return_value={"title": "Pluxee PT 6789"}),
        ) as mock_validate,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NIF: " 123456789 ",
                CONF_PASSWORD: " new-password ",
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {
        CONF_NIF: "123456789",
        CONF_PASSWORD: " new-password ",
    }
    assert entry.unique_id == "123456789"
    mock_validate.assert_awaited_once_with(
        hass,
        {
            CONF_NIF: "123456789",
            CONF_PASSWORD: " new-password ",
        },
    )
    mock_reload.assert_awaited_once_with(entry.entry_id)
