# Changelog

## 1.0.0

- Added original, rights-safe brand images (`brand`, `icon`, and `logo`).
- Added new sensor `Anstoß in Tagen` / kickoff days based on the Team Tracker `date` attribute.
- The kickoff-days sensor refreshes hourly so the day count stays current.
- Updated manifest and constants to version 1.0.0.

## 0.1.1

- The source selector now only lists sensors that look like Team Tracker sensors.
- Removed the Home Assistant helper integration hint from the manifest.
- Renamed the device model from "Team Tracker Helper" to "Team Tracker Dashboard".

## 0.1.0

- Initial release
- UI config flow
- Options flow for source sensor and display name
- Main sensor with all source attributes
- Dedicated sensors for opponent, kickoff, venue, result, status, league, logos, shots, and last update
- German and English translations
- HACS-ready structure
