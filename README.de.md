# Team Tracker Dashboard

Eine Home-Assistant-Custom-Integration, die vorhandene Team-Tracker-Sensoren ausliest und daraus übersichtliche, dashboardfreundliche Sensoren erstellt.

Die Integration fragt ESPN nicht selbst ab. Sie nutzt den bereits vorhandenen Team-Tracker-Sensor als Datenquelle und bereitet dessen State und Attribute auf.

## Funktionen

- Einrichtung über die Home-Assistant-Oberfläche
- Auswahl eines vorhandenen Team-Tracker-Sensors
- mehrere Teams möglich, indem du die Integration mehrfach hinzufügst
- deutscher Config Flow
- Hauptsensor mit allen Original-Attributen des Team-Tracker-Sensors
- eigene Sensoren für Gegner, Anstoß, Stadion, Ergebnis, Liga, Logos, Spielzeit, Schüsse usw.
- automatische Aktualisierung, sobald sich der Quell-Sensor ändert
- HACS-fähige Ordnerstruktur

## Erzeugte Sensoren

Bei Anzeigename `BVB` entstehen zum Beispiel:

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

Die tatsächlichen Entity IDs können je nach Home Assistant leicht abweichen.

## Installation manuell

1. Kopiere den Ordner `custom_components/team_tracker_dashboard` nach:

   ```text
   /config/custom_components/team_tracker_dashboard
   ```

2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
4. Suche nach **Team Tracker Dashboard**.
5. Wähle deinen vorhandenen Team-Tracker-Sensor aus, zum Beispiel:

   ```text
   sensor.bund_borussia_dortmund
   ```

6. Vergib einen Anzeigenamen, zum Beispiel:

   ```text
   BVB
   ```

## Installation über HACS als benutzerdefiniertes Repository

1. Lade das Repository zu GitHub hoch.
2. Öffne HACS.
3. Öffne **Benutzerdefinierte Repositories**.
4. Füge die Repository-URL hinzu.
5. Kategorie: **Integration**.
6. Installieren und Home Assistant neu starten.

## Beispiel Markdown-Karte

```yaml
card_type: markdown
content: |
  ## {{ states('sensor.bvb_naechstes_spiel') }}

  **Status:** {{ states('sensor.bvb_status') }}  
  **Anstoß:** {{ states('sensor.bvb_anstoss') }}  
  **Stadion:** {{ states('sensor.bvb_stadion') }}  
  **Ergebnis:** {{ states('sensor.bvb_ergebnis') }}
```

## Beispiel Template Card

```yaml
type: custom:mushroom-template-card
primary: "{{ states('sensor.bvb_naechstes_spiel') }}"
secondary: >-
  {{ states('sensor.bvb_status') }} · {{ states('sensor.bvb_stadion') }} · {{ states('sensor.bvb_anstoss_in') }}
icon: mdi:soccer
entity: sensor.bvb_naechstes_spiel
```

## Beispiel Automation

```yaml
alias: BVB Spiel startet bald
trigger:
  - platform: time
    at: sensor.bvb_anstoss
condition: []
action:
  - service: notify.mobile_app_iphone
    data:
      message: >
        {{ states('sensor.bvb_naechstes_spiel') }} startet bald im
        {{ states('sensor.bvb_stadion') }}.
mode: single
```

## Hinweise

- Der Quell-Sensor muss bereits existieren.
- Die Integration funktioniert mit Sensoren, die typische Team-Tracker-Attribute enthalten, zum Beispiel `team_name`, `opponent_name`, `event_name`, `date`, `venue` oder `league_name`.
- Der Hauptsensor enthält zusätzlich alle Original-Attribute des Quell-Sensors.

