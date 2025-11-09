-- Default-Superuser 'cassandra' neutralisieren. BITTE PW ÄNDERN !!!!!!
ALTER ROLE cassandra
  WITH PASSWORD = 'initialespasswortbitteaendern'
  AND SUPERUSER = false
  AND LOGIN = false;