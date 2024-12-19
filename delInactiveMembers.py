from aktdb import AktDB


def isSet(v):
    if v is None:
        return False
    if v == 0:
        return False
    if v == "" or v == "0":
        return False
    return True


class DeleteInactiveMembers:
    def __init__(self, doIt):
        self.doIt = doIt
        self.members = []
        self.teams = []
        self.aktDB = AktDB()
        self.message = []
        pass

    def getAktdbData(self):
        self.aktDB.loginADB()
        self.members = self.aktDB.getDBMembers()
        self.teams = self.aktDB.getDBTeams()

    def deleteInactiveMembers(self):
        self.getAktdbData()
        for i, m in enumerate(self.members):
            if self.isInactive(m):
                if self.doIt:
                    self.aktDB.deleteDBMember(m["id"])
                self.message.append("Gelöscht: " + m["name"])
        return "\n".join(self.message)

    def isInactive(self, m):
        if isSet(m["active"]):
            return False
        if isSet(m["responded_to_questionaire_at"]):
            return False
        if isSet(m["email_adfc"]):
            return False
        m = self.aktDB.getDBMember(m["id"])
        mAGs = m["project_teams"]
        if len(mAGs) > 0:
            return False
        return True
