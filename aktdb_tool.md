# Aktdb_tools

## Zweck

Das Programm aktdb_tools ersetzt Code im Umkreis der AktivenDB, der bisher an unterschiedlichen Orten auf unterschiedliche Weise programmiert war.

- Die Synchronisierung AktivenDB->Google Groups war ein eigenes Python-Programm.
- Das Schreiben der Serienbriefe erfolgte über ein Skript, das am Serienbrief-Backend hing, und erforderte, daß man aus dem AktivenDB-Frontend heraus die Member-Daten als Excel exportierte. Diese Excel-Datei wurde von dem Skript gelesen, um die aktuellen Daten der AktivenDB zu haben. Die Antworten-Tabelle aus dem Serienbrief-Backend wurde auch gelesen, um bei dem "Mahnschreiben", das Formular doch bitte bitte noch auszufüllen, nicht die anzuschreiben, die es schon ausgefüllt hatten. Programmiert in Google Appsscript, einer Javascript-Variante.
- Die Serienbrief-Antworten wurden von einem Code im AktivenDB-Frontend ausgeführt, der über die Seite aktivendb/importSB gestartet wurde. Dieser Code erforderte, daß man die Serienbrief-Antworten als Excel-Tabelle exportierte. Programmiert in Vue/Javscript.

Nur das erste Programm griff sowohl auf die AktivenDB wie auf Google Groups zu, die beiden anderen nahmen zu dem Kunstgriff/Hack Zuflucht, die Daten der Gegenseite als Excel-Datei zu bekommen.

Als nun auch noch Code verlangt wurde, um die Daten des Formulars "Erstantworten" in die AktivenDB zu bekommen, wurde es Zeit für ein Redesign. Das Programm aktdb_tools loggt sich sowohl bei Google als bei der AktivenDB ein. Bei Google benutzen wir drei "Services": erstens senden wir Emails, zweitens greifen wir auf die Serienbrief-Tabellen zu, drittens benutzen wir die Google-Groups-Api. Letzteres verlangt Admin-Privilegien. Beim Senden von Emails gilt aber, daß immer der eingeloggte Benutzer als Absender der Email angegeben wird (egal, was man als From:-Parameter angibt).

Die Serienbrief-Antworten müssen immer möglichst zeitnah bearbeitet werden, da sonst die Gefahr besteht, daß andere Änderungen z.B. von einem Gruppenleiter wieder überschrieben werden. Man mußte sich also immer merken, bis zu welcher Zeile schon importiert war, und beim nächsten Import nur die danach folgenden Zeilen importieren. Also die schon importierten Zeilen vor dem Import aus der Excel-Datei zu löschen. Das habe ich einmal verbockt, und damit wurde ein schon längst überholter Stand der AktivenDB wiederhergestellt.

Das Programm aktdb_tools markiert jetzt in der Serienbrief-Tabelle importierte Zeilen, so daß sie beim nächsten Import übersprungen werden. Das erfordert natürlich Schreibrechte.

## Installation

Es gibt Methoden, aus Python-Code eine .exe-Datei zu machen. Leider schlagen dabei oft Antivirus-Programme an. Da ich nicht davon ausgehe, daß aktdb_tools von IT-Laien ausgeführt wird, belasse ich es erst mal bei Python und der command line. Wir müssen also Python installiert haben. Der Aufruf `python -v` sollte eine Versionsnummer >3.10 ausgeben. Git kann, muß aber nicht installiert sein.
Hat man git installiert, ruft man in einem mit Bedacht zu wählenden Verzeichnis

    git clone https://github.com/adfc-muenchen/aktdb_tools.git

auf, oder man entpackt die Zip-Datei https://github.com/adfc-muenchen/aktdb_tools/archive/refs/heads/main.zip
und benennt aktdb_tools-main nach aktdb_tools um. Danach geht man in das Verzeichnis aktdb_tools:

    cd aktdb_tools

und ruft

    python -m venv .venv

auf, um ein sogenanntes "virtuelles environment" zu erstellen. Danach aktiviert man das virtuelle environment mit

    .venv\scripts\activate

Dann werden die requirements, also die zusätzlich erforderlichen Programmbibliotheken, mit

    pip install -r requirements.txt

installiert. Aufrufe, eine neue Release von pip zu installieren, ignorieren wir, die kommen immer. Die bisher durchgeführten Schritte liest man auch im Netz in unzähligen Tutorials.

Mit dem Aufruf

    python main.py --help

sollte jetzt eine Meldung erscheinen, wie das Programm aus der command line heraus gestartet werden kann. Mit nur

    python main.py

sollte ein kleines Fenster gestartet werden, mit dem das Programm genauso gestartet werden kann (und normalerweise wird). Jetzt aber schließen wir das Fenster erstmal wieder, denn noch fehlen die Geheim-Dateien und verschiedene Verzeichnisse!

Im Verzeichnis aktdb_tools legen wir die Unterverzeichnisse aktdb_data, gg_data, logs und secret an. In das Verzeichnis secret kopieren wir die Datei credentials.json, die wir von jemandem bekommen, der sie hat. Und die geheim zu halten ist!

> Wir benötigen Credentials von einem Projekt mit den APIs wie in README.txt beschrieben.

Im Verzeichnis secret erzeugen wir zweitens eine Datei mit dem Namen aktdb.creds und dem Inhalt

    {"email": "vorname.nachname@adfc-muenchen.de", "password": "------"}

Also mit den Daten, mit denen wir uns bei der AktivenDB als Admin einloggen. Genauso geheimzuhalten!

## Einloggen

Das Programm sucht beim Start nach einer Datei token.json, in der ein sogenanntes Zugriffstoken enthalten ist. Existiert die Datei nicht, oder ist das Token abgelaufen, wird ein Dialog gestartet, mit dem dem Programm die Zugriffsrechte im Auftrag des eingeloggten Google-Benutzers erteilt werden. Dazu muß man sich **vorher** in einem Browser als ADFC-Benutzer eingeloggt haben, und dieser Browser muß der aktuell aktive sein. Dann wird der Dialog in diesem Browser gestartet. In einem anderen Browser kommt entweder die Aufforderung, sich einzuloggen, oder die Zugriffsberechtigung wird rundheraus verweigert.
Wir loggen uns also in einem Browser (chrome) als vorname.nachname@adfc-muenchen.de ein, lassen den Browser so stehen, gehen zu keinem anderen Browser, sondern in die command line, und starten das Programm mit

    python main.py

Dann klicken wir auf den obersten roten Knopf. Im Browser sollte jetzt der Dialog aufpoppen. Bei "Konto auswählen" klicken wir natürlich auf unser Konto, und dann auf "Zulassen". Danach können wir den Browser oder das Fenster oder den Tab schließen. In unserem Verzeichnis sehen wir jetzt die Datei token.json.

Sollten wir vorhaben, die Synchronisierung AktivenDB->Google Groups zu starten, reichen uns die Zugriffsrechte unseres normalen Benutzers nicht. Dazu löschen wir die Datei token.json (oder benennen sie um), und wiederholen das Spiel, nur daß wir uns jetzt als ein Google Admin im Browser anmelden. Wir können natürlich auch immer nur als admin eingeloggt sein. Soweit ich weiß, kann man als Admin auch auf alle Dateien zugreifen, ohne dazu eine spezielle Berechtigung zu brauchen. Um Serienbriefe zu verschicken, sollte man aber als Thomas Schubert eingeloggt sein, also als jemand mit dem Mail-Alias aktive@adfc-muenchen.de.

Klicken wir jetzt ein zweites Mal auf den obersten roten Knopf, sollte nicht viel passieren, vor allem sollten keine Fehlermeldungen kommen. Falls doch, fehlen vielleicht Berechtigungen bei der Serienbrief-Backend-Tabelle?

## Programm-Benutzung

aktdb_tools besteht ja eigentlich aus (bisher) vier unterschiedlichen Programmen. In der Gui schlägt sich das in 4 Abschnitten nieder. Die Überschriften sprechen für sich. Bei allen gibt es einen Schalter "Ausführung", der zu Beginn auf "Erstmal testen" steht. Damit wird verhindert, daß wirkliche schreibende Zugriffe erfolgen. Man sieht, was das Programm tun würde. Und man sieht Probleme, die erst gefixt werden sollten.

Nach jeder Ausführung mit umgelegtem Schalter wird eine Log-Datei in das Verzeichnis logs geschrieben. Die Log-Dateien sollten aufbewahrt werden. Es gibt in der AktivenDB zwar auch eine History-Funktion, aber anhand der Log-Dateien kann man später vielleicht mal sehen, wann was passiert ist. Die Log-Dateien haben die Präfixe s2a, e2a, a2g, ssb, mit offensichtlicher Bedeutung.

### Sync von Serienbrief-Antworten -> AktivenDB

Dieses Programm sollte in mehreren Phasen gestartet werden.

In der ersten Phase "Namen überprüfen" werden die in den Serienbrief-Antworten stehenden Namen mit denen in der AktivenDB abgeglichen. Da die Aufforderung zum Ausfüllen des Formulars ja nur an Mitglieder in der AktivenDB ergangen ist, sollten diese eigentlich immer übereinstimmen. Manch einer überlegt sich aber, daß er lieber Toni anstatt Anton heißt, o.ä. In diesem Fall hat man zwei Möglichkeiten: man ändert den Namen in der AktivenDB oder in der SB-Antwort. Ändern muß man aber. Auch auf andere Meldungen in dieser Phase sollte man reagieren, wie z.B. bei mehreren Antworten in den SB-Antworten alle bis auf die letzte löschen. Im Idealfall kommen in dieser Phase keine Meldungen mehr.

Dieses Programm ändert nur bestehende Daten, legt also keine Mitglieder neu an. Ist der Name also wirklich neu, kann man wieder überlegen, was zu tun ist. Die Antwort löschen? Dem künftigen Aktiven eine Email zum Erstanmeldungs-Formular schicken? Die Antworten-Zeile wird jedenfalls weiterhin ignoriert.

In der zweiten Phase "Nicht einverstandene löschen" werden die Mitglieder aus der AktivenDB gelöscht, die der Speicherung im Formular widersprochen haben.

Dann startet man die Phase "Änderungen übernehmen", läßt den Schalter aber noch auf "Erstmal testen". Das Ergebnis schaut man kritisch an. Sieht alles gut aus, betätigt man den Schalter, also "Jetzt aber wirklich", und startet mit banger Erwartung von neuem. Für den Fall, daß jetzt doch schreckliches passiert ist, wäre es hilfreich, vorher von der AktivenDB mittels phymyadmin einen Backup erstellt zu haben. Das steht aber auf einem anderen Blatt.

### Sync von Erstanlage-Antworten -> AktivenDB

Ähnlich dem vorhergehenden. Es fehlt aber die zweite Phase, und es werden nur Namen akzeptiert, die bisher nicht in der AktivenDB stehen. Wenn das der Fall ist, wird ein neues Mitglied angelegt, aber auf inaktiv gesetzt. Außerdem, falls die private Email bekannt ist, bekommt das neue Mitglied eine Email mit einer Bestätigung und einer Datei mit der Datenschutzerklärung (TBD). Diese Email wird im Namen (Von:) des Google-Benutzers gesendet!

Übrigens kann das Mitglied im Formular auch der Speicherung widersprechen. Man kann sich dann natürlich fragen, warum das Formular überhaupt abgeschickt wurde. Solche Antworten werden übersprungen, es wird also nichts in der AktivenDB angelegt.

### Sync von AktivenDB -> Google Groups (mit Admin-Berechtigung!)

Dieser Programmteil fängt damit an, daß er die Dateien aktdb_data/aktdb.json und gg_data/ggdb.json erzeugt, in denen alle aktuellen Daten aus AktivenDB und GoogleGroups stehen. Wenn diese Dateien schon existieren, wird ihr Inhalt gelesen, anstatt die Daten neu von AktivenDB und GG zu holen. Existieren diese Dateien von einem früheren Programmlauf, empfiehlt es sich, sie nach ggdb_YYMMDD.json und aktdb_YYYMMDD.json umzubenennen, wieder aus Dokumentationsgründen. Beim nächsten Programmstart werden aktdb.json und ggdb.json dann mit aktuellen Daten erzeugt, was immer einige Zeit dauert. So kann man den Zustand von AktivenDB und GG über einige Zeit dokumentieren. Indem man in diesen Dateien nach bestimmten Namen sucht, kann man so ihre Versionsgeschichte nachvollziehen. Dem gleichen Zweck dient natürlich auch die History der AktivenDB selber.

Oft bekommt man im Ausführungs-Zustand "Erst mal testen" einige Meldungen, denen man erstmal nachgehen muß. Daraus resultieren evtl. manuelle Änderungen in AktivenDB oder GG. Da dadurch der Inhalt von aktdb.json oder ggdb.json nicht mehr mit dem tatsächlichen Stand übereinstimmen, sollte man die Datei vor einem erneuten Lauf löschen.

Viele Meldungen haben informativen Character, etwa, welche inaktiven Mitglieder noch welchen AGs zugeordnet sind. Interessant wird es am Ende bei den Meldungen zu "Aktionen auf Google Groups". Diese gilt es besonders kritisch zu betrachten. Schlußendlich legt man den Schalter um, und das Programm nimmt seinen Lauf.

### Sende Serienbrief zur DB-Aktualisierung

Wie erwähnt, wird dieser Programmteil nur am Jahresende von Thomas Schubert "wirklich" ausgeführt. Mit "Erstmal testen" bekommt man aber jederzeit eine Liste der URLs mit vorbelegten Feldern, und wenn man darauf klickt, sieht man das Formular, was das Mitglied am Jahresende zu sehen bekäme.

## Sicherheit

Google-Admin-Berechtigungen werden von Andreas Schön vergeben. Z.B. habe ich ein Konto michael.uhlenberg@adfc-muenchen.de und ein Konto michael.uhlenberg.admin@adfc-muenchen.de. Somit kann man das Admin-Konto separat wieder löschen. Unbedingt sollte auch ein zweiter Faktor eingeschaltet werden. Die Berechtigungen für die Serienbrief-Tabelle sind gleichfalls sehr restriktiv zu vergeben. Die Datei credentials.json sollte nur an künftige Benutzer des Programms weitergegeben werden. Vor größeren Änderungen sollte ein Backup der AktivenDB gemacht werden. Über Backups von GG wird separat geredet.
