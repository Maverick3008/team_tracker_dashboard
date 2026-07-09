# Team Tracker Dashboard

A Home Assistant custom integration that reads existing Team Tracker sensors and creates clean, dashboard-friendly sensors from their state and attributes.

This integration does not query ESPN directly. It uses your existing Team Tracker sensor as the source and formats its values for dashboards, automations, and notifications.

## Features

- UI setup via Home Assistant config flow
- Select an existing Team Tracker sensor
- Add multiple teams by adding the integration multiple times
- German and English setup texts
- Main sensor with all original Team Tracker attributes
- Dedicated sensors for opponent, kickoff, venue, result, league, logos, game clock, shots, and more
- Updates automatically when the source entity changes
- HACS-ready structure

## Created sensors

With display name `BVB`, examples are:

- `sensor.bvb_naechstes_spiel`
- `sensor.bvb_status`
- `sensor.bvb_gegner`
- `sensor.bvb_anstoss`
- `sensor.bvb_anstoss_in`
- `sensor.bvb_stadion`
- `sensor.bvb_ort`
- `sensor.bvb_ergebnis`
- `sensor.bvb_spielzeit`
- `sensor.bvb_liga`
- `sensor.bvb_saison`
- `sensor.bvb_team_tore`
- `sensor.bvb_gegner_tore`
- `sensor.bvb_team_logo`
- `sensor.bvb_gegner_logo`
- `sensor.bvb_letzte_aktualisierung`

Actual entity IDs may differ slightly depending on Home Assistant's entity registry.

## Manual installation

1. Copy `custom_components/team_tracker_dashboard` to:

   ```text
   /config/custom_components/team_tracker_dashboard
   ```

2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Team Tracker Dashboard**.
5. Select your existing Team Tracker sensor, for example:

   ```text
   sensor.bund_borussia_dortmund
   ```

6. Enter a display name, for example:

   ```text
   BVB
   ```

## HACS custom repository installation

1. Upload this repository to GitHub.
2. Open HACS.
3. Open **Custom repositories**.
4. Add the repository URL.
5. Category: **Integration**.
6. Install and restart Home Assistant.

## Example Markdown card

```yaml
card_type: markdown
content: |
  ## {{ states('sensor.bvb_naechstes_spiel') }}

  **Status:** {{ states('sensor.bvb_status') }}  
  **Kickoff:** {{ states('sensor.bvb_anstoss') }}  
  **Venue:** {{ states('sensor.bvb_stadion') }}  
  **Result:** {{ states('sensor.bvb_ergebnis') }}
```

## Example Mushroom Template Card

```yaml
type: custom:mushroom-template-card
primary: "{{ states('sensor.bvb_naechstes_spiel') }}"
secondary: >-
  {{ states('sensor.bvb_status') }} · {{ states('sensor.bvb_stadion') }} · {{ states('sensor.bvb_anstoss_in') }}
icon: mdi:soccer
entity: sensor.bvb_naechstes_spiel
```

## Example automation

```yaml
alias: BVB match starts soon
trigger:
  - platform: time
    at: sensor.bvb_anstoss
condition: []
action:
  - service: notify.mobile_app_iphone
    data:
      message: >
        {{ states('sensor.bvb_naechstes_spiel') }} starts soon at
        {{ states('sensor.bvb_stadion') }}.
mode: single
```

## Notes

- The source sensor must already exist.
- The integration expects typical Team Tracker attributes such as `team_name`, `opponent_name`, `event_name`, `date`, `venue`, or `league_name`.
- The main sensor exposes all original source attributes as attributes.

