# sensor_data/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installiere Kafka-Client
RUN pip install kafka-python

# Kopiere den Code ins Image
COPY . /app

# Standardbefehl
CMD ["python", "sensordata.py"]
