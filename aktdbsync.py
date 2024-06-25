import datetime
import logging
from googleapiclient.discovery import build

nullMember = {
    "id": None,
    "name": "",
    "email_adfc": None,
    "email_private": None,
    "phone_primary": None,
    "phone_secondary": None,
    "address": None,
    "adfc_id": None,
    "admin_comments": None,
    "reference": "",  # ??
    "latest_first_aid_training": None,
    "next_first_aid_training": None,
    "gender": None,
    "interests": None,
    "latest_contact": None,
    "active": 1,
    "birthday": "",
    "status": "",
    "registered_for_first_aid_training": 0,
    "responded_to_questionaire": 1,
    "responded_to_questionaire_at": None,
    "first_name": "",
    "last_name": "",
    "project_teams": [],
}

nullAGMember = {
    "admin_comments": None,
    "id": None,
    "member_id": None,
    "member_role_id": 2,  # no role in excel
    "member_role_title": "Mitglied",
    "project_team_id": None,
}

colNames = []
colNamesIdx = {}
colNamesMap = {
    "Nachname": "last_name",
    "Vorname": "first_name",
    "Geschlecht": "gender",
    "Geburtsjahr": "birthday",
    "Postleitzahl": "address",
    "ADFC Email-Adresse": "email_adfc",
    "Eigene Email-Adresse": "email_private",
    "Telefonnummer 1": "phone_primary",
    "Telefonnummer 2": "phone_secondary",
    "AGs": "AGs",
    "Interessen": "interests",
    "ADFC-Mitgliedsnummer": "adfc_id",
    "Letztes Erste-Hilfe-Training": "latest_first_aid_training",
    "Nächstes Erste-Hilfe-Training": "next_first_aid_training",
    "Registriert für ein Erste-Hilfe-Training?": "registered_for_first_aid_training",
    "Mit Speicherung einverstanden?": "daccord",
    "Aktives Mitglied?": "active",
    "Zeitstempel": "responded_to_questionaire_at",
    "Status": "status",
}
emailRegexp = r"/[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/"


class AktDBSync:
    def __init__(self, doIt, creds, phase):
        self.doIt = doIt
        self.data = {}
        self.eingetragen = "Eingetragen"
        self.zusatzFelder = [self.eingetragen]
        self.completed = []
        self.phase = phase
        self.excelFile = None

    def validSheetName(self, sname):
        return sname == "Antworten" or sname == "Erstanlage"

    def getData(self):
        service = build('sheets', 'v4', credentials=self.creds)
        self.ssheet = service.spreadsheets()
        sheet_props = self.ssheet.get(
            spreadsheetId=self.spreadSheetId, fields="sheets.properties").execute()
        sheet_names = [sheet_prop["properties"]["title"]
                       for sheet_prop in sheet_props["sheets"]]

        for i, sname in enumerate(sheet_names):
            if not self.validSheetName(sname):
                continue
            try:
                rows = self.ssheet.values().get(spreadsheetId=self.spreadSheetId, range=sname). \
                    execute().get('values', [])
                self.data[sname] = rows
            except Exception as e:
                logging.exception("Kann Arbeitsblatt " +
                                  sname + " nicht laden")
                raise e

    def parseGS(self):
        res = {}
        for sheet in self.data.keys():
            vals = []
            srows = self.data[sheet]
            headers = srows[0]
            try:
                eingetragenX = headers.index(self.eingetragen)
            except:
                continue
            for r, srow in enumerate(srows[1:]):
                if len(srow) == 0:
                    continue
                if len(srow) > eingetragenX and srow[eingetragenX] != "":
                    continue
                row = {}
                for c, v in enumerate(srow):
                    if c < len(headers) and headers[c] != "":
                        key = headers[c]
                    else:
                        while c >= len(headers):
                            headers.append("")
                        key = headers[c] = chr(ord('A') + c)
                    row[key] = v
                row["Sheet"] = sheet
                vals.append(row)
                # Merken wo das Eingezogen-Datum gespeichert wird, nachdem ebics.xml geschrieben wurde
                self.completed.append(
                    {"sheet": sheet, "row": r + 1, "col": eingetragenX})
            res[sheet] = vals
        return res

    def getEntries(self):
        self.getData()
        self.checkColumns()
        entries = self.parseGS()
        return entries

    def addColumn(self, sheetName, colName):
        col = 0
        for row in self.data[sheetName]:
            col = max(col, len(row))
        self.addValue(sheetName, 0, col, colName)

    def addValue(self, sheetName, row, col, val):
        # row, col are 0 based
        values = [[val]]
        body = {"values": values}
        # A B ... Z AA AB ... AZ BA BB ... BZ ...
        col0 = "" if col < 26 else chr(ord('A') + int(col / 26) - 1)
        col1 = chr(ord('A') + int(col % 26))
        srange = sheetName + "!" + col0 + col1 + \
            str(row + 1)  # 0,0-> A1, 1,2->C2 2,1->B3
        if row == 0:
            try:
                result = self.ssheet.values().update(spreadsheetId=self.spreadSheetId,
                                                     range=srange, valueInputOption="RAW", body=body).execute()
            except:
                result = self.ssheet.values().append(spreadsheetId=self.spreadSheetId,
                                                     range=srange, valueInputOption="RAW", body=body).execute()
        else:
            result = self.ssheet.values().update(spreadsheetId=self.spreadSheetId,
                                                 range=srange, valueInputOption="RAW", body=body).execute()
        logging.log(logging.INFO, "result %s", result)

    def checkColumns(self):
        # Prüfen ob im sheet die Zusatzfelder angelegt sind
        for sheet in self.data.keys():
            srows = self.data[sheet]
            headers = srows[0]  # ein Pointer nach data, keine Kopie!
            try:
                _ = headers.index("Nachname")
            except:
                continue
            for h in self.zusatzFelder:
                if h not in headers:
                    self.addColumn(sheet, h)
                    headers.append(h)

    def fillEingetragen(self):
        # Spalte "Eingezogen" auf heutiges Datum setzen
        now = datetime.datetime.now()
        d = now.strftime("%Y-%m-%d")
        for c in self.completed:
            self.addValue(c["sheet"], c["row"], c["col"], d)

    def storeMembers(self, rows):
        if self.phase < 1 or self.phase > 4:
            raise Exception("phase invalid", self.phase)
