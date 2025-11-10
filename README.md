# DataEng – Echtzeit Data Engineering Pipeline

Dieses Projekt demonstriert eine vollständige **Streaming Data Pipeline** mit **Kafka**, **Apache Spark Structured Streaming** und **Cassandra**. Ozeanographische Sensordaten werden simuliert, über Kafka gestreamt, von Spark verarbeitet und in Cassandra gespeichert.

---
## Architekturüberblick

### Datenfluss:
Sensor-Simulator → Kafka → Spark Structured Streaming → Cassandra

Sensor-Simulator sendet fortlaufend JSON-Messwerte (Temperatur, Salzgehalt) von drei simulierten Sensoren an Kafka.

Kafka dient als Message-Broker für den Echtzeit-Datenstrom.

Spark Structured Streaming liest kontinuierlich die Daten aus Kafka, führt Berechnungen und Aggregationen durch:

Berechnung von Durchschnitts-, Minimal- und Maximalwerten pro Sensor in 30-Sekunden-Zeitfenstern.

Erkennung von Anomalien, wenn Temperaturwerte außerhalb des normalen Bereichs ( <2.5 °C oder >9.5 °C) liegen.

Cassandra speichert sowohl aggregierte Sensordaten als auch erkannte Anomalien persistent in den Tabellen sensor_aggregates und sensor_anomalies.

---

## Voraussetzungen

Vor dem Start sollten folgende Tools installiert sein:

| Komponente            | Empfehlung                  | Hinweis                                                          |
| --------------------- | --------------------------- | ---------------------------------------------------------------- |
| **Docker Desktop**    | ≥ 4.x                       | Empfohlen für lokale Entwicklung und Containerverwaltung         |            
| **Java JDK 11**       | Zwingend erforderlich       | Spark benötigt Java 11 zur Laufzeit                              |
| **Python 3.9+**       | Optional                    | Nur nötig, wenn du den Code außerhalb von Docker testen möchtest |

---

## Setup & Ausführung

### 1️. Projekt starten

```bash
docker compose up --build -d
```

Alle Container werden gebaut und gestartet. Healthchecks sorgen dafür, dass Services in der richtigen Reihenfolge initialisiert werden.

---

### 2. Cassandra initialisieren

Bei der **erstmaligen Initialisierung**:

```bash
docker exec -it cassandra cqlsh -u cassandra -p cassandra -f /init.cql
```

Alternativ können auch die SQL-Dateien manuell ausgeführt werden:

```bash
docker exec -it cassandra cqlsh -u cassandra -p cassandra -f /init.sql
```

Optional kann der Cassandra Standard-Superuser entfernt werden:

```bash
docker exec -it cassandra cqlsh -u cassandra -p cassandra -f /deletesuperuser.cql
```

---

### 3. Services überwachen
Für die Überwachung der Services wird Docker Desktop empfohlen.

* **Alternativ:**
* **Logs anzeigen:**

  ```bash
  docker logs -f sensor-simulator
  docker logs -f spark-submit-job
  ```
* **Cassandra-Client öffnen:**

  ```bash
  docker exec -it cassandra cqlsh
  ```

---

## Netzwerksicherheit

* Standardmäßig sind **alle externen Ports deaktiviert** (außer Cassandra-Port `9042` für PyCharm).
* Ports können bei Bedarf in `docker-compose.yml` aktiviert werden.
* Kafka und Spark Web-UIs sind **optional** (siehe unten).

---

## Optionale Komponenten

### Kafka Web UI aktivieren

```yaml
# In docker-compose.yml entkommentieren:
# kafka-ui:
#   image: provectuslabs/kafka-ui:latest
#   ports:
#     - 8085:8080
```

Zugriff anschließend über [http://localhost:8085](http://localhost:8085)

### Spark UI aktivieren

```yaml
# spark-master:
#   ports:
#     - 7070:7070
# spark-worker:
#   ports:
#     - 8081:8081
```

---

## Zugangsdaten & Sicherheit

* Standardpasswort für Cassandra:

  ```
  initialespasswortbitteaendern
  ```

  → **Bitte unbedingt ändern!**

* Kafka Log-Retention:

  ```
  24 Stunden (Datenschutz-konform)
  ```

* `.env` enthält sensible Variablen (`CASSANDRA_USER`, `CASSANDRA_PASSWORD`)

---

## Skalierbarkeit

Mehr Rechenknoten oder Broker können einfach hinzugefügt werden:

```yaml
# Beispiel: zusätzlicher Spark Worker
spark-worker-2:
  image: bde2020/spark-worker:3.3.0-hadoop3.3
  environment:
    - SPARK_MASTER=spark://spark-master:7077
  networks:
    - data-pipeline
```

Ebenso können zusätzliche Kafka-Broker definiert werden.

---

## Datenfluss

```text
[Sensoren → Kafka → Spark Streaming → Cassandra]
```

* Sensor simuliert Messwerte (JSON)
* Kafka verteilt Daten an Spark
* Spark aggregiert & erkennt Anomalien
* Cassandra speichert Ergebnisse dauerhaft

---

## Hinweise

* **Docker Desktop wird dringend empfohlen**, da es alle benötigten Dienste lokal bündelt.
* **Java JDK 11 ist zwingend erforderlich**, da Spark darauf basiert.
  Überprüfe die Installation mit:

  ```bash
  java -version
  # Ausgabe sollte ähnlich lauten: openjdk version "11.0.x"
  ```


## Autor

Erstellt im Rahmen des Moduls **Data Engineering**
von J.W.
