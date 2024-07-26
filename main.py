import argparse
import sys
from gg import Google
from ggsync import GGSync
from aktdbsync import AktDBSync
from gui import Gui
from sendSB import SendeSB
from utils import log


def main():
    if len(sys.argv) == 1:
        gui = Gui()
        gui.startGui()
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--execute", action="store_true",
                        dest="doIt", default=False)
    parser.add_argument("-s", "--syncSerienbriefToAktDB", action="store_true",
                        dest="syncSerienbriefToAktDB", default=False)
    parser.add_argument("-e", "--syncErstanlageToAktDB", action="store_true",
                        dest="syncErstanlageToAktDB", default=False)
    parser.add_argument("-a", "--syncAktdbToGgroups", action="store_true",
                        dest="syncAktdbToGgroups", default=False)
    parser.add_argument("-b", "--sendeSerienbrief", action="store_true",
                        dest="sendeSerienbrief", default=False)
    parser.add_argument("-p", "--phase", type=int,
                        dest="phase", default=1)
    args = parser.parse_args()
    print("parser.doIt", args.doIt)

    if args.syncAktdbToGgroups:
        ggsync = GGSync(args.doIt)
        msgs = ggsync.syncAktdbToGgroups()
        if args.doIt:
            log("a2g", msgs)
        return
    if args.sendeSerienbrief:
        sendsb = SendeSB(args.doIt)
        msgs = sendsb.sendeSB()
        if args.doIt:
            log("ssb", msgs)
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
    if args.doIt:
        log(logName, msgs)


if __name__ == '__main__':
    main()
