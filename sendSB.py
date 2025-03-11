import datetime
import re
import urllib
from aktdb import AktDB
from gg import Google
from utils import date2String

entries = {}
entries["last_name"] = "entry.1985977124"
entries["first_name"] = "entry.666565320"
entries["gender"] = "entry.1638875874"
entries["birthday"] = "entry.931621781"
entries["address"] = "entry.1777914664"
entries["adfc_id"] = "entry.98896261"
entries["email_adfc"] = "entry.2076354113"
entries["email_private"] = "entry.440890410"
entries["phone_primary"] = "entry.329829470"
entries["phone_secondary"] = "entry.1481160666"
entries["AGs"] = "entry.1781476495"
entries["interests"] = "entry.1674515812"
# entries["latest_first_aid_training"] = "entry.1254417615"
# entries["next_first_aid_training"] = "entry.285304371"
# entries["status"] = "entry.583933307"
# entries["Einverstanden mit Speicherung"] = "entry.273898972"
# entries["Aktiv"] = "entry.2103848384"

verifLinkUrl = "https://docs.google.com/forms/d/e/1FAIpQLSfDjK7m42eofskS164D2qTj8e-7ngHZeoiSgwsMWzB-AG-xfA/viewform?usp=pp_url"


def encodeURIComponent(s):
    return urllib.parse.quote(s)


class SendeSB:
    def __init__(self, doIt):
        self.doIt = doIt
        self.sheetData = []
        self.sheetName = "Antworten"
        self.members = []
        self.antwortMap = {}
        self.dbMap = {}
        self.mailTxt = ""
        self.nowDate = date2String(datetime.datetime.now())

        # statistik
        self.total = 0
        self.antworten = 0
        self.inaktiv = 0
        self.emails = 0

        self.aktDB = AktDB()
        self.google = Google(sheetName=self.sheetName)
        self.message = []

    def sendeSB(self):
        self.aktDB.loginADB()
        self.members = self.aktDB.getDBMembers()
        for row in self.members:
            name = row["last_name"].strip() + "," + \
                row["first_name"].strip()
            self.dbMap[name] = 1
        self.sheetData = self.google.getSheetData()
        # wer hat alles schon geantwortet?
        for row in self.sheetData[1:]:
            if len(row) < 15:
                continue
            name = row[1].strip() + "," + \
                row[2].strip()  # Nachname,Vorname
            if name == "":
                continue
            cnt = self.antwortMap.get(name)
            if cnt:
                self.antwortMap[name] = cnt + 1
            else:
                self.antwortMap[name] = 1
            if self.dbMap.get(name) is None:
                print(f"Antworten-Name {name} nicht in der AktivenDB")
        for name, cnt in self.antwortMap.items():
            if cnt > 1:
                print(f"{cnt}-fach geantwortet hat {name}")

        with open("SerienbriefEmail.html", "r", encoding="utf-8") as fp:
            self.mailtxt = fp.read()

        for row in self.members:
            self.sendeEmail(row)
        self.message.append(f"total {self.total} antworten {self.antworten} inaktiv {
            self.inaktiv} emails {self.emails}")
        return "\n".join(self.message)

    def sendeEmail(self, row):
        self.total += 1
        name = row["last_name"].strip() + "," + row["first_name"].strip()
        if self.antwortMap.get(name):
            print(f"Schon geantwortet: {name}")
            self.antworten += 1
            return
        if not row["active"]:
            print(f"Inaktiv: {name}")
            self.inaktiv += 1
            return
        emailTo1 = row["email_private"]
        if emailTo1 and emailTo1.startswith("undef"):
            emailTo1 = ""
        emailTo2 = row["email_adfc"]
        if emailTo2 and emailTo2.startswith("undef"):
            emailTo2 = ""
        emailTo = ""
        if emailTo1:
            emailTo = emailTo1
            if emailTo2:
                emailTo = emailTo + "," + emailTo2
        elif emailTo2:
            emailTo = emailTo2
        else:
            print("Keine Email Adresse für " + name)
            return
        self.emails += 1
        # anrede = f"Liebe(r) {row["first_name"].strip()} {
        #     row["last_name"].strip()}"
        anrede = f"Servus {row["first_name"].strip()}"
        verifLink = verifLinkUrl + self.row2Params(row)
        msg = "Email an " + name + " mit URL " + verifLink
        self.message.append(msg)
        print(msg)
        txt = self.mailtxt.format(anrede=anrede, verifLink=verifLink)

        if self.doIt:
            self.google.gmail_send_message(
                emailTo, "Erinnerung: Aktualisierung Deiner Daten in der AktivenDB", txt, useHtml=True)  # TODO
        pass

    def row2Params(self, row):
        params = []
        for k, v in row.items():
            if not v:
                continue
            entry = entries.get(k)
            if not entry:
                continue
            if k == "adfc_id":
                # v = 12345.0, number
                params.append("&" + entry + "=" + encodeURIComponent(str(v)))
            # elif k == "latest_first_aid_training":
            #     # v = date
            #     params.append("&" + entry + "=" + date2String(v))
            # elif k == "next_first_aid_training":
            #     ndate = date2String(v)
            #     if len(ndate) >= 10 and ndate <= self.nowDate:
            #         ndate = ""
            #     params.append("&" + entry + "=" + ndate)
            elif k == "phone_primary" or k == "phone_secondary":
                # v = string, remove blank, -
                params.append("&" + entry + "=" +
                              re.sub(r"[\s-]", "", str(v)))
            else:
                # v = simple string or number param
                if isinstance(v, str):
                    v = v.strip()
                params.append("&" + entry + "=" + encodeURIComponent(v))
        member = self.aktDB.getDBMember(row["id"])
        teamNames = [t["name"] for t in member["project_teams"]]
        # v = [ag1,ag2,ag3]
        for teamName in teamNames:
            params.append(
                "&" + entries["AGs"] + "=" + encodeURIComponent(teamName))

        return "".join(params)
