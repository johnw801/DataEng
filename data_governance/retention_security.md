# Retention and Security
Dieser Abschnitt definiert, wie lange Daten gespeichert werden und beschreibt Datenschutz- sowie Sicherheitsanforderungen .

**Kafka Datenaufbewahrung**
- Aufbewahrungsdauer: 24 Stunden
- Begründung: Minimierung personenbezogener Daten (DSGVO) (Projekt hat keine personenbezogenen Daten daher ist die Info allgemein)
- Empfehlung für Produktion: Anpassung je nach Speicherbedarf und Compliance

**Cassandra Datenaufbewahrung**
- Tabelle Aggregationen: Dauerhafte Speicherung
- Tabelle Anomalien: Dauerhafte Speicherung
- Empfehlung für Produktion: Archivierung in Data Lake nach 12 Monaten

**Netzwerksicherheit**

- Keine extern exponierten Ports (mit Ausnahme 9042)
- Empfehlung für Produktion: TLS/SSL für Daten in Transit zwischen Kafka, Spark und Cassandra aktivieren
- Zusätzlich TDE/ Verschlüsselung für Daten at Rest