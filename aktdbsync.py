import copy
import datetime
import re
from aktdb import AktDB
from gg import Google
from utils import string2Date, date2String

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
    "created_at": None,
    "updated_at": None,
    "deleted_at": None,
    "with_details": None,
    "user": None,
}

nullAGMember = {
    "admin_comments": None,
    "id": None,
    "member_id": None,
    "member_role_id": 2,  # no role in excel
    "member_role_title": "Mitglied",
    "project_team_id": None,
}

colNamesMap = {
    "Nachname": "last_name",
    "Vorname": "first_name",
    "Geschlecht": "gender",
    "Geburtsjahr": "birthday",
    "Postleitzahl": "address",
    "ADFC Email-Adresse": "email_adfc",
    "Eigene Email-Adresse": "email_private",  # in Antworten
    "E-Mail-Adresse": "email_private",  # in Erstanlage
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
emailRegexp = r"[a-z0-9]+(?:\.[a-z0-9]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"


def nameOf(row):
    return row["Nachname"].strip() + ", " + row["Vorname"].strip()


class AktDBSync:
    def __init__(self, doIt, phase, sname):
        self.doIt = doIt
        self.sheetData = []
        self.eingetragen = "Eingetragen"
        self.zusatzFelder = [self.eingetragen]
        self.completed = []
        self.phase = phase
        self.sheetName = sname
        self.erstAnlage = sname == "Erstanlage"
        self.colNames = []
        self.colNamesIdx = {}
        self.entryMap = {}
        self.members = []
        self.teams = []
        self.aktDB = AktDB()
        self.message = []
        self.google = Google(sheetName=sname)

    def getSheetData(self):
        self.sheetData = self.google.getSheetData()
        self.colNames = self.sheetData[0]
        for i, colName in enumerate(self.colNames):
            self.colNamesIdx[colName] = i

    def getAktdbData(self):
        self.aktDB.loginADB()
        self.members = self.aktDB.getDBMembers()
        self.teams = self.aktDB.getDBTeams()

    def getFormEntries(self):
        vals = []
        srows = self.sheetData
        try:
            eingetragenX = self.colNames.index(self.eingetragen)
        except:
            print("Keine Spalte " + self.eingetragen +
                  " im Arbeitsblatt " + self.sheetName)
            return None
        for r, srow in enumerate(srows[1:]):
            if len(srow) == 0:
                continue
            if len(srow) > eingetragenX and srow[eingetragenX] != "":
                continue
            # first row = header, and rows in sheet are 1-based
            row = {"row": r + 2}
            for c, v in enumerate(srow):
                if c < len(self.colNames) and self.colNames[c] != "":
                    key = self.colNames[c]
                else:
                    while c >= len(self.colNames):
                        self.colNames.append("")
                    key = self.colNames[c] = chr(ord('A') + c)
                row[key] = v
            vals.append(row)
            # Merken wo das Eingetragen-Datum gespeichert wird
            self.completed.append({"row": r + 1, "col": eingetragenX})
        return vals

    def addColumn(self, colName):
        col = 0
        for row in self.sheetData:
            col = max(col, len(row))
        self.google.addValue(0, col, colName)

    def checkColumns(self):
        # Prüfen ob im sheet die Zusatzfelder angelegt sind
        try:
            _ = self.colNames.index("Nachname")
        except:
            print("Keine Spalte Nachname im Arbeitsblatt " + self.sheetName)
            return
        for h in self.zusatzFelder:
            if h not in self.colNames:
                self.addColumn(h)
                self.colNames.append(h)

    def fillEingetragen(self):
        # Spalte "Eingezogen" auf heutiges Datum setzen
        now = datetime.datetime.now()
        d = now.strftime("%Y-%m-%d")
        for c in self.completed:
            self.google.addValue(c["row"], c["col"], d)

    def setEntryMap(self, row):
        name = nameOf(row)
        prev = self.entryMap.get(name)
        self.entryMap[name] = row
        if prev is not None:
            print("Doppelter Eintrag für " + name + ", vorherige Reihe:" +
                  str(prev["row"]) + ", jetzt:" + str(row["row"]))
            for colName in self.colNames:
                if colName == "Letztes Erste-Hilfe-Training":
                    prev[colName] = date2String(prev[colName])
                    row[colName] = date2String(row[colName])
                if prev.get(colName) != row.get(colName):
                    print("\t" + colName +
                          ": " + str(prev.get(colName)) + " => " + str(row.get(colName)))

    def storeMembers(self, rows):
        if self.phase < 1 or self.phase > 3:
            raise Exception("phase invalid", self.phase)
        with open("begruessung.html", "r", encoding="utf-8") as fp:
            begrtxt = fp.read()
        # TODO: doppelte Einträge filtern!
        for row in rows:
            vorname = row["Vorname"].strip()
            nachname = row["Nachname"].strip()
            if self.phase == 1:
                self.setEntryMap(row)
            x = [i for i, m in enumerate(self.members) if m["first_name"].strip(
            ) == vorname and m["last_name"].strip() == nachname]
            if self.erstAnlage:
                if len(x) != 0:
                    self.message.append("Schon bekannt: " + nameOf(row))
                    continue  # for erstanlage member must be unknown
                if row["Mit Speicherung einverstanden?"] == "Nein":
                    self.message.append(
                        "Nicht mit Speicherung einverstanden: " + nameOf(row))
                    continue
            else:
                if len(x) == 0:
                    if row["Mit Speicherung einverstanden?"] == "Nein":
                        self.message.append(
                            "Schon gelöscht wurde: " + nameOf(row))
                        continue
                    self.message.append("Unbekannt oder neu: " + nameOf(row))
                    continue  # we do not add members to AktivenDB here
            if self.phase == 1:
                continue
            if self.phase == 2 and not self.erstAnlage:  # delete member if storage not wanted
                if len(x) > 0 and row["Mit Speicherung einverstanden?"] == "Nein":
                    if self.doIt:
                        self.aktDB.deleteDBMember(row["id"])
                    del self.members[x[0]]
                    self.message.append("Gelöscht: " + nameOf(row))
                continue
            exi = None if len(x) == 0 else self.members[x[0]]
            member = self.mapRow(row, exi)
            now = datetime.datetime.now()
            if exi:
                if member["changed"] and self.phase == 3 and self.doIt:
                    id = member["id"]
                    del member["id"]
                    self.aktDB.updDBMember(id, member)
                    member["id"] = id
                    self.google.addValue(
                        row["row"]-1, self.colNamesIdx[self.eingetragen], date2String(now, dateOnly=False))
            elif self.erstAnlage:
                if self.phase == 3 and self.doIt:
                    # bei Erstanlage erst mal auf inaktiv setzen
                    member["active"] = 0
                    self.aktDB.addDBMember(member)
                    self.google.addValue(
                        row["row"]-1, self.colNamesIdx[self.eingetragen], date2String(now, dateOnly=False))
                    if member["email_private"]:
                        anrede = "Liebe(r) "
                        if member["gender"] == "M":
                            anrede = "Lieber "
                        elif member["gender"] == "F":
                            anrede = "Liebe "
                        anrede += member["first_name"] + \
                            " " + member["last_name"]
                        try:
                            data = {"anrede": anrede, **member}
                            for k, v in data.items():
                                if v is None:
                                    data[k] = "-"
                            txt = begrtxt.format_map(data)
                            self.google.gmail_send_message(
                                dest=member["email_private"],
                                subject="Bestätigung der Eintragung in die AktivenDB des ADFC München eV",
                                body=txt,
                                # attachment_filename="Datenschutzerklärung.pdf",
                                useHtml=True)
                        except Exception as e:
                            msg = "Konnte Bestätigungsemail an " + \
                                nameOf(row) + " nicht senden :" + str(e)
                            print(msg)
                            self.message.append(msg)
                continue
            if member.get("id") is None:
                print("???")  # TODO
                continue
            # now we get the member again, but this time with project_teams
            exiMember = self.aktDB.getDBMember(member["id"])
            exiAGs = exiMember["project_teams"]
            for agName in member["project_teams"]:
                x = [i for i, t in enumerate(exiAGs) if t["name"] == agName]
                if len(x) > 0:
                    continue
                agMember = copy.copy(nullAGMember)
                agMember["member_id"] = member["id"]
                ag = [a for a in self.teams if a["name"] == agName]
                if len(ag) == 0:
                    print("Kann AG " + agName + " für " +
                          nameOf(row) + " nicht finden")
                    continue
                ag = ag[0]
                agMember["project_team_id"] = ag["id"]
                self.message.append(
                    "Mitglied: " + nameOf(row) + " möchte der " + ag["name"] + " beitreten")
                # self.aktDB.storeDBTeamMember(agMember)
                # nicht mehr, soll der AG-Leiter machen
            for team in exiMember["project_teams"]:
                agName = team["name"]
                x = [i for i, t in enumerate(
                    member["project_teams"]) if t == agName]
                if len(x) == 0:
                    tm = team["project_team_member"]
                    self.message.append("Mitglied: " + nameOf(row) +
                                        " tritt aus der " + agName + " aus")
                    if self.phase == 3 and self.doIt:
                        self.aktDB.deleteDBTeamMember(tm.id)
        return "\n".join(self.message)

    def mapRow(self, row, exi):
        nullMember["project_teams"] = []
        member = copy.copy(nullMember) if exi is None else copy.copy(exi)
        savedMember = copy.copy(member)
        member["responded_to_questionaire"] = 1
        if member.get("project_teams") is None:
            member["project_teams"] = []
        for colName in self.colNames:
            dbColName = colNamesMap.get(colName)
            if dbColName is None:
                continue
            val = row.get(colName)
            if dbColName.startswith("email_") and (val is None or val == ""):
                val = "undef@undef.de"
            if val is None or val == "":
                continue
            if colName == "AGs":
                for ag in self.teams:
                    if val.find(ag["name"]) >= 0:
                        member["project_teams"].append(ag["name"])
            elif dbColName == "active":
                member[dbColName] = 0 if val == "Nein" else 1
            elif dbColName == "registered_for_first_aid_training":
                member[dbColName] = 1 if val.lower().startsWith("ja") else 0
            elif dbColName.startswith("email_"):
                val = val.lower()
                m = re.match(emailRegexp, val)
                if m is None or m.string != val:
                    print("Ungültige Email-Adresse " + val)
                    val = ""
                member[dbColName] = val
            else:
                if isinstance(val, str):
                    val = val.strip()
                member[dbColName] = val
        member["name"] = nameOf(row)
        member["latest_first_aid_training"] = date2String(string2Date(
            member["latest_first_aid_training"]))
        member["next_first_aid_training"] = date2String(string2Date(
            member["next_first_aid_training"]))
        member["latest_contact"] = date2String(
            string2Date(member["latest_contact"]))
        member["datum"] = member["responded_to_questionaire_at"]
        member["responded_to_questionaire_at"] = date2String(
            string2Date(member["responded_to_questionaire_at"]))
        member["changed"] = self.logDiffs(member, savedMember, exi) is not None
        return member

    def logDiffs(self, member, prev, exi):
        msg = ""
        # fields not affected by questionaire
        del member["admin_comments"]
        del member["reference"]
        del member["latest_contact"]
        del member["created_at"]
        del member["updated_at"]
        del member["deleted_at"]
        del member["with_details"]
        del member["user"]
        if exi:
            del member["first_name"]
            del member["last_name"]

        if member["email_adfc"] != prev["email_adfc"]:
            if (member["email_adfc"] == "" or member["email_adfc"] == "undef@undef.de") and prev["email_adfc"] != "" and prev["email_adfc"] != "undef@undef.de":
                member["email_adfc"] = prev["email_adfc"]
            else:
                msg += "email_adfc:" + \
                    F'{prev["email_adfc"]}' + "=>" + \
                    F'{member["email_adfc"]}' + " "
        elif exi or self.erstAnlage:
            del member["email_adfc"]

        if member["email_private"] != prev["email_private"]:
            if (member["email_private"] == "" or member["email_private"] == "undef@undef.de") and prev["email_private"] != "" and prev["email_private"] != "undef@undef.de":
                member["email_private"] = prev["email_private"]
            else:
                msg += "email_private:" + \
                    F'{prev["email_private"]}' + "=>" + \
                    F'{member["email_private"]}' + " "
        elif exi:
            del member["email_private"]

        if member["phone_primary"] != prev["phone_primary"]:
            msg += "phone_primary:" + \
                F'{prev["phone_primary"]}' + "=>" + \
                F'{member["phone_primary"]}' + " "
        elif exi:
            del member["phone_primary"]

        if member["phone_secondary"] != prev["phone_secondary"]:
            msg += "phone_secondary:" + \
                F'{prev["phone_secondary"]}' + "=>" + \
                F'{member["phone_secondary"]}' + " "
        elif exi:
            del member["phone_secondary"]

        if member["address"] != prev["address"]:
            msg += "address:" + F'{prev["address"]}' + \
                "=>" + F'{member["address"]}' + " "
        elif exi:
            del member["address"]

        if member["gender"] != prev["gender"]:
            msg += "gender:" + F'{prev["gender"]}' + \
                "=>" + F'{member["gender"]}' + " "
        elif exi:
            del member["gender"]

        if member["birthday"] != prev["birthday"]:
            msg += "birthday:" + F'{prev["birthday"]
                                    }' + "=>" + F'{member["birthday"]}' + " "
        elif exi:
            del member["birthday"]

        if member["interests"] != prev["interests"]:
            msg += "interests:" + F'{prev["interests"]
                                     }' + "=>" + F'{member["interests"]}' + " "
        elif exi:
            del member["interests"]

        if member["adfc_id"] != prev["adfc_id"]:
            msg += "adfc_id:" + F'{prev["adfc_id"]}' + \
                "=>" + F'{member["adfc_id"]}' + " "
        elif exi:
            del member["adfc_id"]

        if member["active"] != prev["active"]:
            msg += "active:" + F'{prev["active"]}' + \
                "=>" + F'{member["active"]}' + " "
        elif exi:
            del member["active"]

        if member["status"] != prev["status"]:
            msg += "status:" + F'{prev["status"]}' + \
                "=>" + F'{member["status"]}' + " "
        elif exi:
            del member["status"]

        if member["responded_to_questionaire"] != prev["responded_to_questionaire"]:
            msg += "responded_to_questionaire:" + \
                F'{prev["responded_to_questionaire"]}' + "=>" + \
                F'{member["responded_to_questionaire"]}' + " "
        elif exi:
            del member["responded_to_questionaire"]

        if member["responded_to_questionaire_at"] != prev["responded_to_questionaire_at"]:
            msg += "responded_to_questionaire_at:" + \
                F'{prev["responded_to_questionaire_at"]}' + "=>" + \
                F'{member["responded_to_questionaire_at"]}' + " "
        elif exi:
            del member["responded_to_questionaire_at"]

        if exi is None:
            if member["latest_first_aid_training"]:
                self.message.append("Neues Mitglied " + member["name"] + " möchte als EHK-Datum " +
                                    F'{member["latest_first_aid_training"]}')
                member["latest_first_aid_training"] = None
        else:
            if member["latest_first_aid_training"] and member["latest_first_aid_training"] != exi["latest_first_aid_training"]:
                self.message.append("Mitglied: " + F'{member["name"]}' + " möchte das EHK-Datum von " + F'{
                    exi["latest_first_aid_training"]}' + " auf " + F'{member["latest_first_aid_training"]}' + " ändern")
                member["latest_first_aid_training"] = exi["latest_first_aid_training"]
        if msg == "":
            return None
        msg = ("New" if exi is None else "Existing") + \
            " Member:" + member["name"] + ": " + msg
        self.message.append(msg)
        return msg
