import argparse
import pprint
import os
import sys
from gg import Google
from ggsync import GGSync
from aktdbsync import AktDBSync


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--execute", action="store_true",
                        dest="doIt", default=False)
    parser.add_argument("-s", "--syncSerienbriefToAktDB", action="store_true",
                        dest="syncSerienbriefToAktDB", default=False)
    parser.add_argument("-e", "--syncErstanlageToAktDB", action="store_true",
                        dest="syncErstanlageToAktDB", default=False)
    parser.add_argument("-g", "--syncAktdbToGgroups", action="store_true",
                        dest="syncAktdbToGgroups", default=False)
    parser.add_argument("-p", "--phase", type=int,
                        dest="phase", default=1)
    args = parser.parse_args()
    print("parser.doIt", args.doIt)

    if args.syncAktdbToGgroups:
        ggsync = GGSync(args.doIt)
        ggsync.syncAktdbToGgroups()
        return

    aksync = None
    if args.syncSerienbriefToAktDB:
        aksync = AktDBSync(args.doIt, args.phase, "Antworten")
    if args.syncErstanlageToAktDB:
        aksync = AktDBSync(args.doIt, args.phase, "Erstanlage")
    if aksync is None:
        print("use params -s, -e or -d")
        return
    aksync.getSheetData()
    aksync.checkColumns()
    aksync.getAktdbData()
    entries = aksync.getFormEntries()
    aksync.storeMembers(entries)
    # pprint.pprint(entries)


if __name__ == '__main__':
    main()
