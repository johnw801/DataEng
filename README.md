# DataEng – Echtzeit Data Engineering Pipeline
## Beschreibung

Dieses Projekt demonstriert eine vollständige Streaming Data Pipeline mit Kafka, Apache Spark Structured Streaming und Cassandra. Ozeanographische Sensordaten werden simuliert, über Kafka gestreamt, von Spark verarbeitet und in Cassandra gespeichert.

---
## Architekturüberblick

### Datenfluss
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
---
### Verwendete Docker Images
- cassandra:4.1
- confluentinc/cp-kafka:8.1.0
- bde2020/spark-master:3.3.0-hadoop3.3
- bde2020/spark-worker:3.3.0-hadoop3.3
- bde2020/spark-submit:3.3.0-hadoop3.3
- provectuslabs/kafka-ui:latest (optional)

---
## Voraussetzungen

Vor dem Start sollten folgende Tools installiert werden:

| Komponente            | Empfehlung                  | Hinweis                                                          |
| --------------------- | --------------------------- | ---------------------------------------------------------------- |
| **Docker Desktop**    | ≥ 4.x/ mind. 4 GB RAM       | Empfohlen für lokale Entwicklung und Containerverwaltung         |            
| **Python 3.9+**       | Optional                    | Nur nötig, wenn Code außerhalb von Docker getesten werden soll   |

---

## Setup & Ausführung

### Wichtige Hinweise zum Startverhalten

- Der vollständige Start aller Services kann bis zu **5 Minuten** dauern.
- Der Sensor-Simulator hat einen Startverzögerungstimer von **2 Minuten**, damit alle abhängigen Services (Kafka, Spark, Cassandra) korrekt initialisiert sind bevor Daten gesendet werden.
Bei langsameren Hostsystemen kann dieser Wert bei Bedarf erhöht werden.
- Innerhalb dieser 2 Minuten sollte bei Erstinitialisierung die u.g. Cassandra `init.cql` ausgeführt werden.
- Healthchecks sorgen dafür, dass Services in der richtigen Reihenfolge initialisiert werden.
  
---
### 1️. Starten der Container

```bash
docker compose up --build -d
```

Alle Container werden gebaut und gestartet.

---
### 2. Cassandra initialisieren

Bei der **erstmaligen Initialisierung:** 
Warten bis der Cassandra-Container vollständig hochgefahren ist, kann bis zu **2 Minuten** dauern. Danach folgenden Befehl ausführen:

```bash
docker exec -it cassandra cqlsh -u cassandra -p cassandra -f /init.cql
```
Erstellung des keyspaces `sensordata`, der Tabellen `sensor_aggregates` und `sensor_anomalies` sowie der Standarduser `admin` und `myuser` (User mit least privilege Rechten)


Optional kann der Cassandra Standard-Superuser entfernt werden:

```bash
docker exec -it cassandra cqlsh -u cassandra -p cassandra -f /deletesuperuser.cql
```

---

### 3. Services überwachen
Für die Überwachung der Services wird Docker Desktop empfohlen.

**Alternativ:**

**Wichtige Dockerbefehle**

Container-Status prüfen:

```bash
docker ps
```

Logs anzeigen:

```bash
docker logs -f sensor-simulator
docker logs -f spark-submit-job
docker logs -f cassandra
docker logs -f kafka
```

Container neu starten:

```bash
docker restart kafka # einzelnen Container neustarten
docker restart $(docker ps -q) # alle Container neustarten
```

Container starten/stoppen (ohne Löschen):

```bash
docker start kafka # einzelnen Container starten
docker start $(docker ps -a -q) # alle Container starten
docker stop kafka # einzelnen Container stoppen
docker stop $(docker ps -q) # alle Container stoppen
```

Alle Container stoppen und löschen:

```bash
docker compose down
docker compose down -v # inkl. löschen von Volumes
```

---

**Wichtige Cassandra Befehle**

Cassandra-Client öffnen:

```bash
docker exec -it cassandra cqlsh
```

Alle Keyspaces anzeigen:

```bash
DESCRIBE KEYSPACES;
```

In Keyspace wechseln:

```bash
USE sensordata;
```

Tabellen anzeigen:

```bash
DESCRIBE TABLES;
```

Struktur einer Tabelle anzeigen:

```bash
DESCRIBE TABLE sensor_aggregates;
```

Daten ansehen:

```bash
SELECT * FROM sensor_aggregates LIMIT 10;
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

* Nach dem Ausführen von `init.cql` werden eine `admin` Rolle und eine Userrolle `myuser` (least privilege) für den Zugriff auf die Cassandra DB erstellt.
* Für den Produktiveinsatz wird dringend empfohlen den Standard Cassandra-Superuser zu löschen oder zu deaktivieren. Dafür wird das Skript `deletesuperuser.cql` bereitgestellt.

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
---
### Netzwerksicherheit

* Standardmäßig sind **alle externen Ports deaktiviert** (außer Cassandra-Port `9042` für PyCharm-Integration) um Netzwerkisolation zu wahren.
* Ports können bei Bedarf in `docker-compose.yml` aktiviert werden.
* Kafka und Spark Web-UIs sind **optional** (siehe oben).
---
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
