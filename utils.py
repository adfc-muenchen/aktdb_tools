def date2String(t, short=True):
    s = None
    if t:
        if isinstance(t, str):
            s = t
        else:
            s = t.isoformat()
            if short:
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
