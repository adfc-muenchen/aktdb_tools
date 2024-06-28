import datetime
import os
import sys


def date2String(t, dateOnly=True):
    s = None
    if t:
        if isinstance(t, str):
            s = t
        else:
            s = t.isoformat()
            if dateOnly:
                s = s[0:10]
    return s


def string2Date(s):
    d = None
    if s:
        if not isinstance(s, str):
            d = s
        else:
            d = datetime.datetime.strptime(s, "%d.%m.%Y %H:%M:%S")
    return d


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
