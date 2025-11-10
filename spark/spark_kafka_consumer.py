"""
Kafka → Spark Structured Streaming → Cassandra Pipeline

Funktion:
Dieses Skript liest kontinuierlich Sensordaten aus einem Kafka-Topic ("sensor-data"),
führt zeitfensterbasierte Aggregationen (Temperatur/Salzgehalt) durch,
erkennt Temperatur-Anomalien und schreibt Ergebnisse in Cassandra-Tabellen.

Komponenten:
- Kafka  → Datenquelle (JSON)
- Spark  → Stream-Verarbeitung & Aggregation
- Cassandra → Persistente Speicherung

Parameter:
- Kafka Topic: sensor-data
- Cassandra Keyspace: sensordata
  Tabellen: sensor_aggregates, sensor_anomalies
- ENV Variablen: CASSANDRA_USER, CASSANDRA_PASSWORD

Abhängigkeiten:
- pyspark
- Cassandra Connector für Spark

Hinweise:
- Authentifizierungsdaten (Cassandra) werden über Umgebungsvariablen
  `CASSANDRA_USER` und `CASSANDRA_PASSWORD` eingelesen.
- Für produktive Nutzung: SSL- oder SASL-Auth aktivieren
"""

import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, min, max, window, round
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("spark-consumer")

logger.info("Spark Streaming job starting...")

# Environment konfiguration
KAFKA_BOOTSTRAP = "kafka:9092"
KAFKA_TOPIC = "sensor-data"
SPARK_PACKAGES = ("org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,"
                  "com.datastax.spark:spark-cassandra-connector_2.12:3.3.0")
CASSANDRA_HOST = "cassandra"
CASSANDRA_PORT = "9042"
CASSANDRA_USER = os.getenv("CASSANDRA_USER") #.env anlegen und User hinterlegen
CASSANDRA_PASS = os.getenv("CASSANDRA_PASSWORD") #.env anlegen und PW hinterlegen

# Spark Session setup
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingConsumer") \
    .config("spark.jars.packages",SPARK_PACKAGES) \
    .config("spark.cassandra.connection.host", CASSANDRA_HOST) \
    .config("spark.cassandra.connection.port", CASSANDRA_PORT) \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Kafka Stream einlesen
logger.info(f"Connecting to Kafka topic '{KAFKA_TOPIC}' on {KAFKA_BOOTSTRAP}...")

# Spark liest kontinuierlich neue Daten aus Kafka
raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest") #"earliest" = alle vorhandenen Daten + neue
    .option("failOnDataLoss", "true")  # bricht ab, falls Datenlücke erkannt wird
    .load()
)

logger.info("Kafka stream successfully initialized.")

# JSON Parsing & Schema
# JSON aus Kafka in Spalten umwandeln
schema = (
    StructType()
    .add("sensor_id", StringType())
    .add("temperature", DoubleType())
    .add("salinity", DoubleType())
    .add("timestamp", TimestampType())
)

# JSON-String aus Kafka ("value") wird in Spalten aufgelöst
json_df = (
    raw_df.selectExpr("CAST(value AS STRING) AS kafka_value")
    .select(from_json(col("kafka_value"), schema).alias("data"))
    .select("data.*")
)

# Fensterbasierte Aggregationen
# Aggregation in 30-Sekunden-Zeitfenstern pro Sensor
# Berechnet Durchschnitt, Minimum und Maximum der Temperatur & Salinität
windowed_df = (
    json_df
    .withWatermark("timestamp", "1 minute")  # erlaubt 1 Minute "late data"
    .groupBy(
        col("sensor_id"),
        window(col("timestamp"), "30 seconds")
    )
    .agg(
        round(avg("temperature"), 2).alias("avg_temp"),
        round(min("temperature"), 2).alias("min_temp"),
        round(max("temperature"), 2).alias("max_temp"),
        round(avg("salinity"), 2).alias("avg_salinity")
    )
)

# Flatten des Fensterobjekts (Start/Ende als separate Spalten)
windowed_df_flat = (
    windowed_df
    .withColumn("window_start", col("window.start"))
    .withColumn("window_end", col("window.end"))
    .drop("window")
)

# Anomalie-Erkennung
# Filtert Sensorwerte, deren Temperatur außerhalb des "normalen" Bereichs lieg
anomalies_df = json_df.filter((col("temperature") > 9.5) | (col("temperature") < 2.5))

 # Cassandra Write-Funktionen
def write_to_cassandra(batch_df, batch_id):
    """Schreibt aggregierte Sensordaten nach Cassandra."""
    try:
        logger.info(f"Writing batch {batch_id} to Cassandra (aggregates)...")
        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(
                keyspace="sensordata",
                table="sensor_aggregates",
                **{
                    "spark.cassandra.connection.host": CASSANDRA_HOST,
                    "spark.cassandra.connection.port": CASSANDRA_PORT,
                    "spark.cassandra.auth.username": CASSANDRA_USER,
                    "spark.cassandra.auth.password": CASSANDRA_PASS,
                }
            ).save()
        logger.info(f"Batch {batch_id} written to sensor_aggregates.")
    except Exception as e:
        logger.error(f"Error writing batch {batch_id}: {e}", exc_info=True)


def write_anomalies_to_cassandra(batch_df, batch_id):
    """Schreibt erkannte Anomalien in Cassandra."""
    if batch_df.isEmpty():
        return
    try:
        logger.warning(f"Detected anomalies in batch {batch_id}. Writing to Cassandra...")
        batch_df.select("sensor_id", "temperature", "salinity", "timestamp") \
            .write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(
                keyspace="sensordata",
                table="sensor_anomalies",
                **{
                    "spark.cassandra.connection.host": CASSANDRA_HOST,
                    "spark.cassandra.connection.port": CASSANDRA_PORT,
                    "spark.cassandra.auth.username": CASSANDRA_USER,
                    "spark.cassandra.auth.password": CASSANDRA_PASS,
                }
            ).save()
        logger.info(f"Anomalies batch {batch_id} written to Cassandra.")
    except Exception as e:
        logger.error(f"Error writing anomalies batch {batch_id}: {e}", exc_info=True)

# Konsolen-Output → zeigt aktuelle Aggregationen im Terminal
query_console = (
    windowed_df.writeStream
    .outputMode("update")
    .format("console")
    .option("truncate", "false")
    .option("numRows", 20)
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/console")
    .start()
)

# Aggregationen → Cassandra schreiben
query_agg = (
    windowed_df_flat.writeStream
    .outputMode("update")
    .foreachBatch(write_to_cassandra)
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/sensor_agg")
    .start()
)

# Anomalien → Cassandra schreiben
query_anomalies = (
    anomalies_df.writeStream
    .outputMode("append")
    .foreachBatch(write_anomalies_to_cassandra)
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/anomalies")
    .start()
)

# Streaming aktiv halten
query_console.awaitTermination()
query_agg.awaitTermination()
query_anomalies.awaitTermination()