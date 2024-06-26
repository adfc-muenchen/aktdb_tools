import json
import http.client

hdrs = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*",
        "Authorization": "Bearer undefined"}


class AktDB:
    def __init__(self):
        pass

    def loginADB(self):
        with open("secret/aktdb.creds") as fp:
            body = fp.read()
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="POST", url="/auth/login", headers=hdrs, body=body)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        self.token = res["token"]
        print("token", self.token)

    def getDBMembers(self):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="GET", url="/api/members?token=" +
                   self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def getDBMember(self, id):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="GET", url="/api/member/" + str(id) +
                   "?token=" + self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def deleteDBMember(self, id):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="DELETE", url="/api/member/" + str(id) +
                   "?token=" + self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def getDBTeams(self):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="GET", url="/api/project-teams?token=" +
                   self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def getDBTeamMember(self, id):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="GET", url="/api/project-team/" +
                   str(id) + "?token=" + self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def setDBTeamEmail(self, id, email):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        body = json.dumps({"email": email})
        hc.request(method="PUT", url="/api/project-team/" +
                   str(id) + "?token=" + self.token, headers=hdrs, body=body)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def addDBMember(self, email_adfc, email_private, fname, lname):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        body = {"email_adfc": email_adfc,
                "first_name": fname, "last_name": lname}
        if email_private is not None:
            body["email_private"] = email_private
        body = json.dumps(body)
        hc.request(method="POST", url="/api/member" + "?token=" +
                   self.token, headers=hdrs, body=body)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def updDBMember(self, id, body):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        body = json.dumps(body)
        hc.request(method="PUT", url="/api/member/" + str(id) +
                   "?token=" + self.token, headers=hdrs, body=body)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def storeDBTeamMember(self, teamMember):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        body = {}  # TODO
        body = json.dumps(body)
        hc.request(method="POST", url="/api/project-team-member" + "?token=" +
                   self.token, headers=hdrs, body=body)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def deleteDBTeamMember(self, id):
        hc = http.client.HTTPSConnection("aktivendb.adfc-muenchen.de")
        hc.request(method="DELETE", url="/api/project-team-member/" + str(id) +
                   "?token=" + self.token, headers=hdrs)
        resp = hc.getresponse()
        # print("msg", resp.msg, resp.status, resp.reason)
        res = json.loads(resp.read())
        hc.close()
        return res

    def sortDB(self, dbMemberList, dbTeamList):
        for dbm in dbMemberList:
            for emKind in ["email_adfc", "email_private"]:
                if dbm[emKind] is not None and dbm[emKind] == "undef@undef.de":
                    dbm[emKind] = ""
        emailToMember = self.aktdb["emailToMember"]
        for emKind in ["email_adfc", "email_private"]:
            emailToMember[emKind] = {}
            for dbm in dbMemberList:
                email = dbm.get(emKind)
                if email is not None and email != "":
                    email = email.lower()
                    if emKind == "email_adfc":
                        if not email.endswith("@adfc-muenchen.de") and not email.endswith("@radentscheid-muenchen.de"):
                            print("ADFC_Email-Adresse falsch", email)
                    else:
                        if email.endswith("@adfc-muenchen.de"):
                            print("Private_Email-Adresse falsch", email)
                        em_adfc = dbm.get("email_adfc")
                        if em_adfc is not None and em_adfc != "":
                            continue
                    entries = emailToMember[emKind].get(email)
                    if entries is not None:
                        print(emKind, "mehrfach", email, *
                              [e["name"] for e in entries])
                    else:
                        entries = []
                        emailToMember[emKind][email] = entries
                    entries.append(dbm)
        teamName2Team = self.aktdb["teamName2Team"]
        for dbt in dbTeamList:
            teamName = dbt["name"]
            id = dbt["id"]
            teamName2Team[teamName] = dbt
            print("Team", teamName, id)
            detail = self.getDBTeamMembers(id)
            detail = {"members": detail["members"]}
            dbt["detail"] = detail
            memberList = dbt["detail"]["members"]
            memberListShortened = []
            for m in memberList:
                if m["active"] == "0" or m["active"] == 0:
                    print("inactive member ", m["name"], "in team ", teamName)
                    pass
                for emKind in ["email_adfc", "email_private"]:
                    if m[emKind] is not None and m[emKind] == "undef@undef.de":
                        m[emKind] = ""
                ptm = m["project_team_member"]
                ptm = {"member_role_id": +ptm["member_role_id"]}
                m = {"email_private": m["email_private"],
                     "email_adfc": m["email_adfc"],
                     "active": m["active"],
                     "name": m["name"],
                     "project_team_member": ptm
                     }
                memberListShortened.append(m)
            dbt["detail"]["members"] = memberListShortened
        self.dbMembers = self.aktdb["emailToMember"]
        self.dbTeams = self.aktdb["teamName2Team"]

        with open("aktdb_data/aktdb.json", "w") as fp:
            json.dump(self.aktdb, fp, indent=2)

    def getEntries(self):
        self.loginADB()
        try:
            with open("aktdb_data/aktdb.json", "r") as fp:
                self.aktdb = json.load(fp)
                self.dbMembers = self.aktdb["emailToMember"]
                self.dbTeams = self.aktdb["teamName2Team"]
        except Exception as _e:
            dbMemberList = self.getDBMembers()
            dbTeamList = self.getDBTeams()
            # dbMem = getDBMember(token, dbMembers[0]["id"])
            self.aktdb = {"emailToMember": {}, "teamName2Team": {}}
            self.sortDB(dbMemberList, dbTeamList)
        return {
            "dbMembers": self.dbMembers,
            "dbTeams": self.dbTeams,
        }
