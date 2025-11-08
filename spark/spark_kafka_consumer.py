from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType

# 1️⃣ Spark Session
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingConsumer") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2️⃣ Kafka Config
kafka_bootstrap_servers = "kafka:9092"
kafka_topic = "sensor-data"  # Topic

# 3️⃣ Kafka-Stream lesen
raw_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "earliest") \
    .load()

# Key und Value als String casten
parsed_df = raw_df.selectExpr(
    "CAST(key AS STRING) AS kafka_key",
    "CAST(value AS STRING) AS kafka_value",
    "partition",
    "offset"
)

# 4️⃣ JSON aus Kafka "value" Feld extrahieren
schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("temperature", DoubleType()) \
    .add("salinity", DoubleType()) \
    .add("timestamp", TimestampType())

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

# 5️⃣ Stream ausgeben (zur Kontrolle)
query = json_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()