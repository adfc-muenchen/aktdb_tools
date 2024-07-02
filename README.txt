Das Google-Project ist aktdb2groups, User michael.uhlenberg@adfc-muenchen.de, siehe https://console.cloud.google.com.
Dort setzt man die APIs, bisher wohl
Google Sheets API
Admin SDK API
BigQuery API
BigQuery Migration API
BigQuery Storage API
Cloud Datastore API
Cloud Logging API
Cloud Monitoring API
Cloud SQL
Cloud Storage
Cloud Storage API
Cloud Trace API
Gmail API
Google Cloud APIs
Google Cloud Storage JSON API
Google Drive API
Groups Settings API
Service Management API
Service Usage API

Benutzt werden bisher nur Admin SDK API, Google Sheets API und Gmail API (siehe gg.py ssheetService, adminService, gmailService)
Die Scopes stehen in gg.py.
Ändert sich was an den APIs oder Scopes, oder ist das Token sonst ungültig, oder token.json fehlt,
muß für den sync AktivenDB->GGroups der Browser für einen Google Admin 
(z.B. michael.uhlenberg.admin@adfc-muenchen.de) offen sein. 
Wir brauchen Admin-Privilegien für Änderungen an Google Groups! 
Um das Spreadsheet lesen und ändern zu können, für den sync Serienbrief/Erstanmeldung->AktivenDB, 
genügt ein normaler Benutzer mit den entsprechenden Rechten.