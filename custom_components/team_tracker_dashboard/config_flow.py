"""Config flow for Team Tracker Dashboard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers import selector

from .const import CONF_DISPLAY_NAME, CONF_SOURCE_ENTITY, DEFAULT_NAME, DOMAIN


TEAM_TRACKER_REQUIRED_COMBINATIONS = (
    ("event_name", "team_name", "opponent_name"),
    ("event_name", "team_long_name", "opponent_long_name"),
    ("event_name", "team_abbr", "opponent_abbr"),
    ("sport", "league", "team_abbr", "opponent_abbr"),
)

TEAM_TRACKER_HINT_ATTRIBUTES = {
    "event_name",
    "team_name",
    "team_long_name",
    "opponent_name",
    "opponent_long_name",
    "team_abbr",
    "opponent_abbr",
    "sport",
    "league",
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


def _state_looks_like_team_tracker(state: State | None) -> bool:
    """Return true if a state has attributes typical for Team Tracker."""
    if state is None or state.domain != "sensor":
        return False

    attributes = state.attributes
    if not any(attr in attributes for attr in TEAM_TRACKER_HINT_ATTRIBUTES):
        return False

    return any(
        all(attr in attributes for attr in required_attributes)
        for required_attributes in TEAM_TRACKER_REQUIRED_COMBINATIONS
    )


def _looks_like_team_tracker(hass: HomeAssistant, source_entity: str) -> bool:
    """Return true if the source entity has attributes typical for Team Tracker."""
    return _state_looks_like_team_tracker(hass.states.get(source_entity))


def _team_tracker_entity_options(
    hass: HomeAssistant, current_entity: str | None = None
) -> list[dict[str, str]]:
    """Return selectable Team Tracker sensor options only."""
    options: list[dict[str, str]] = []
    seen: set[str] = set()

    for state in hass.states.async_all():
        if not _state_looks_like_team_tracker(state):
            continue

        friendly_name = state.attributes.get("friendly_name") or state.name
        team_name = state.attributes.get("team_name") or state.attributes.get("team_long_name")
        opponent_name = state.attributes.get("opponent_name") or state.attributes.get(
            "opponent_long_name"
        )

        if team_name and opponent_name:
            label = f"{team_name} vs. {opponent_name} ({state.entity_id})"
        else:
            label = f"{friendly_name} ({state.entity_id})"

        options.append({"value": state.entity_id, "label": str(label)})
        seen.add(state.entity_id)

    if current_entity and current_entity not in seen:
        current_state = hass.states.get(current_entity)
        if current_state is not None:
            friendly_name = current_state.attributes.get("friendly_name") or current_state.name
            options.append(
                {
                    "value": current_entity,
                    "label": f"{friendly_name} ({current_entity})",
                }
            )

    return sorted(options, key=lambda option: option["label"].casefold())


def _source_entity_selector(
    hass: HomeAssistant, current_entity: str | None = None
) -> selector.SelectSelector:
    """Build a dropdown selector containing only Team Tracker sensors."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=_team_tracker_entity_options(hass, current_entity),
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


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
            source_key: _source_entity_selector(hass, source_entity),
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
