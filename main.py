import argparse
import getpass
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
    parser.add_argument("-p", "--phase",
                        dest="phase", default=1)
    args = parser.parse_args()
    print("parser.doIt", args.doIt)

    ggsync = GGSync(args.doIt)
    ggsync.main()

    # aksync = AktDBSync(args.doIt, args.phase)
    # entries = aksync.getEntries()
    # aksync.storeMembers(entries)


if __name__ == '__main__':
    main()
