# !/usr/bin/env python
# TODO: inaktiv-> nicht in alle_aktiven, nicht in irgendeiner Gruppe
# TODO: normales mitglied das nur in OG ist nicht in alle_aktiven tun
# TODO: OGs nicht in aktive@... - händisch OGs aus aktive@groups entfernen (ich habe OG Ismaning entfernt)
# TODO: ABER: OG Leitungen in aktive

# Python Quickstart
# https://developers.google.com/admin-sdk/directory/v1/quickstart/python
# Admin Directory API
# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

# https://stackoverflow.com/questions/62166670/getting-a-403-trying-to-list-directory-users

# manage custom user fields
# https://developers.google.com/admin-sdk/directory/v1/guides/manage-schemas

import json
import sys

from gg import Google
from aktdb import AktDB


def isEmpty(s):
    return s is None or s == ""


class GGSync():
    def __init__(self, doIt):
        self.google = Google(None)
        self.aktdb = AktDB()
        aktdbEntries = self.aktdb.getEntries()
        self.dbMembers = aktdbEntries["dbMembers"]
        self.dbTeams = aktdbEntries["dbTeams"]
        self.doIt = doIt
        self.message = []

        # TODO: funktion für mapGrpG2A, mapGrpA2G
        with open("conf/mapping.json", "r") as fp:
            self.mapGrpA2G = json.load(fp)
            self.mapGrpG2A = {self.mapGrpA2G[k]: k for k in self.mapGrpA2G.keys()}
        with open("conf/ignore_groups.json", "r") as fp:
            self.ignoreGroups = json.load(fp)

        self.spclGroups = ["NoResponse", "Alle Aktiven", "Keine Emails"]
        try:
            with open("gg_data/ggdb.json", "r") as fp:
                self.ggdb = json.load(fp)
                self.ggUsers = self.ggdb["email2User"]
                self.ggGroups = self.ggdb["groupName2Group"]
        except Exception as _e:
            print("get users list from GG")
            self.ggUsers = self.google.getGGUsers()
            print("get groups list from GG")
            self.ggGroups = self.google.getGGGroups()
            self.sortGG()

        # self.noResponseGrp = self.google.getGGGroup("noresponse@adfc-muenchen.de")

        # grp = ggGroups["MUTest"]
        # grp["members"] = self.google.getGGGroupMemberNames(grp["id"])
        # with open("ggdb.json", "w") as fp:
        #     json.dump(ggdb, fp, indent=2)

    def sortGG(self):
        self.ggdb = {"email2User": self.ggUsers,
                     "groupName2Group": self.ggGroups}

        aktTeamNames = list(self.dbTeams.keys())
        for g in sorted(self.ggGroups.values(), key=lambda g: g["name"]):
            g["members"] = []
            grpName = g["name"]
            if grpName in self.ignoreGroups:
                continue
            teamName = grpName
            if teamName.endswith("Leitung"):
                teamName = teamName.replace(" Leitung", "")
            if teamName.endswith("SprecherInnen"):
                teamName = teamName.replace(" SprecherInnen", "")
            mapped = self.mapGrpG2A.get(teamName)
            if mapped is not None:
                teamName = mapped
            elif teamName.startswith("Ortsgruppe "):
                teamName = "OG " + teamName[11:]
            if teamName in self.ignoreGroups:
                continue
            if teamName not in aktTeamNames and teamName not in self.spclGroups:
                continue
            print("get groupmembers from", grpName)
            # self.google.getGGAccessSettings(g)
            g["members"] = grpMembers = self.google.getGGGroupMemberNames(
                g["id"])
            for gm in grpMembers:
                gu = self.ggUsers.get(gm["email"])
                if gu is None:
                    continue
                memberIn = gu.get("memberIn")
                if memberIn is None:
                    gu["memberIn"] = memberIn = {}
                memberIn[teamName] = gm["role"]
        with open("gg_data/ggdb.json", "w") as fp:
            json.dump(self.ggdb, fp, indent=2)

    def createGroup(self, grpName, leitung=False):
        grplName = grpName.lower()
        if "vorstand" in grpName:
            return
        # if "test" in grplName or "leitung" in grplName or "fundraising" in grplName or "radfahrschule" in grplName:
        grpEmail = grplName.replace(" ", "-") \
            .replace("ortsgruppe", "og") \
            .replace("ä", "ae") \
            .replace("ö", "oe") \
            .replace("ü", "ue")
        if leitung:
            if "ortsgruppe" in grplName:
                grpEmail += "_sprecherinnen"
                desc = "SprecherInnen der " + grpName
                grpName += " SprecherInnen"
            else:
                grpEmail += "_leitung"
                desc = "Leitung der " + grpName
                grpName += " Leitung"
        else:
            grpEmail += "_aktive"
            desc = "Aktive der " + grpName
        grpEmail += "@groups.adfc-muenchen.de"
        grp = {
            "kind": "admin#directory#group",
            "email": grpEmail,
            "name": grpName,
            "description": desc,
        }
        print("Action: create group", grpName)
        self.message.append("Erzeuge neue Gruppe" + grpName)
        if self.doIt:
            res = self.google.createGroup(grp)
            if res is None:
                return None, None
        return grpName, res

    def createMissingGroups(self):
        # compare AG names
        aktTeamNames = list(self.dbTeams.keys())
        ggGrpNames = list(self.ggGroups.keys())
        aktTeamNames.sort()
        ggGrpNames.sort()
        # print("a", aktTeamNames)
        # print("g", ggGrpNames)
        addedGroup = False
        for atn in aktTeamNames:
            if atn in self.ignoreGroups:
                continue
            grpName = atn
            mapped = self.mapGrpA2G.get(grpName)
            if mapped is not None:
                grpName = mapped
            elif grpName.startswith("OG "):
                grpName = "Ortsgruppe " + grpName[3:]
            if "Vorstand" in grpName:
                pass
            if grpName in self.ignoreGroups:
                continue
            if grpName not in ggGrpNames:
                if self.doIt:
                    name, res = self.createGroup(grpName, leitung=False)
                    if res is not None:
                        self.ggGroups[name] = res
                        addedGroup = True
            leitung = " SprecherInnen" if "Ortsgruppe" in grpName else " Leitung"
            if (grpName + leitung) in self.ignoreGroups:
                continue
            if (grpName + leitung) not in ggGrpNames:
                if self.doIt:
                    name, res = self.createGroup(grpName, leitung=True)
                    if res is not None:
                        addedGroup = True
        if addedGroup:
            print("Please delete ggdb.json and start again")
            sys.exit(0)

    def printUnmatchedDBGroups(self):
        aktTeamNames = list(self.dbTeams.keys())
        aktTeamNames.sort()
        ggGrpNames = list(self.ggGroups.keys())
        ggGrpNames.sort()
        print("\n\nAG/OG Missing in AktivenDB")
        for grpName in ggGrpNames:
            if grpName.endswith("Leitung") or "Sprecher" in grpName:
                continue
            mapped = self.mapGrpG2A.get(grpName)
            if mapped is not None:
                grpName = mapped
            elif grpName.startswith("Ortsgruppe "):
                grpName = "OG " + grpName[11:]
            if grpName not in aktTeamNames:
                print(grpName)
            else:
                print("Matching", grpName)

    # def cleanNoResp(self):
    #     print("Clean up NoResponse Group in Ggroups")
    #     noRespMembers = self.google.getGGGroupMemberNames(self.noResponseGrp.get("id"))
    #     noRespMemberNames = [m.get("email") for m in noRespMembers]
    #     aktMembers = {}
    #     for emKind in ["email_adfc", "email_private"]:
    #         aktMemberNames = list(self.dbMembers[emKind].keys())
    #         for aktMemberName in aktMemberNames:
    #             aktMemberList = self.dbMembers[emKind].get(aktMemberName)
    #             for aktMember in aktMemberList:
    #                 em_adfc = aktMember.get("email_adfc")
    #                 if not isEmpty(em_adfc):
    #                     aktMembers[em_adfc.lower()] = aktMember
    #                 em_priv = aktMember.get("email_private")
    #                 if not isEmpty(em_priv):
    #                     aktMembers[em_priv.lower()] = aktMember
    #
    #     for gun in noRespMembers:
    #         gun = gun.get("email")
    #         aktMember = aktMembers.get(gun)
    #         if aktMember is None \
    #                 or aktMember.get("active") == "0" \
    #                 or aktMember.get("active") == 0 \
    #                 or aktMember["responded_to_questionaire"] != 0 \
    #                 or not isEmpty(aktMember["responded_to_questionaire_at"]):
    #             print("Aktion: delete", gun, "from NoResponse")
    #             self.message.append("")
    #             if self.doIt:
    #                 self.google.delMemberFromGroup(self.noResponseGrp, gun)
    #             noRespMemberNames.remove(gun)
    #
    #     for aktMemberName in aktMembers.keys():
    #         if aktMemberName in noRespMemberNames:
    #             continue
    #         aktMember = aktMembers.get(aktMemberName)
    #         if aktMember.get("active") == "0" or aktMember.get("active") == 0:
    #                 continue
    #         em_adfc = aktMember.get("email_adfc")
    #         if em_adfc is not None:
    #             em_adfc = em_adfc.lower()
    #         # don't add private email if adfc email is already set
    #         if not isEmpty(em_adfc) and em_adfc in noRespMemberNames:
    #             continue
    #         if aktMember["responded_to_questionaire"] == 0 \
    #                 and isEmpty(aktMember["responded_to_questionaire_at"]):
    #             print("Aktion: add", aktMemberName, "to NoResponse")
    #             self.message.append("")
    #             noRespMemberNames.append(aktMemberName)
    #             if self.doIt:
    #                 self.google.addMemberToGroup(self.noResponseGrp, aktMemberName, "MEMBER")

    def findDBUser(self, fname, lname):
        for emKind in ["email_adfc", "email_private"]:
            for members in self.dbMembers[emKind].values():
                for member in members:
                    if member.get("first_name") == fname and member.get("last_name") == lname:
                        return member
        return None

    def addToDBMembers(self, email_adfc, email_private, fname, lname):
        self.dbMembers["email_adfc"][email_adfc.lower()] = [{
            "name": lname + ", " + fname,
            "email_adfc": email_adfc,
            "email_private": email_private,
            "first_name": fname,
            "last_name": lname,
        }]

    def addEmailAdfcInTeams(self, email_adfc, email_private):
        for team in self.dbTeams.values():
            for m in team["detail"]["members"]:
                if m["email_private"] == email_private:
                    m["email_adfc"] = email_adfc

    def addGGUsersToDB(self):
        aktMemberNames = list(self.dbMembers["email_adfc"].keys())
        aktMemberNames = [e.lower() for e in aktMemberNames]
        aktMemberNames.sort()
        ggUserNames = list(self.ggUsers.keys())
        ggUserNames.sort()
        print("\n\nMember Missing in AktivenDB")
        for gun in ggUserNames:
            if gun.startswith("webadmin"):
                continue
            x = gun.find('@')
            cnt = gun.count('.', 0, x)
            ggu = self.ggUsers[gun]
            if cnt != 1 or gun in aktMemberNames:
                continue
            emails = ggu.get("emails")
            priv = None
            addr = None
            name = ggu.get('name')
            fname = name.get('givenName')
            lname = name.get('familyName')
            lname = lname.replace(" ADFC München", "")
            for email in emails:
                addr = email.get("address")
                if addr.find("@adfc-muenchen.de") > 0:
                    addr = None
                    continue
                if addr.find("@radentscheid-muenchen.de") > 0:
                    addr = None
                    continue
                priv = self.dbMembers["email_private"].get(addr)
                if priv is not None:
                    priv = priv[0]  # ??
                break
            if priv is None:
                priv = self.findDBUser(fname, lname)
            if priv is not None:
                email_private = priv.get("email_private")
                id = priv.get("id")
                print("addaddr", gun, "to", email_private, "with id", id)
                self.message.append(
                    "Private Adresse " + email_private + " zu " + gun + " hinzugefügt")
                if self.doIt:
                    self.updDBMember(id, "email_adfc", gun)
                priv["email_adfc"] = gun
                self.dbMembers["email_adfc"][gun] = [priv]
                self.addEmailAdfcInTeams(gun, addr)
                continue
            print("Google user not in AktivenDB:", gun, addr, fname, lname)
            # if self.doIt:
            #     m = {"email_adfc": gun, "first_name": fname, "last_name": lname}
            #     if addr is not None:
            #         m["email_private"] = addr
            #     self.addDBMember(m)
            self.addToDBMembers(gun, addr, fname, lname)

            print("Not in AktivenDB:", fname, lname, gun)

    def addTeamEmailAddressesToAktb(self):
        for team in sorted(self.dbTeams.values(), key=lambda t: t["name"]):
            name = team["name"]
            mapped = self.mapGrpA2G.get(name)
            if mapped is not None:
                name = mapped
            elif name.startswith("OG "):
                name = "Ortsgruppe " + name[3:]
            grp = self.ggGroups.get(name)
            if grp is None:
                continue
            if team["email"] != grp["email"]:
                # print("a:", team["email"], "g", grp["email"])
                if name.find("Radfahrschule") > 0:
                    continue
                else:
                    print("Action(in AktivenDB): set email of team",
                          name, "to", grp["email"])
                    self.message.append(
                        "In der AktivenDB setze email von " + name + " auf " + grp["email"])
                if self.doIt:
                    self.setDBTeamEmail(team["id"], grp["email"])

    def memberInGroup(self, grpName, email):
        grp = self.ggGroups.get(grpName)
        if grp is None:
            return None
        members = grp["members"]
        emails = [m["email"] for m in members]
        return email in emails

    def addToGG(self):
        print("\nAktionen auf Google Groups:")
        addedEmails = {}
        for team in sorted(self.dbTeams.values(), key=lambda t: t["name"]):
            teamName = team["name"]
            if teamName in self.ignoreGroups:
                continue
            if "Vorstand" in teamName:
                continue
            grpName = teamName
            mapped = self.mapGrpA2G.get(teamName)
            if mapped is not None:
                grpName = mapped
            elif teamName.startswith("OG "):
                grpName = "Ortsgruppe " + teamName[3:]
            grp = self.ggGroups.get(grpName)
            if grp is None:
                print("cannot find group", grpName, "for team", teamName)
                continue
            for member in team["detail"]["members"]:
                if member["email_private"] is None:
                    member["email_private"] = ""
                if member["email_adfc"] is None:
                    member["email_adfc"] = ""
                if member["active"] == "0" or member["active"] == 0:
                    continue
                aktRole = +member["project_team_member"]["member_role_id"]
                ggRole = "MANAGER" if aktRole == 1 else "MEMBER"
                adfcEmail = member["email_adfc"].lower()
                user = None if adfcEmail == "" else self.ggUsers.get(adfcEmail)
                if adfcEmail != "" and user is None:
                    print("Aktb member ", adfcEmail,
                          "of team", teamName, "not in GG")
                    member["missingUser"] = True
                    # Create User?
                    continue
                privEmail = member["email_private"].lower()

                if privEmail != "" and user is not None:
                    emails = [email["address"] for email in user["emails"]]
                    if privEmail not in emails and addedEmails.get(privEmail + adfcEmail) is None:
                        member["missingEmail"] = True
                        user["missingEmail"] = True
                        print("Action: add email", privEmail,
                              "to user", adfcEmail)
                        self.message.append(
                            "Private Adresse " + privEmail + " zu " + adfcEmail + " hinzugefügt")
                        if self.doIt:
                            self.google.addEmailToUser(user, privEmail)
                        addedEmails[privEmail + adfcEmail] = True

                foundEmail = None
                if adfcEmail != "" and self.memberInGroup(grpName, adfcEmail):
                    foundEmail = adfcEmail
                elif privEmail != "" and self.memberInGroup(grpName, privEmail):
                    foundEmail = privEmail
                email = adfcEmail or privEmail
                gmember = None
                if email == "":
                    print("no email for ", member["name"])
                    continue
                if adfcEmail != "" and foundEmail is not None and foundEmail != adfcEmail:
                    print("Action: add member", adfcEmail,
                          "in addition of", foundEmail, "to", grpName)
                    self.message.append("Zusätzliche Adresse " + adfcEmail +
                                        " für " + foundEmail + " zu " + grpName + " hinzugefügt")
                    if self.doIt:
                        self.google.addMemberToGroup(grp, adfcEmail, ggRole)
                    grp["members"].append({"email": adfcEmail, "role": ggRole})
                elif foundEmail is None:
                    print("Action: add member", email, "to", grpName)
                    self.message.append(
                        "Mitglied " + email + " zu " + grpName + " hinzugefügt")
                    if self.doIt:
                        self.google.addMemberToGroup(grp, email, ggRole)
                    grp["members"].append({"email": email, "role": ggRole})
                else:
                    gmembers = grp["members"]
                    gmember = next(
                        (gm for gm in gmembers if gm["email"] == foundEmail), None)
                    if gmember is not None and ggRole != gmember["role"]:
                        print("Action: change role of ", foundEmail, "in group", grpName, "from", gmember["role"], "to",
                              ggRole)
                        self.message.append(
                            "Rolle von " + foundEmail + " in " + grpName + " von " + gmember["role"] + " zu " + ggRole + " geändert")
                        if self.doIt:
                            self.google.chgGGMemberRole(grp, email, ggRole)

                lgrp = self.ggGroups.get(grpName + " Leitung")
                if lgrp is None:
                    lgrp = self.ggGroups.get(grpName + " SprecherInnen")
                if lgrp is None:
                    print("No leader group for", email, "of group", grpName)
                    continue
                lgrpName = lgrp["name"]
                foundEmail = None
                if adfcEmail != "" and self.memberInGroup(lgrpName, adfcEmail):
                    foundEmail = adfcEmail
                elif privEmail != "" and self.memberInGroup(lgrpName, privEmail):
                    foundEmail = privEmail
                if ggRole == 'MANAGER':  # Vorsitz, add to group Leitung/Sprecherinnen
                    if foundEmail is None:
                        print("Action: add member", email, "to", lgrpName)
                        self.message.append(
                            "Mitglied " + email + " zu " + lgrpName + " hinzugefügt")
                        if self.doIt:
                            self.google.addMemberToGroup(
                                lgrp, email, "MEMBER")  # TODO MANAGER?
                        lgrp["members"].append(
                            {"email": email, "role": "MEMBER"})
                elif gmember is not None and gmember["role"] == "MANAGER":
                    if foundEmail is not None:
                        print("Action: remove member",
                              foundEmail, "from", lgrpName)
                        self.message.append(
                            "Entferne " + foundEmail + " von " + lgrpName)
                        if self.doIt:
                            self.google.delMemberFromGroup(lgrp, foundEmail)
                        lgrp["members"] = [m for m in lgrp["members"]
                                           if m["email"] != foundEmail]

    def removeFromGG(self):
        aktTeamNames = list(self.dbTeams.keys())
        aktTeamNames.sort()
        missingAktdb = {}
        noEmail = {}
        for grp in sorted(self.ggGroups.values(), key=lambda g: g["name"]):
            grpName = grp["name"]
            if grpName in self.ignoreGroups:
                continue
            teamName = grpName
            leiterGrp = False
            if teamName.endswith("Leitung"):
                teamName = teamName.replace(" Leitung", "")
                leiterGrp = True
            if teamName in self.ignoreGroups:
                continue
            if teamName.endswith("SprecherInnen"):
                teamName = teamName.replace(" SprecherInnen", "")
                leiterGrp = True
            mapped = self.mapGrpG2A.get(teamName)
            if mapped is not None:
                teamName = mapped
            elif teamName.startswith("Ortsgruppe "):
                teamName = "OG " + teamName[11:]
            if teamName not in aktTeamNames:
                continue
            team = self.dbTeams[teamName]
            gmembers = grp["members"]
            gmemberEmails = [gm["email"] for gm in gmembers]  # XXX
            amembers = []
            for tmember in team["detail"]["members"]:
                adfcEmail = tmember["email_adfc"].lower()
                privEmail = tmember["email_private"].lower()
                email = adfcEmail or privEmail
                if email == "" and noEmail.get(tmember["name"]) is None:
                    print("no email", tmember["name"], "in group", grpName)
                    noEmail[tmember["name"]] = 1
                    continue
                if leiterGrp:
                    if +tmember["project_team_member"]["member_role_id"] == 1:
                        if email != adfcEmail:
                            print("leiter", email, "of group",
                                  grpName, "is no user")
                            # continue ??
                        amembers.append(email)
                else:
                    amembers.append(email)
            for gmemberEmail in gmemberEmails:
                if gmemberEmail not in amembers:
                    if "leitung@" in gmemberEmail:
                        continue
                    if self.dbMembers["email_adfc"].get(gmemberEmail) is None \
                            and self.dbMembers["email_private"].get(gmemberEmail) is None:
                        if missingAktdb.get(gmemberEmail) is None:
                            print("GG Member", gmemberEmail, "in group",
                                  grpName, "not in AktivenDB")
                            missingAktdb[gmemberEmail] = True

                    print("Action: delete", gmemberEmail, "from", grpName)
                    self.message.append(
                        "Entferne " + gmemberEmail + " von " + grpName)
                    if self.doIt:
                        self.google.delMemberFromGroup(grp, gmemberEmail)
                    grp["members"] = [
                        m for m in gmembers if m["email"] != gmemberEmail]

    def listSpcl(self):
        print("\n\nSpecials:")
        print("Benutzer mit orgUnitPath /")
        for k, u in self.ggUsers.items():
            if "orgUnitPath" not in u:
                print("no orgUnitPath for", k)
                continue
            if u["orgUnitPath"] == "/":
                print(k, u["name"]["fullName"])

        # print("\n\nBenutzer mit orgUnitPath /ADFC")
        # for k, u in self.ggUsers.items():
        #     if "orgUnitPath" not in u:
        #         print("no orgUnitPath for", k)
        #         continue
        #     if u["orgUnitPath"] == "/ADFC":
        #         print(k, u["name"]["fullName"])

        print("\n\nBenutzer mit anderem orgUnitPath als / oder /ADFC")
        for k, u in self.ggUsers.items():
            if "orgUnitPath" not in u:
                print("no orgUnitPath for", k)
                continue
            if u["orgUnitPath"] != "/" and u["orgUnitPath"] != "/ADFC":
                print(k, u["name"]["fullName"],
                      "orgUnitPath:", u["orgUnitPath"])

        tmembersAll = {}
        tmembersGrp = {}
        for kind in ["email_adfc", "email_private"]:
            for k, u in self.dbMembers[kind].items():
                for v in u:
                    aktiv = v["active"] == "1" or v["active"] == 1
                    tmembersAll[k.lower()] = (
                        v["name"], "aktiv" if aktiv else "inaktiv")
        for t in self.dbTeams.values():
            for m in t["detail"]["members"]:
                tmembersGrp[m["email_adfc"].lower()] = True

        print("\n\nBenutzer die nicht in der AktivenDB stehen:")
        for g in self.ggUsers.keys():
            tm = tmembersAll.get(g)
            if tm is None:
                print(g)

        print("\n\nBenutzer die in keiner Gruppe der AktivenDB sind (aber vielleicht in anderen google groups!):")
        for g in self.ggUsers.keys():
            tm = tmembersAll.get(g)
            if tm is not None:
                if g not in tmembersGrp:
                    print(g, *tm)

        print("\n\nInaktive Mitglieder der AktivenDB")
        for k, v in tmembersAll.items():
            if v[1] == "inaktiv":
                print(k, v[0])

    def setOU(self):
        for k, u in self.ggUsers.items():
            if "orgUnitPath" not in u:
                print("no orgUnitPath for", k)
                continue
            if u["orgUnitPath"] != "/":
                # print("OK", k, u["name"]["fullName"], u["orgUnitPath"])
                continue
            x = k.find('@')
            y = k.find('.', 0, x)
            if y == -1:
                # print("skip ", k)
                continue
            print("setOU", k, u["name"]["fullName"], u["orgUnitPath"])
            if self.doIt:
                self.google.setOU2ADFC(k)

    def istAktiv(self, email, default):
        member = self.dbMembers["email_adfc"].get(email)
        if member is None:
            member = self.dbMembers["email_private"].get(email)
        if member is None:
            return default
        # if len(member) != 1:
        #     print("xxxxxx", member)  # e.g. michael uhlenberg has 2 entries
        member = member[0]
        return member["active"] != "0" and member["active"] != 0

    def suspendInactiveUsers(self):
        for user in self.ggUsers.values():
            if user["suspended"] or self.istAktiv(user["primaryEmail"], True):
                continue
            print("Aktion: suspend", user["primaryEmail"])
            self.message.append("Suspendiere " + user["primaryEmail"])
            if self.doIt:
                self.google.suspend(user)

    def updAlleAktiven(self):
        alleAktivenGrp = self.ggGroups.get("Alle Aktiven")
        alleAktiven = {m["email"]: m for m in alleAktivenGrp["members"]}
        keineEmails = {m["email"]: m for m in self.ggGroups.get(
            "Keine Emails")["members"] if m["role"] == "MEMBER"}
        alleEmails = {}
        for ggrp in self.ggGroups.values():
            grpName = ggrp["name"]
            if grpName in self.spclGroups:
                continue
            # "normale" OG-Mitglieder sollen nicht in alle_aktiven stehen, nur die SprecherInnen
            if grpName.startswith("OG ") and not grpName.endswith("SprecherInnen"):
                continue
            for member in ggrp["members"]:
                email = member["email"]
                alleEmails[email] = member
                if self.istAktiv(email, False) and alleAktiven.get(email) is None and keineEmails.get(email) is None:
                    print("Aktion: add", email, "to Alle Aktiven")
                    self.message.append(
                        "Mitglied " + email + " hinzugefügt zu Alle Aktiven")
                    if self.doIt:
                        self.google.addMemberToGroup(
                            alleAktivenGrp, email, "MEMBER")
                    alleAktiven[email] = member
        for email in list(alleAktiven.keys()).copy():
            if not self.istAktiv(email, False) or alleEmails.get(email) is None:
                if "info@adfc-muenchen.de" == email:
                    continue
                print("Aktion: delete", email, "from Alle Aktiven")
                self.message.append("Mitglied " + email +
                                    " von Alle Aktiven entfernt")
                if self.doIt:
                    self.google.delMemberFromGroup(alleAktivenGrp, email)
                del alleAktiven[email]
        for email in keineEmails.keys():
            if alleEmails.get(email) is not None:
                print("Aktion: delete", email, "from Alle Aktiven")
                self.message.append("Mitglied " + email +
                                    " von Alle Aktiven entfernt")
                if self.doIt:
                    self.google.delMemberFromGroup(alleAktivenGrp, email)
                del alleAktiven[email]

    def syncAktdbToGgroups(self):
        self.setOU()
        self.listSpcl()
        # self.createMissingGroups()
        self.printUnmatchedDBGroups()
        self.addGGUsersToDB()
        self.addTeamEmailAddressesToAktb()
        self.addToGG()
        self.suspendInactiveUsers()
        self.removeFromGG()
        self.updAlleAktiven()
        # self.cleanNoResp()
        return "\n".join(self.message)
