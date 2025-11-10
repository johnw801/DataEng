# DataEng – Echtzeit Data Engineering Pipeline

Dieses Projekt demonstriert eine vollständige **Streaming Data Pipeline** mit **Kafka**, **Apache Spark Structured Streaming** und **Cassandra**. Ozeanographische Sensordaten werden simuliert, über Kafka gestreamt, von Spark verarbeitet und in Cassandra gespeichert.

---
## Architekturüberblick

### Datenfluss:
Sensor-Simulator → Kafka → Spark Structured Streaming → Cassandra

Sensor-Simulator sendet fortlaufend JSON-Messwerte (Temperatur, Salzgehalt) von drei simulierten Sensoren an Kafka.

Kafka dient als Message-Broker für den Echtzeit-Datenstrom.

Spark Structured Streaming liest kontinuierlich die Daten aus Kafka, führt Berechnungen und Aggregationen durch:

- Berechnung von Durchschnitts-, Minimal- und Maximalwerten pro Sensor in 30-Sekunden-Zeitfenstern.

- Erkennung von Anomalien, wenn Temperaturwerte außerhalb des normalen Bereichs ( <2.5 °C oder >9.5 °C) liegen.

Cassandra speichert sowohl aggregierte Sensordaten als auch erkannte Anomalien persistent in den Tabellen sensor_aggregates und sensor_anomalies.

---

### Ordnerstruktur

```bash
project-root/
│
├── sensor_data/
│   ├── Dockerfile             # Image-Build für den Sensor-Simulator
│   ├── requirements.txt       # Python-Abhängigkeiten
│   └── sensordata.py          # Sensor-Simulator (Kafka Producer)
├── spark/
│   └── spark_kafka_consumer.py # Spark Streaming Job
├── cassandra/
│   ├── init.cql               # Initialisierung des Keyspace & Tabellen
│   ├── cassandra.yaml         # Benutzerdefinierte Konfiguration (optional entfernbar)
│   └── deletesuperuser.cql    # Optional: Entfernt Cassandra Superuser
├── docker-compose.yaml        # Service-Konfiguration
└── .env                       # Muss manuell angelegt werden (Cassandra-Credentials)
```

## Voraussetzungen

Vor dem Start sollten folgende Tools installiert werden:

| Komponente            | Empfehlung                  | Hinweis                                                          |
| --------------------- | --------------------------- | ---------------------------------------------------------------- |
| **Docker Desktop**    | ≥ 4.x/ mind. 4 GB RAM       | Empfohlen für lokale Entwicklung und Containerverwaltung         |            
| **Java JDK 11**       | Zwingend erforderlich       | Spark benötigt Java 11 zur Laufzeit                              |
| **Python 3.9+**       | Optional                    | Nur nötig, wenn Code außerhalb von Docker getesten werden soll   |

---

## Setup & Ausführung

**Wichtige Hinweise zum Startverhalten:**

- Der vollständige Start aller Services kann bis zu 5 Minuten dauern.
- Der Sensor-Simulator hat einen Startverzögerungstimer von 2 Minuten, damit alle abhängigen Services (Kafka, Spark, Cassandra) korrekt initialisiert sind bevor Daten gesendet werden.
- Innerhalb dieser 2 Minuten sollte bei Erstinitialisierung die u.g. Cassandra `init.cql` ausgeführt werden.

### 1️. Starten der Container

```bash
docker compose up --build -d
```

Alle Container werden gebaut und gestartet. Healthchecks sorgen dafür, dass Services in der richtigen Reihenfolge initialisiert werden.

---

### 2. Cassandra initialisieren

Bei der **erstmaligen Initialisierung:** 
Warten bis der Cassandra-Container vollständig hochgefahren ist, kann bis zu **2 Minuten** dauern. Danach folgenden Befehl ausführen:

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

**Alternativ:**
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

* .env-Datei: Diese wird nicht mitgeliefert und muss manuell angelegt werden.
Sie enthält sensible Umgebungsvariablen:

```
CASSANDRA_USER=<dein_benutzername>
CASSANDRA_PASSWORD=<dein_passwort>
```

* **Alternative Cassandra-Konfiguration:** Die Datei `cassandra.yaml` im Ordner `/cassandra` kann **gelöscht** werden, um die **Standardkonfiguration** von Cassandra zu aktivieren. Dabei wird u. a. der `AllowAllAuthenticator` genutzt, der **keine Authentifizierungsprüfung** durchführt.
  Dies ist **nicht empfohlen** und sollte nur zu Testzwecken verwendet werden.

### Netzwerksicherheit

* Standardmäßig sind **alle externen Ports deaktiviert** (außer Cassandra-Port `9042` für PyCharm-Integration) um Netzwerkisolation zu wahren.
* Ports können bei Bedarf in `docker-compose.yml` aktiviert werden.
* Kafka und Spark Web-UIs sind **optional** (siehe oben).

### Datenverschlüsselung

Für Produktivumgebungen wird empfohlen:

- SSL/TLS-Verschlüsselung zwischen allen Diensten zu aktivieren (Kafka, Spark, Cassandra)

- Verschlüsselung gespeicherter Daten (at rest) in Cassandra zu nutzen

Diese Sicherheitsmechanismen erfordern die Einrichtung geeigneter Zertifikate und Schlüsseldateien (z. B. JKS oder PEM) zur Authentifizierung und Verschlüsselung.

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

## Autor

Erstellt im Rahmen des Moduls **Projekt: Data Engineering** © 2025 – J.W.
