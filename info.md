# Team Tracker Dashboard

Creates dashboard-friendly Home Assistant sensors from an existing Team Tracker sensor.

The integration does not fetch ESPN data itself. It reads an existing Team Tracker entity and creates clean sensors for next event, opponent, kickoff, venue, result, logos, game clock, shots, and more.


Version 1.0.2 stores the updated logo and icon in Home Assistant’s local `brand/` folder and keeps the kickoff days sensor.
