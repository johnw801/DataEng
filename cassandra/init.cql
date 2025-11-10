-- admin Rolle anlegen.BITTE PW ÄNDERN !!!!!!
CREATE ROLE IF NOT EXISTS admin
    WITH PASSWORD = 'initialespasswortbitteaendern'
    AND LOGIN = true
    AND SUPERUSER = true;

-- User Rolle anlegen (Least Privilege).BITTE PW ÄNDERN !!!!!!
CREATE ROLE IF NOT EXISTS myuser
    WITH PASSWORD = 'initialespasswortbitteaendern'
    AND LOGIN = true;

-- Keyspace erstellen
CREATE KEYSPACE IF NOT EXISTS sensordata
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

GRANT SELECT ON KEYSPACE sensordata TO myuser;
GRANT MODIFY ON KEYSPACE sensordata TO myuser;

-- Tabellen erstellen unter keyspace sensordata
USE sensordata;

-- Tabelle aggregierte Werte
CREATE TABLE IF NOT EXISTS sensor_aggregates (
    sensor_id text,
    window_start timestamp,
    avg_temp double,
    min_temp double,
    max_temp double,
    avg_salinity double,
    window_end timestamp,
    PRIMARY KEY (sensor_id, window_start)
);

-- Tabelle Anomalien
CREATE TABLE IF NOT EXISTS sensor_anomalies (
    sensor_id text,
    temperature double,
    salinity double,
    timestamp timestamp,
    PRIMARY KEY (sensor_id, timestamp)
);
