"""Config flow for Team Tracker Dashboard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import CONF_DISPLAY_NAME, CONF_SOURCE_ENTITY, DEFAULT_NAME, DOMAIN


TEAM_TRACKER_HINT_ATTRIBUTES = {
    "event_name",
    "team_name",
    "team_long_name",
    "opponent_name",
    "opponent_long_name",
    "league_name",
}


def _suggest_name(hass: HomeAssistant, source_entity: str | None) -> str:
    """Suggest a display name from the selected source entity."""
    if not source_entity:
        return DEFAULT_NAME

    state = hass.states.get(source_entity)
    if state is not None:
        friendly_name = state.attributes.get("friendly_name")
        team_name = state.attributes.get("team_name") or state.attributes.get("team_long_name")
        if team_name:
            return str(team_name)
        if friendly_name:
            return str(friendly_name)

    return source_entity.split(".", 1)[-1].replace("_", " ").title()


def _looks_like_team_tracker(hass: HomeAssistant, source_entity: str) -> bool:
    """Return true if the source entity has attributes typical for Team Tracker."""
    state = hass.states.get(source_entity)
    if state is None:
        return False

    return any(attr in state.attributes for attr in TEAM_TRACKER_HINT_ATTRIBUTES)


def _schema(hass: HomeAssistant, user_input: dict[str, Any] | None = None) -> vol.Schema:
    """Build config/options schema."""
    source_entity = None
    display_name = DEFAULT_NAME

    if user_input:
        source_entity = user_input.get(CONF_SOURCE_ENTITY)
        display_name = user_input.get(CONF_DISPLAY_NAME) or _suggest_name(hass, source_entity)

    source_key = (
        vol.Required(CONF_SOURCE_ENTITY, default=source_entity)
        if source_entity
        else vol.Required(CONF_SOURCE_ENTITY)
    )

    return vol.Schema(
        {
            source_key: selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_DISPLAY_NAME, default=display_name): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
        }
    )


class TeamTrackerDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Team Tracker Dashboard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            display_name = user_input.get(CONF_DISPLAY_NAME) or _suggest_name(
                self.hass, source_entity
            )

            if self.hass.states.get(source_entity) is None:
                errors["base"] = "entity_not_found"
            elif not _looks_like_team_tracker(self.hass, source_entity):
                errors["base"] = "not_team_tracker"
            else:
                await self.async_set_unique_id(source_entity)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=display_name,
                    data={
                        CONF_SOURCE_ENTITY: source_entity,
                        CONF_DISPLAY_NAME: display_name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(self.hass, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return TeamTrackerDashboardOptionsFlow(config_entry)


class TeamTrackerDashboardOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Team Tracker Dashboard."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}

        current = dict(self._config_entry.data)
        current.update(dict(self._config_entry.options))

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            display_name = user_input.get(CONF_DISPLAY_NAME) or _suggest_name(
                self.hass, source_entity
            )

            if self.hass.states.get(source_entity) is None:
                errors["base"] = "entity_not_found"
            elif not _looks_like_team_tracker(self.hass, source_entity):
                errors["base"] = "not_team_tracker"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SOURCE_ENTITY: source_entity,
                        CONF_DISPLAY_NAME: display_name,
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.hass, user_input or current),
            errors=errors,
        )
