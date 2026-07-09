"""Constants for Team Tracker Dashboard."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "team_tracker_dashboard"
NAME = "Team Tracker Dashboard"
VERSION = "0.1.0"

CONF_SOURCE_ENTITY = "source_entity"
CONF_DISPLAY_NAME = "display_name"

DEFAULT_NAME = "Team Tracker Dashboard"
PLATFORMS = [Platform.SENSOR]
