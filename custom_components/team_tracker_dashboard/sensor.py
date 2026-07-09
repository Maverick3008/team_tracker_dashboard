"""Sensor platform for Team Tracker Dashboard."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import CONF_DISPLAY_NAME, CONF_SOURCE_ENTITY, DOMAIN

_SOURCE_BAD_STATES = {STATE_UNKNOWN, STATE_UNAVAILABLE}


@dataclass(frozen=True, kw_only=True)
class TeamTrackerDashboardSensorDescription(SensorEntityDescription):
    """Description for Team Tracker Dashboard sensors."""

    value_fn: Callable[[HomeAssistant, str], Any]
    attr_fn: Callable[[HomeAssistant, str], dict[str, Any]] | None = None
    picture_attr: str | None = None


def _source_state(hass: HomeAssistant, source_entity: str):
    """Return the current source state object."""
    return hass.states.get(source_entity)


def _source_attrs(hass: HomeAssistant, source_entity: str) -> dict[str, Any]:
    """Return the source entity attributes."""
    state = _source_state(hass, source_entity)
    return dict(state.attributes) if state is not None else {}


def _attr(hass: HomeAssistant, source_entity: str, attr_name: str, default: Any = None) -> Any:
    """Read one attribute from the Team Tracker source entity."""
    return _source_attrs(hass, source_entity).get(attr_name, default)


def _state(hass: HomeAssistant, source_entity: str) -> str | None:
    """Read the state from the Team Tracker source entity."""
    state = _source_state(hass, source_entity)
    if state is None or state.state in _SOURCE_BAD_STATES:
        return None
    return state.state


def _parse_datetime(value: Any) -> datetime | None:
    """Parse an ESPN/Home Assistant datetime value to a timezone-aware datetime."""
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        parsed = dt_util.parse_datetime(text)

    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


def _home_away_attrs(hass: HomeAssistant, source_entity: str) -> dict[str, Any]:
    """Return normalized home/away values based on Team Tracker attributes."""
    attrs = _source_attrs(hass, source_entity)
    team_is_home = attrs.get("team_homeaway") == "home"
    team_prefix = "team"
    opponent_prefix = "opponent"

    home_prefix = team_prefix if team_is_home else opponent_prefix
    away_prefix = opponent_prefix if team_is_home else team_prefix

    return {
        "home_name": attrs.get(f"{home_prefix}_long_name") or attrs.get(f"{home_prefix}_name"),
        "away_name": attrs.get(f"{away_prefix}_long_name") or attrs.get(f"{away_prefix}_name"),
        "home_abbr": attrs.get(f"{home_prefix}_abbr"),
        "away_abbr": attrs.get(f"{away_prefix}_abbr"),
        "home_score": attrs.get(f"{home_prefix}_score"),
        "away_score": attrs.get(f"{away_prefix}_score"),
        "home_logo": attrs.get(f"{home_prefix}_logo"),
        "away_logo": attrs.get(f"{away_prefix}_logo"),
    }


def _event_name(hass: HomeAssistant, source_entity: str) -> str | None:
    """Build a readable event name."""
    normalized = _home_away_attrs(hass, source_entity)
    home = normalized.get("home_name") or normalized.get("home_abbr")
    away = normalized.get("away_name") or normalized.get("away_abbr")
    if home and away:
        return f"{home} - {away}"

    return _attr(hass, source_entity, "event_name")


def _opponent(hass: HomeAssistant, source_entity: str) -> str | None:
    """Return opponent name."""
    return _attr(hass, source_entity, "opponent_long_name") or _attr(
        hass, source_entity, "opponent_name"
    )


def _result(hass: HomeAssistant, source_entity: str) -> str | None:
    """Return result in home-away order."""
    normalized = _home_away_attrs(hass, source_entity)
    home_score = normalized.get("home_score")
    away_score = normalized.get("away_score")
    if home_score is None or away_score is None:
        return None
    return f"{home_score}:{away_score}"


def _status_text(hass: HomeAssistant, source_entity: str) -> str | None:
    """Return a readable status text."""
    source_status = _state(hass, source_entity)
    if source_status is None:
        return None

    status_map = {
        "PRE": "Vor dem Spiel",
        "IN": "Live",
        "POST": "Beendet",
        "STATUS_SCHEDULED": "Geplant",
        "STATUS_IN_PROGRESS": "Live",
        "STATUS_FINAL": "Beendet",
    }
    return status_map.get(source_status, source_status)


def _main_attributes(hass: HomeAssistant, source_entity: str) -> dict[str, Any]:
    """Expose all original and normalized source attributes on the main sensor."""
    state = _source_state(hass, source_entity)
    attrs = _source_attrs(hass, source_entity)
    normalized = _home_away_attrs(hass, source_entity)

    return {
        "source_entity": source_entity,
        "source_state": state.state if state is not None else None,
        "status_text": _status_text(hass, source_entity),
        "event_display_name": _event_name(hass, source_entity),
        "result_display": _result(hass, source_entity),
        **normalized,
        **attrs,
    }


def _score_attr(attr_name: str) -> Callable[[HomeAssistant, str], Any]:
    """Return a value function for score/stat attributes."""

    def _value(hass: HomeAssistant, source_entity: str) -> Any:
        return _attr(hass, source_entity, attr_name)

    return _value


def _timestamp_attr(attr_name: str) -> Callable[[HomeAssistant, str], Any]:
    """Return a value function for timestamp attributes."""

    def _value(hass: HomeAssistant, source_entity: str) -> datetime | None:
        return _parse_datetime(_attr(hass, source_entity, attr_name))

    return _value


SENSOR_DESCRIPTIONS: tuple[TeamTrackerDashboardSensorDescription, ...] = (
    TeamTrackerDashboardSensorDescription(
        key="next_event",
        name="Nächstes Spiel",
        icon="mdi:soccer",
        value_fn=_event_name,
        attr_fn=_main_attributes,
    ),
    TeamTrackerDashboardSensorDescription(
        key="status",
        name="Status",
        icon="mdi:information-outline",
        value_fn=_status_text,
    ),
    TeamTrackerDashboardSensorDescription(
        key="opponent",
        name="Gegner",
        icon="mdi:account-group-outline",
        value_fn=_opponent,
    ),
    TeamTrackerDashboardSensorDescription(
        key="kickoff",
        name="Anstoß",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_timestamp_attr("date"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="kickoff_in",
        name="Anstoß in",
        icon="mdi:timer-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "kickoff_in"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="venue",
        name="Stadion",
        icon="mdi:stadium",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "venue"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="location",
        name="Ort",
        icon="mdi:map-marker-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "location"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="result",
        name="Ergebnis",
        icon="mdi:counter",
        value_fn=_result,
    ),
    TeamTrackerDashboardSensorDescription(
        key="clock",
        name="Spielzeit",
        icon="mdi:clock-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "clock"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="league",
        name="Liga",
        icon="mdi:trophy-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "league_name"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="season",
        name="Saison",
        icon="mdi:calendar-range",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "season"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="team_score",
        name="Team Tore",
        icon="mdi:soccer-field",
        value_fn=_score_attr("team_score"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="opponent_score",
        name="Gegner Tore",
        icon="mdi:soccer-field",
        value_fn=_score_attr("opponent_score"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="team_shots_on_target",
        name="Team Schüsse aufs Tor",
        icon="mdi:target",
        value_fn=_score_attr("team_shots_on_target"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="opponent_shots_on_target",
        name="Gegner Schüsse aufs Tor",
        icon="mdi:target",
        value_fn=_score_attr("opponent_shots_on_target"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="team_total_shots",
        name="Team Schüsse gesamt",
        icon="mdi:soccer",
        value_fn=_score_attr("team_total_shots"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="opponent_total_shots",
        name="Gegner Schüsse gesamt",
        icon="mdi:soccer",
        value_fn=_score_attr("opponent_total_shots"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="tv_network",
        name="TV Sender",
        icon="mdi:television-classic",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "tv_network"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="event_url",
        name="Spiel URL",
        icon="mdi:link-variant",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "event_url"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="team_logo",
        name="Team Logo",
        icon="mdi:image-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "team_logo"),
        picture_attr="team_logo",
    ),
    TeamTrackerDashboardSensorDescription(
        key="opponent_logo",
        name="Gegner Logo",
        icon="mdi:image-outline",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "opponent_logo"),
        picture_attr="opponent_logo",
    ),
    TeamTrackerDashboardSensorDescription(
        key="last_update",
        name="Letzte Aktualisierung",
        icon="mdi:update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_timestamp_attr("last_update"),
    ),
    TeamTrackerDashboardSensorDescription(
        key="api_message",
        name="API Meldung",
        icon="mdi:api",
        value_fn=lambda hass, source_entity: _attr(hass, source_entity, "api_message"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Team Tracker Dashboard sensors."""
    config = dict(entry.data)
    config.update(dict(entry.options))

    source_entity = config[CONF_SOURCE_ENTITY]
    display_name = config[CONF_DISPLAY_NAME]

    async_add_entities(
        TeamTrackerDashboardSensor(entry, source_entity, display_name, description)
        for description in SENSOR_DESCRIPTIONS
    )


class TeamTrackerDashboardSensor(SensorEntity):
    """A sensor that mirrors and formats Team Tracker data."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        entry: ConfigEntry,
        source_entity: str,
        display_name: str,
        description: TeamTrackerDashboardSensorDescription,
    ) -> None:
        """Initialize sensor."""
        self.entity_description = description
        self._entry = entry
        self._source_entity = source_entity
        self._display_name = display_name
        self._attr_name = f"{display_name} {description.name}"
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    async def async_added_to_hass(self) -> None:
        """Register update listener for the source entity."""
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._source_entity],
                self._async_source_changed,
            )
        )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source entity changes."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if source entity is available."""
        source = _source_state(self.hass, self._source_entity)
        return source is not None and source.state not in _SOURCE_BAD_STATES

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.hass, self._source_entity)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        attributes: dict[str, Any] = {"source_entity": self._source_entity}
        if self.entity_description.attr_fn is not None:
            attributes.update(self.entity_description.attr_fn(self.hass, self._source_entity))
        return attributes

    @property
    def entity_picture(self) -> str | None:
        """Return dynamic entity picture for logo sensors."""
        if not self.entity_description.picture_attr:
            return None
        value = _attr(self.hass, self._source_entity, self.entity_description.picture_attr)
        return str(value) if value else None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._display_name,
            "manufacturer": "Team Tracker Dashboard",
            "model": "Team Tracker Helper",
        }
        event_url = _attr(self.hass, self._source_entity, "event_url")
        if event_url:
            info["configuration_url"] = str(event_url)
        return info
