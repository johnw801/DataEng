-- Keyspace und Tabellen erstellen

-- Keyspace erstellen
CREATE KEYSPACE IF NOT EXISTS sensordata
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

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

-- Rollen erstellen und Rechte vergeben

-- admin Rolle anlegen.BITTE PW ÄNDERN !!!!!!
CREATE ROLE IF NOT EXISTS admin
    WITH PASSWORD = 'initialespasswortbitteaendern'
    AND LOGIN = true
    AND SUPERUSER = true;

-- User Rolle anlegen (Least Privilege).BITTE PW ÄNDERN !!!!!!
CREATE ROLE IF NOT EXISTS myuser
    WITH PASSWORD = 'initialespasswortbitteaendern'
    AND LOGIN = true;

-- myuser Leserechte vergeben
GRANT SELECT ON TABLE sensordata.sensor_aggregates TO myuser;
GRANT SELECT ON TABLE sensordata.sensor_anomalies TO myuser;