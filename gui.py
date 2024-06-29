import contextlib
from tkinter import *
from tkinter import ttk
import customtkinter

from aktdbsync import AktDBSync
from ggsync import GGSync
from utils import log

onMsg = "Jetzt aber wirklich!"
offMsg = "Erstmal testen"
phases = ("Namen überprüfen", "Nicht einverstandene löschen",
          "Änderungen übernehmen")


class TxtWriter:
    def __init__(self, targ, tk):
        self.txt = targ
        self.tk = tk

    def write(self, s):
        self.txt.insert("end", s)
        self.tk.update_idletasks()


class Gui:
    def __init__(self):
        root = Tk()
        self.root = root
        # root = customtkinter.CTk()
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        c = ttk.Frame(root, padding=(3, 6),
                      borderwidth=3, relief="solid")
        c.grid(column=0, row=0, sticky=(N, W, E, S))
        c.rowconfigure(0, weight=1)
        c.rowconfigure(1, weight=1)
        c.columnconfigure(0, weight=1)

        # Frame c1
        c1 = ttk.Frame(c, padding=(3, 6), width=400, height=200,
                       borderwidth=3, relief="solid")
        c1.grid(column=0, row=0, sticky=(N, W, E, S), pady=5)
        c1.columnconfigure(0, weight=1)
        c1.columnconfigure(1, weight=1)
        c1.columnconfigure(2, weight=1)

        # Zeile 0
        lbl1h = Label(
            c1, text="Sync von Serienbrief-Antworten -> AktivenDB")
        # Zeile 1
        lbl11 = Label(c1, text="Ausführung:")
        sw1_var = StringVar(value=offMsg)
        sw1 = customtkinter.CTkSwitch(
            c1, text="", variable=sw1_var, onvalue=onMsg, offvalue=offMsg)
        lbl12 = Label(c1, textvariable=sw1_var)
        # Zeile 2
        lbl13 = Label(c1, text="Phase:")
        cb1_var = StringVar(value="Namen überprüfen")
        cb1 = ttk.Combobox(c1, textvariable=cb1_var)
        cb1["values"] = ("Namen überprüfen",
                         "Nicht einverstandene löschen", "Änderungen übernehmen")
        # Zeile 3
        btn1 = Button(c1, text="Start", command=lambda: self.run(
            "s2a", cb1_var, sw1_var, btn1), bg="red")

        # Zeile 0
        lbl1h.grid(column=0, row=0, columnspan=3, sticky=(N, W, E, S))
        # Zeile 1
        lbl11.grid(column=0, row=1, sticky=(W))
        sw1.grid(column=1, row=1, sticky=(N, W, E, S))
        lbl12.grid(column=2, row=1, sticky=(E))
        # Zeile 2
        lbl13.grid(column=0, row=2, sticky=(W))
        cb1.grid(column=1, row=2, columnspan=2, sticky=(N, W, E, S))
        # Zeile 3
        btn1.grid(column=0, row=3, columnspan=3, pady=10)

        # Frame c2
        c2 = ttk.Frame(c, padding=(3, 6), width=400, height=200,
                       borderwidth=3, relief="solid")
        c2.grid(column=0, row=1, sticky=(N, W, E, S), pady=5)
        c2.columnconfigure(0, weight=1)
        c2.columnconfigure(1, weight=1)
        c2.columnconfigure(2, weight=1)

        # Zeile 0
        lbl2h = Label(c2, text="Sync von Erstanlage-Antworten -> AktivenDB")
        # Zeile 1
        lbl21 = Label(c2, text="Ausführung:")
        sw2_var = StringVar(value=offMsg)
        sw2 = customtkinter.CTkSwitch(
            c2, text="", variable=sw2_var, onvalue=onMsg, offvalue=offMsg)
        lbl22 = Label(c2, textvariable=sw2_var)
        # Zeile 2
        lbl23 = Label(c2, text="Phase:")
        cb2_var = StringVar(value="Namen überprüfen")
        cb2 = ttk.Combobox(c2, textvariable=cb2_var)
        cb2["values"] = ("Namen überprüfen", "Erstanmeldungen übernehmen")
        # Zeile 3
        btn2 = Button(c2, text="Start", command=lambda: self.run(
            "e2a", cb2_var, sw2_var, btn2), bg="red")

        # Zeile 0
        lbl2h.grid(column=0, row=0, columnspan=3, sticky=(N, W, E, S))
        # Zeile 1
        lbl21.grid(column=0, row=1, sticky=(W))
        sw2.grid(column=1, row=1, sticky=(N, W, E, S))
        lbl22.grid(column=2, row=1, sticky=(E))
        # Zeile 2
        lbl23.grid(column=0, row=2, sticky=(W))
        cb2.grid(column=1, row=2, columnspan=2, sticky=(N, W, E, S))
        # Zeile 3
        btn2.grid(column=0, row=3, columnspan=3, pady=10)

        # Frame c3
        c3 = ttk.Frame(c, padding=(3, 6), width=400, height=200,
                       borderwidth=3, relief="solid")
        c3.grid(column=0, row=2, sticky=(N, W, E, S), pady=5)
        c3.columnconfigure(0, weight=1)
        c3.columnconfigure(1, weight=1)
        c3.columnconfigure(2, weight=1)

        # Zeile 0
        lbl3h = Label(
            c3, text="Sync von AktivenDB -> Google Groups (mit Admin-Berechtigung!)")
        # Zeile 1
        lbl31 = Label(c3, text="Ausführung:")
        sw3_var = StringVar(value=offMsg)
        sw3 = customtkinter.CTkSwitch(
            c3, text="", variable=sw3_var, onvalue=onMsg, offvalue=offMsg)
        lbl32 = Label(c3, textvariable=sw3_var)
        # Zeile 2
        btn3 = Button(c3, text="Start", command=lambda: self.run(
            "a2g", None, sw3_var, btn3), bg="red")

        # Zeile 0
        lbl3h.grid(column=0, row=0, columnspan=3, sticky=(N, W, E, S))
        # Zeile 1
        lbl31.grid(column=0, row=1, sticky=(W))
        sw3.grid(column=1, row=1, sticky=(N, W, E, S))
        lbl32.grid(column=2, row=1, sticky=(E))
        # Zeile 2
        btn3.grid(column=0, row=2, columnspan=3, pady=10)

        textContainer = Frame(root, borderwidth=2, relief="sunken")
        text = Text(textContainer, wrap="none", borderwidth=0,
                    cursor="arrow")  # width=100, height=40,
        self.text = text
        textVsb = Scrollbar(textContainer, orient="vertical",
                            command=text.yview)
        textHsb = Scrollbar(textContainer, orient="horizontal",
                            command=text.xview)
        text.configure(yscrollcommand=textVsb.set,
                       xscrollcommand=textHsb.set)
        textContainer.grid(row=4, columnspan=2, padx=5, pady=2, sticky="nsew")
        text.grid(row=0, column=0, sticky="nsew")
        textVsb.grid(row=0, column=1, sticky="ns")
        textHsb.grid(row=1, column=0, sticky="ew")
        textContainer.rowconfigure(0, weight=1)
        textContainer.columnconfigure(0, weight=1)

    def startGui(self):
        self.text.delete("1.0", END)
        txtWriter = TxtWriter(self.text, self.root)
        with contextlib.redirect_stdout(txtWriter):
            self.root.mainloop()

    def run(self, logName, phase, doIt, btn):
        try:
            self.text.delete("1.0", END)
            btn.config(state=DISABLED)
            if phase is not None:
                phase = phase.get()
                if phase == "Namen überprüfen":
                    phase = 1
                elif phase == "Nicht einverstandene löschen":
                    phase = 2
                else:
                    phase = 3
            doIt = doIt.get()
            doIt = doIt == onMsg
            if logName == "a2g":
                ggsync = GGSync(doIt)
                msgs = ggsync.syncAktdbToGgroups()
                log("a2g", msgs)
                return
            if logName == "s2a":
                aksync = AktDBSync(doIt, phase, "Antworten 2023")
            elif logName == "e2a":
                aksync = AktDBSync(doIt, phase, "Erstanlage")
            else:
                print("invalid logName")
                return
            aksync.getSheetData()
            aksync.checkColumns()
            aksync.getAktdbData()
            entries = aksync.getFormEntries()
            msgs = aksync.storeMembers(entries)
            log(logName, msgs)
        except Exception as e:
            print("Exception", e)
        finally:
            btn.config(state=NORMAL)
            print("Fertig!")
