import time
import json
import random
import logging
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

#Logging einrichten(B)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Kafka-Producer initialisieren
try:
    producer = KafkaProducer(
        bootstrap_servers=["kafka:9092"],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") #Partitionierung
    )
    logging.info("Connected to Kafka broker")
except NoBrokersAvailable:
    logging.error("Connection to Broker failed")
    exit(1)
except KafkaError as e:
    logging.error(f"Error connecting to Kafka {e}")
    exit(1)

# Simulationsparameter
sensor_ids = ["SENSOR-01", "SENSOR-02", "SENSOR-03"]

try:
    while True:
        # Zufällig einen Sensor wählen
        sensor_id = random.choice(sensor_ids)
        # Zufällige Messwerte generieren
        temperature = round(random.uniform(2.0, 10.0), 2)
        salinity = round(random.uniform(31.0, 35.0), 2)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Datenstruktur aufbauen
        data = {
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "temperature": temperature,
            "salinity": salinity
        }

        try:
            producer.send("sensor-data", key=sensor_id, value=data)
            logging.info(f"Send: {data}")
        except KafkaError as e:
            logging.error(f"Error while sending: {e}")
            exit(1)

        # Eine Sekunde warten
        time.sleep(1)

finally:
    producer.flush()
    producer.close()
    logging.info("Kafka producer closed.")