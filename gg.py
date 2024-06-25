import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/admin.directory.group',
          'https://www.googleapis.com/auth/admin.directory.user',
          'https://www.googleapis.com/auth/admin.directory.customer',
          'https://www.googleapis.com/auth/admin.directory.rolemanagement',
          'https://www.googleapis.com/auth/admin.directory.userschema',
          'https://www.googleapis.com/auth/apps.groups.settings',
          'https://www.googleapis.com/auth/spreadsheets']


class Google:
    def __init__(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    'secret/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        self.adminService = googleapiclient.discovery.build(
            'admin', 'directory_v1', credentials=creds)
        # self.gsService = googleapiclient.discovery.build(
        #     'groupssettings', 'v1', credentials=creds)

    def getGGUsers(self):
        userList = []
        for domain in ["adfc-muenchen.de", "radentscheid-muenchen.de"]:
            page = None
            while True:
                requ = self.adminService.users().list(pageToken=page, domain=domain)
                respu = requ.execute()
                userList.extend(respu.get("users"))
                page = respu.get("nextPageToken")
                if page is None or page == "":
                    break
        users = {u["primaryEmail"]: u for u in userList}
        return users

    def getGGGroups(self):
        domainNames = ["adfc-muenchen.de",
                       "groups.adfc-muenchen.de", "lists.adfc-muenchen.de"]
        page = None
        groupList = []
        for dn in domainNames:
            while True:
                reqg = self.adminService.groups().list(pageToken=page, domain=dn)
                respg = reqg.execute()
                groupList.extend(respg.get("groups"))
                page = respg.get("nextPageToken")
                if page is None or page == "":
                    break
        groups = {g["name"]: g for g in groupList}
        return groups

    # def getGGAccessSettings(self, group):
    #     reqas = self.gsService.groups().get(groupUniqueId=group["email"])
    #     respas = reqas.execute()
    #     group["accessSettings"] = respas

    # def getGGMember(self, grpId, email):
    #     reqm = self.adminService.members().get(groupKey=grpId, memberKey=email)  # , projection="full"
    #     respm = reqm.execute()
    #     return respm

    def chgGGMemberRole(self, group, email, role):
        body = {"role": role}
        requ = self.adminService.members().update(
            groupKey=group["id"], memberKey=email, body=body)
        respu = requ.execute()
        return respu

    def getGGGroup(self, grpId):
        reqg = self.adminService.groups().get(groupKey=grpId)
        respg = reqg.execute()
        return respg

    def getGGGroupMemberNames(self, grpId):
        page = None
        memberList = []
        while True:
            reqg = self.adminService.members().list(
                groupKey=grpId, pageToken=page)  # , projection="full"
            respg = reqg.execute()
            ms = respg.get("members")
            if ms is not None:
                memberList.extend(ms)
            page = respg.get("nextPageToken")
            if page is None or page == "":
                break
        members = [{"email": m["email"].lower(), "role": m["role"]}
                   for m in memberList if m["type"] == "USER"]
        return members

    def addMemberToGroup(self, group, email, role):
        body = {
            "kind": "admin#directory#member",
            "delivery_settings": "ALL_MAIL",
            "email": email,
            "role": role,  # MEMBER or MANAGER
            "type": "USER",
            "status": "ACTIVE",
        }
        try:
            reqm = self.adminService.members().insert(
                groupKey=group["id"], body=body)
            respm = reqm.execute()
            return respm
        except Exception as e:
            print("Error: cannot add member", email,
                  "to group", group["name"], ":", e)
            return None

    def delMemberFromGroup(self, group, email):
        # body = {"password": "wahrscheinlich_Inaktives_Mitglied"}
        # try:
        #     requ = self.adminService.users().update(userKey=email, body=body)
        #     requ.execute()
        # except Exception as e:
        #     print("Error: cannot change password of", email, ":", e)
        try:
            reqd = self.adminService.members().delete(
                groupKey=group["id"], memberKey=email)
            reqd.execute()
        except Exception as e:
            print("Error: cannot delete member", email,
                  "from group", group["name"], ":", e)

    def addEmailToUser(self, user, privEmail):
        body = {
            "emails": [
                {
                    "address": privEmail,
                    "type": "other"
                }
            ]
        }
        try:
            requ = self.adminService.users().update(
                userKey=user["id"], body=body)
            respu = requ.execute()
            return respu
        except Exception as e:
            print("Error: cannot add email", privEmail,
                  "to user", user["primaryEmail"], ":", e)
            return None

    def suspend(self, user):
        body = {
            "suspended": True,
            "suspensionReason": "inactive"
        }
        try:
            requ = self.adminService.users().update(
                userKey=user["id"], body=body)
            respu = requ.execute()
            return respu
        except Exception as e:
            print("Error: cannot suspend user", user["primaryEmail"], ":", e)
            return None

    def setOU2ADFC(self, email):
        body = {"orgUnitPath": "/ADFC"}
        try:
            requ = self.adminService.users().update(userKey=email, body=body)
            requ.execute()
        except Exception as e:
            print("Error: cannot set OU of", email, ":", e)

    def createGroup(self, grp):
        try:
            req = self.adminService.groups().insert(body=grp)
            res = req.execute()
            return res
        except Exception as e:
            print("Error: cannot create Group", grp.name)
            return None
