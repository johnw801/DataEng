# Data Dictionary

Dieser Abschnitt bietet einen Überblick über die verwendeten Datenstrukturen.

### sensor-data (Kafka Topic)
| Feld | Typ            | Beschreibung               | Einheit |
|------|----------------|----------------------------|---------|
|sensor_id| object         | ID des Sensors             | -       |
|temperature| float          | Gemessene Wassertemperatur | °C      |
|salinity| float          | Gemessener Salzgehalt      | PSU     |
|timestamp| datetime (UTC) | Zeitstempel der Messung    | UTC     |

### Cassandra table – sensor_aggregates

| Feld | Typ           | Beschreibung |
|------|---------------|-------------|
|sensor_id| object        |ID des Sensors|
|window_start | datetime (UTC) |Startzeit des Aggregationsfensters|
|   window_end   | datetime (UTC) |Endzeit des Aggregationsfensters          |
|avg_temperature      | float         |Durchschnittstemperatur           |
|min_temperature      | float               |Minimaltemperatur             |
|max_temperature      |  float              |Maximaltemperatur             |
|avg_salinity      |    float            |Durchschnittlicher Salzgehalt             |

### Cassandra table – sensor_anomalies

| Feld        | Typ            | Beschreibung                   |
|-------------|----------------|--------------------------------|
| sensor_id   | object         | ID des Sensors                 |
| timestamp   | datetime (UTC) | Zeitpunkt der Anomalie         |
| temperature | float          | Auffälliger Temperaturmesswert |
| salinity    | float          | Auffälliger Salzgehaltmesswert |
