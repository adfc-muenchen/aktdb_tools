import datetime
import os
import sys


def date2String(t, dateOnly=True):
    s = None
    if t:
        if isinstance(t, str):
            s = t
        else:
            s = t.isoformat(sep=" ", timespec="seconds")  # yyyy-mm-dd hh:mm:ss
            if dateOnly:
                s = s[0:10]
    return s


def string2Date(s):
    d = None
    if s:
        if not isinstance(s, str) or s[4] == "-" and s[7] == "-":
            d = s
        else:
            try:
                d = datetime.datetime.strptime(s, "%d.%m.%Y %H:%M:%S")
            except:
                d = datetime.datetime.strptime(s, "%d.%m.%Y")
    return d


"time data '20.07.2024' does not match format '%d.%m.%Y %H:%M:%S'"


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
    with open(name, "w", encoding="utf-8") as fp:
        fp.write(msgs)
