"""Config flow for Tonal Companion."""

from __future__ import annotations

from typing import Any, Mapping

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import TonalApiError, TonalClient
from .const import CONF_HOST, DEFAULT_HOST, DOMAIN


class TonalCompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Tonal Companion setup and reauthentication."""

    VERSION = 1

    def __init__(self) -> None:
        self._host = DEFAULT_HOST

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].rstrip("/")
            client = TonalClient(host)
            try:
                await self.hass.async_add_executor_job(client.health)
            except TonalApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Tonal", data={CONF_HOST: host})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=DEFAULT_HOST): str}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Start reauthentication from the HA integration UI/app."""
        self._host = entry_data[CONF_HOST]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = TonalClient(self._host)
            try:
                await self.hass.async_add_executor_job(
                    client.authenticate,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
            except TonalApiError:
                errors["base"] = "invalid_auth"
            else:
                return self.async_update_reload_and_abort(self._get_reauth_entry())

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password")
                    ),
                }
            ),
            errors=errors,
        )
