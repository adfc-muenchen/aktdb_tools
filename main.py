import argparse
import datetime
import pprint
import os
import sys
from gg import Google
from ggsync import GGSync
from aktdbsync import AktDBSync
from utils import date2String


#  it seems that with "pyinstaller -F" tkinter (resp. TK) does not find data files relative to the MEIPASS dir
def pyinst(path):
    path = path.strip()
    if os.path.exists(path):
        return path
    if hasattr(sys, "_MEIPASS"):  # i.e. if running as exe produced by pyinstaller
        pypath = sys._MEIPASS + "/" + path
        if os.path.exists(pypath):
            return pypath
    return path


def log(name, msgs):
    if len(msgs) == 0:
        return
    name = "logs/" + name + "_" + \
        date2String(datetime.datetime.now(), dateOnly=False)[
            0:19].replace(":", "") + ".log"
    os.makedirs("logs", exist_ok=True)
    with open(name, "w") as fp:
        fp.write(msgs)
    print(msgs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--execute", action="store_true",
                        dest="doIt", default=False)
    parser.add_argument("-s", "--syncSerienbriefToAktDB", action="store_true",
                        dest="syncSerienbriefToAktDB", default=False)
    parser.add_argument("-e", "--syncErstanlageToAktDB", action="store_true",
                        dest="syncErstanlageToAktDB", default=False)
    parser.add_argument("-a", "--syncAktdbToGgroups", action="store_true",
                        dest="syncAktdbToGgroups", default=False)
    parser.add_argument("-p", "--phase", type=int,
                        dest="phase", default=1)
    args = parser.parse_args()
    print("parser.doIt", args.doIt)

    if args.syncAktdbToGgroups:
        ggsync = GGSync(args.doIt)
        msgs = ggsync.syncAktdbToGgroups()
        log("a2g", msgs)
        return

    logName = ""
    aksync = None
    if args.syncSerienbriefToAktDB:
        aksync = AktDBSync(args.doIt, args.phase, "Antworten")
        logName = "s2a"
    if args.syncErstanlageToAktDB:
        aksync = AktDBSync(args.doIt, args.phase, "Erstanlage")
        logName = "e2a"
    if aksync is None:
        print("use params -s, -e or -a")
        return
    aksync.getSheetData()
    aksync.checkColumns()
    aksync.getAktdbData()
    entries = aksync.getFormEntries()
    msgs = aksync.storeMembers(entries)
    log(logName, msgs)


if __name__ == '__main__':
    main()
