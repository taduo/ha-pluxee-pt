"""Config flow for the Pluxee Portugal integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .client import (
    PluxeePtAuthError,
    PluxeePtClient,
    PluxeePtConnectionError,
    PluxeePtParseError,
    title_for_nif,
)
from .const import (
    CONF_NIF,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    UPDATE_INTERVAL_OPTION_LABELS,
    normalize_update_interval_minutes,
)

_LOGGER = logging.getLogger(__name__)


async def async_validate_input(
    hass: HomeAssistant,
    user_input: dict[str, str],
) -> dict[str, str]:
    """Validate the user credentials."""
    session = async_get_clientsession(hass)
    client = PluxeePtClient(
        session,
        user_input[CONF_NIF],
        user_input[CONF_PASSWORD],
    )
    await client.async_fetch_balance()
    return {"title": title_for_nif(user_input[CONF_NIF])}


class PluxeePtConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pluxee Portugal."""

    VERSION = 1

    _reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self,
        user_input: dict[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self.async_set_unique_id(user_input[CONF_NIF])
                self._abort_if_unique_id_configured()

                info = await async_validate_input(self.hass, user_input)
            except PluxeePtAuthError:
                errors["base"] = "invalid_auth"
            except PluxeePtConnectionError:
                errors["base"] = "cannot_connect"
            except PluxeePtParseError:
                errors["base"] = "cannot_parse"
            except Exception:
                _LOGGER.exception("Unexpected error while validating Pluxee credentials")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, str],
    ) -> config_entries.ConfigFlowResult:
        """Handle a reauthentication request."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm(
            {
                CONF_NIF: entry_data[CONF_NIF],
            }
        )

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Confirm updated credentials during reauthentication."""
        errors: dict[str, str] = {}
        entry = self._reauth_entry

        if entry is None:
            return self.async_abort(reason="unknown")

        if user_input is not None and CONF_PASSWORD in user_input:
            data = {
                CONF_NIF: user_input[CONF_NIF],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            try:
                await self.async_set_unique_id(data[CONF_NIF])
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                await async_validate_input(self.hass, data)
            except PluxeePtAuthError:
                errors["base"] = "invalid_auth"
            except PluxeePtConnectionError:
                errors["base"] = "cannot_connect"
            except PluxeePtParseError:
                errors["base"] = "cannot_parse"
            except Exception:
                _LOGGER.exception("Unexpected error while reauthenticating Pluxee credentials")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        defaults = user_input or {CONF_NIF: entry.data[CONF_NIF]}
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self._build_schema(defaults),
            errors=errors,
            description_placeholders={"account": entry.title},
        )

    @staticmethod
    def _build_schema(defaults: dict[str, str] | None) -> vol.Schema:
        """Build the flow schema."""
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(CONF_NIF, default=defaults.get(CONF_NIF, "")): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        autocomplete="username",
                    )
                ),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD,
                        autocomplete="current-password",
                    )
                ),
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PluxeePtOptionsFlowHandler()


class PluxeePtOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle the options flow for Pluxee Portugal."""

    async def async_step_init(
        self,
        user_input: dict[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_UPDATE_INTERVAL_MINUTES: normalize_update_interval_minutes(
                        user_input[CONF_UPDATE_INTERVAL_MINUTES]
                    )
                }
            )

        current_interval = normalize_update_interval_minutes(
            self.config_entry.options.get(
                CONF_UPDATE_INTERVAL_MINUTES,
                DEFAULT_UPDATE_INTERVAL_MINUTES,
            )
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL_MINUTES,
                        default=str(current_interval),
                    ): vol.In(UPDATE_INTERVAL_OPTION_LABELS)
                }
            ),
        )
