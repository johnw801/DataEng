"""
Dieses Skript simuliert Sensordaten (Temperatur & Salzgehalt)
von mehreren Sensoren und sendet sie als JSON-Nachrichten an
das Kafka-Topic "sensor-data".

Funktion:
- Generiert kontinuerlich zufällige Messwerte.
- Sendet diese über einen KafkaProducer an den Broker.
- Läuft kontinuierlich, bis es manuell gestoppt wird

Parameter:
- Kafka-Broker:  kafka:9092
- Topic:         sensor-data
- Sensoren:      SENSOR-01 bis SENSOR-03
- Intervall:     1 Sekunde

Abhängigkeit:
- kafka-python (siehe requirements.txt)

Beispielausgabe:
2025-11-10 10:45:12 [INFO] Send: {'sensor_id': 'SENSOR-01', ...}

Hinweise:
- Dient der Simulation und zum Testen von Kafka-Datenpipelines.
- In Produktivsystemen sollten zusätzliche Sicherheitsmaßnahmen wie SSL-Verschlüsselung eingestzt werden
"""

import time
import json
import random
import logging
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Kafka-Producer initialisieren
try:
    producer = KafkaProducer(
        bootstrap_servers=["kafka:9092"],       # Verbindet Producer mit Kafka-Broker
        value_serializer=lambda v: json.dumps(v).encode("utf-8"), # wandelt Python-Daten in JSON um
        key_serializer=lambda k: k.encode("utf-8") # Partitionierung nach Sensor-ID
    )
    logging.info("Connected to Kafka broker")
except NoBrokersAvailable:
    logging.error("Connection to Broker failed")
    exit(1)
except KafkaError as e:
    logging.error(f"Error connecting to Kafka {e}")
    exit(1)

# Simulationsparameter
# Liste Sensoren
sensor_ids = ["SENSOR-01", "SENSOR-02", "SENSOR-03"]

# Endlosschleife: sendet kontinuierlich Sensordaten
try:
    while True:
        # Zufällig einen Sensor wählen
        sensor_id = random.choice(sensor_ids)
        # Zufällige Messwerte generieren (Temp + Salzgehalt)
        temperature = round(random.uniform(2.0, 10.0), 2)
        salinity = round(random.uniform(31.0, 35.0), 2)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Datenstruktur aufbauen (JSON-kompatibel)
        data = {
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "temperature": temperature,
            "salinity": salinity
        }

# Nachricht an Kafka senden, Topic: "sensor-data", key: sensor_id (bestimmt Partition), value: Datensatz (JSON)
        try:
            producer.send("sensor-data", key=sensor_id, value=data)
            logging.info(f"Send: {data}")
        except KafkaError as e:
            logging.error(f"Error while sending: {e}")
            exit(1)

        # Eine Sekunde warten bevor nächster Datensatz gesendet wird
        time.sleep(1)

# Sicherstellen, dass alle Nachrichten gesendet und die Verbindung sauber geschlossen wird
finally:
    producer.flush() # Sendet alle ausstehenden Nachrichten
    producer.close() # Schließt die Kafka-Verbindung
    logging.info("Kafka producer closed.")