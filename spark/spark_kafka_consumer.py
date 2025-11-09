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
kafka_bootstrap_servers = "kafka:9092"
kafka_topic = "sensor-data"
cassandra_user = os.getenv("CASSANDRA_USER") #.env anlegen und User hinterlegen
cassandra_pass = os.getenv("CASSANDRA_PASSWORD") #.env anlegen und PW hinterlegen

# Spark Session setup
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingConsumer") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,"
            "com.datastax.spark:spark-cassandra-connector_2.12:3.3.0") \
    .config("spark.cassandra.connection.host", "cassandra") \
    .config("spark.cassandra.connection.port", "9042") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Kafka-Stream lesen #Fail von DataLoss evtl. an HIER PRÜFEN
logger.info(f"Connecting to Kafka topic '{kafka_topic}' on {kafka_bootstrap_servers}...")

raw_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

logger.info("Kafka stream successfully initialized.")

# Kafka Payload parsen
parsed_df = raw_df.selectExpr(
    "CAST(key AS STRING) AS kafka_key",
    "CAST(value AS STRING) AS kafka_value",
    "partition",
    "offset"
)

# Definiton Schema
schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("temperature", DoubleType()) \
    .add("salinity", DoubleType()) \
    .add("timestamp", TimestampType())

# JSON Payload entpacken
json_df = parsed_df.select(
    "partition",
    "offset",
    "kafka_key",
    from_json(col("kafka_value"), schema).alias("data")
).select(
    "partition",
    "offset",
    "kafka_key",
    col("data.*")
)

# Fensterbasierte Aggregationen
windowed_df = json_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(
        col("sensor_id"),
        window(col("timestamp"), "30 seconds")
    ) \
    .agg(
        round(avg("temperature"), 2).alias("avg_temp"),
        round(min("temperature"), 2).alias("min_temp"),
        round(max("temperature"), 2).alias("max_temp"),
        round(avg("salinity"), 2).alias("avg_salinity")
    )

# Fenster flatten für Cassandra
windowed_df_flat = windowed_df \
    .withColumn("window_start", col("window.start")) \
    .withColumn("window_end", col("window.end")) \
    .drop("window")

# Anomalien erkennen und Schreiben in Cassandra
anomalies_df = json_df.filter((col("temperature") > 9.5) | (col("temperature") < 2.5))

# Funktionen schreiben
def write_to_cassandra(batch_df, batch_id):
    try:
        logger.info(f"Writing batch {batch_id} to Cassandra (aggregates)...")
        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", "sensordata") \
            .option("table", "sensor_aggregates") \
            .option("spark.cassandra.connection.host", "cassandra") \
            .option("spark.cassandra.connection.port", "9042") \
            .option("spark.cassandra.auth.username", cassandra_user) \
            .option("spark.cassandra.auth.password", cassandra_pass) \
            .save()
        logger.info(f"Batch {batch_id} successfully written to sensor_aggregates.")
    except Exception as e:
        logger.error(f"Error writing batch {batch_id} to Cassandra: {e}", exc_info=True)

def write_anomalies_to_cassandra(batch_df, batch_id):
    try:
        if batch_df.count() == 0:
            return
        logger.warning(f"Detected {batch_df.count()} anomalies in batch {batch_id}. Writing to Cassandra...")
        cleaned_df = batch_df.select("sensor_id", "temperature", "salinity", "timestamp")
        cleaned_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", "sensordata") \
            .option("table", "sensor_anomalies") \
            .option("spark.cassandra.connection.host", "cassandra") \
            .option("spark.cassandra.connection.port", "9042") \
            .option("spark.cassandra.auth.username", "cassandra") \
            .option("spark.cassandra.auth.password", "cassandra") \
            .save()
        logger.info(f"Anomalies batch {batch_id} written to Cassandra.")
    except Exception as e:
        logger.error(f"Error writing anomalies batch {batch_id}: {e}", exc_info=True)

# Ausgabe an Konsole
query_console = windowed_df.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .option("numRows", 20) \
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/console") \
    .start()

# Stream Aggregationen
query_agg = windowed_df_flat.writeStream \
    .outputMode("update") \
    .foreachBatch(write_to_cassandra) \
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/sensor_agg") \
    .start()

# Schreiben der Anomalien
query_anomalies = anomalies_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_anomalies_to_cassandra) \
    .option("checkpointLocation", "file:///tmp/spark-checkpoint/anomalies") \
    .start()

# KEEP STREAM ALIVE
query_console.awaitTermination()
query_agg.awaitTermination()
query_anomalies.awaitTermination()