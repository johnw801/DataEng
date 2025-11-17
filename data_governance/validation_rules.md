# Data Validation Rules

Dieser Abschnitt erläutert die bestehende Datenvalidierungen.

**Eingangsvalidierung (Spark)**
- Temperatur darf nicht negativ sein (temperatur < 0 → verworfen)
- Salzgehalt darf nicht negativ sein (salinity < 0 → verworfen)
- sensor_id muss vorhanden, nicht leer und nicht "0" sein

Ungültige Datensätze werden verworfen, bevor Aggregationen erfolgen.

**Verarbeitungsregeln (Spark)**

- Aggregationen basieren auf validierten Daten (siehe Eingangsvalidierung)
- Anomalien gelten bei:
  - Temperatur < 2.5°C oder > 9.5°C
  - Salzgehalt < 31 PSU oder > 34 PSU
- Fehlerhafte oder unvollständige Nachrichten werden geloggt und verworfen