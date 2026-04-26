import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import shutil
from datetime import datetime
from abc import ABC, abstractmethod


# ─────────────────────────────────────────────
#  OOP KLASĖS
# ─────────────────────────────────────────────

class BazinisIrasas(ABC):
    """Bazinė abstrakti klasė visiems įrašams"""

    def __init__(self, data: str, vieta: str, pastabos: str = ""):
        self._data = data
        self._vieta = vieta
        self._pastabos = pastabos

    @property
    def data(self):
        return self._data

    @property
    def vieta(self):
        return self._vieta

    @property
    def pastabos(self):
        return self._pastabos

    @pastabos.setter
    def pastabos(self, value: str):
        self._pastabos = value

    @abstractmethod
    def santrauka(self) -> str:
        pass

    def __str__(self):
        return self.santrauka()


class OrasIrasas:
    """Oras - atskira klasė (kompozicija)"""

    def __init__(self, temperatura: float = 0.0, oras_aprasas: str = ""):
        self.temperatura = temperatura
        self.oras_aprasas = oras_aprasas

    def __str__(self):
        return f"{self.oras_aprasas}, {self.temperatura}°C"


class ZvejybosIrasas(BazinisIrasas):
    """Pagrindinis žvejybos įrašas - paveldi iš BazinisIrasas"""

    def __init__(self, data: str, vieta: str, zuvis_rusys: str,
                 svoris: float, ilgis: float, masalas: str,
                 oras: OrasIrasas, nuotrauka_path: str = "",
                 pastabos: str = "", irasas_id: int = None):
        super().__init__(data, vieta, pastabos)
        self._zuvis_rusys = zuvis_rusys
        self._svoris = svoris
        self._ilgis = ilgis
        self._masalas = masalas
        self._oras = oras
        self._nuotrauka_path = nuotrauka_path
        self.irasas_id = irasas_id

    @property
    def zuvis_rusys(self):
        return self._zuvis_rusys

    @property
    def svoris(self):
        return self._svoris

    @svoris.setter
    def svoris(self, value: float):
        if value < 0:
            raise ValueError("Svoris negali būti neigiamas")
        self._svoris = value

    @property
    def ilgis(self):
        return self._ilgis

    @property
    def masalas(self):
        return self._masalas

    @property
    def oras(self):
        return self._oras

    @property
    def nuotrauka_path(self):
        return self._nuotrauka_path

    def santrauka(self) -> str:
        return (f"{self._data} | {self._vieta} | "
                f"{self._zuvis_rusys} {self._svoris}kg")


class TrofejinisIrasas(ZvejybosIrasas):
    """Trofėjinis įrašas - paveldi iš ZvejybosIrasas (Polymorphism)"""

    STATUSAI = [
        "Asmeninis rekordas",
        "Didžiausia šiais metais",
        "Varžybų laimėjimas",
        "Ypatingas laimikis"]

    def __init__(self, data: str, vieta: str, zuvis_rusys: str,
                 svoris: float, ilgis: float, masalas: str,
                 oras: OrasIrasas, trofejaus_statusas: str = "",
                 isleista_atgal: bool = False, vieta_varzbose: str = "",
                 nuotrauka_path: str = "", pastabos: str = "",
                 irasas_id: int = None):
        super().__init__(data, vieta, zuvis_rusys, svoris, ilgis,
                         masalas, oras, nuotrauka_path, pastabos, irasas_id)
        self._trofejaus_statusas = trofejaus_statusas
        self._isleista_atgal = isleista_atgal
        self._vieta_varzbose = vieta_varzbose

    @property
    def trofejaus_statusas(self):
        return self._trofejaus_statusas

    @property
    def isleista_atgal(self):
        return self._isleista_atgal

    @property
    def vieta_varzbose(self):
        return self._vieta_varzbose

    def santrauka(self) -> str:
        # Perrašytas metodas - Polymorphism
        atgal = " (išleista atgal)" if self._isleista_atgal else ""
        return (f"🏆 {self._data} | {self._vieta} | "
                f"{self._zuvis_rusys} {self._svoris}kg | "
                f"{self._trofejaus_statusas}{atgal}")


class Dienorastis:
    """Dienoraščio valdiklis - agregacija (saugo ZvejybosIrasas sąrašą)"""

    def __init__(self, db: 'DuomenuBaze'):
        self._db = db
        self._irasai: list[ZvejybosIrasas] = []

    def prideti_irasa(self, irasas: ZvejybosIrasas) -> int:
        irasas_id = self._db.issaugoti(irasas)
        irasas.irasas_id = irasas_id
        self._irasai.append(irasas)
        return irasas_id

    def gauti_visus(self) -> list[ZvejybosIrasas]:
        self._irasai = self._db.gauti_visus()
        return self._irasai

    def istrinti(self, irasas_id: int):
        self._db.istrinti(irasas_id)
        self._irasai = [i for i in self._irasai if i.irasas_id != irasas_id]

    def statistika(self) -> dict:
        irasai = self.gauti_visus()
        if not irasai:
            return {}
        svoriai = [i.svoris for i in irasai if i.svoris > 0]
        return {
            "viso_irasu": len(irasai),
            "max_svoris": max(svoriai) if svoriai else 0,
            "vid_svoris": (
                round(sum(svoriai) / len(svoriai), 2) if svoriai else 0),
            "rusys": list(set(i.zuvis_rusys for i in irasai))
        }


class DuomenuBaze:
    """Singleton - vienas DB ryšys"""

    _instance = None

    def __new__(cls, db_path: str = "zvejo_dienorastis.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = db_path
            cls._instance._sukurti_lenteles()
        return cls._instance

    def _sukurti_lenteles(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS irasai (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    vieta TEXT NOT NULL,
                    zuvis_rusys TEXT NOT NULL,
                    svoris REAL DEFAULT 0,
                    ilgis REAL DEFAULT 0,
                    masalas TEXT DEFAULT '',
                    temperatura REAL DEFAULT 0,
                    oras_aprasas TEXT DEFAULT '',
                    nuotrauka_path TEXT DEFAULT '',
                    pastabos TEXT DEFAULT '',
                    trofejinis INTEGER DEFAULT 0,
                    trofejaus_statusas TEXT DEFAULT '',
                    isleista_atgal INTEGER DEFAULT 0,
                    vieta_varzbose TEXT DEFAULT '',
                    sukurta TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            for col in ["trofejinis INTEGER DEFAULT 0",
                        "trofejaus_statusas TEXT DEFAULT ''",
                        "isleista_atgal INTEGER DEFAULT 0",
                        "vieta_varzbose TEXT DEFAULT ''"]:
                try:
                    conn.execute(f"ALTER TABLE irasai ADD COLUMN {col}")
                except Exception:
                    pass

    def issaugoti(self, irasas: ZvejybosIrasas) -> int:
        trofejinis = isinstance(irasas, TrofejinisIrasas)
        trofejaus_statusas = irasas.trofejaus_statusas if trofejinis else ""
        isleista_atgal = int(irasas.isleista_atgal) if trofejinis else 0
        vieta_varzbose = irasas.vieta_varzbose if trofejinis else ""
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO irasai
                (data, vieta, zuvis_rusys, svoris, ilgis, masalas,
                 temperatura, oras_aprasas, nuotrauka_path, pastabos,
                 trofejinis, trofejaus_statusas,
                 isleista_atgal, vieta_varzbose)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (irasas.data,
                 irasas.vieta,
                 irasas.zuvis_rusys,
                 irasas.svoris,
                 irasas.ilgis,
                 irasas.masalas,
                 irasas.oras.temperatura,
                 irasas.oras.oras_aprasas,
                 irasas.nuotrauka_path,
                 irasas.pastabos,
                 int(trofejinis),
                    trofejaus_statusas,
                    isleista_atgal,
                    vieta_varzbose))
            return cur.lastrowid

    def gauti_visus(self) -> list[ZvejybosIrasas]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM irasai ORDER BY data DESC"
            ).fetchall()
        result = []
        for r in rows:
            oras = OrasIrasas(r["temperatura"], r["oras_aprasas"])
            if r["trofejinis"]:
                irasas = TrofejinisIrasas(
                    data=r["data"], vieta=r["vieta"],
                    zuvis_rusys=r["zuvis_rusys"], svoris=r["svoris"],
                    ilgis=r["ilgis"], masalas=r["masalas"],
                    oras=oras,
                    trofejaus_statusas=r["trofejaus_statusas"],
                    isleista_atgal=bool(r["isleista_atgal"]),
                    vieta_varzbose=r["vieta_varzbose"],
                    nuotrauka_path=r["nuotrauka_path"],
                    pastabos=r["pastabos"], irasas_id=r["id"]
                )
            else:
                irasas = ZvejybosIrasas(
                    data=r["data"], vieta=r["vieta"],
                    zuvis_rusys=r["zuvis_rusys"], svoris=r["svoris"],
                    ilgis=r["ilgis"], masalas=r["masalas"],
                    oras=oras, nuotrauka_path=r["nuotrauka_path"],
                    pastabos=r["pastabos"], irasas_id=r["id"]
                )
            result.append(irasas)
        return result

    def istrinti(self, irasas_id: int):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM irasai WHERE id=?", (irasas_id,))


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

COLORS = {
    "bg": "#0d1b2a",
    "panel": "#1a2e42",
    "card": "#1f3550",
    "accent": "#2a9d8f",
    "accent2": "#e9c46a",
    "text": "#eaf4f4",
    "text_dim": "#7fb3c8",
    "danger": "#e76f51",
    "border": "#2a4560",
    "entry_bg": "#142233",
}

ZUVIS_RUSYS = [
    "Karšis", "Lydeka", "Ešerys", "Kuoja", "Ungurys",
    "Sykas", "Šamas", "Starkis", "Plakis", "Kita"
]

ORAS_TIPAI = [
    "Saulėta", "Debesuota", "Lietinga", "Vėjuota",
    "Rūkana", "Snieguota", "Kita"
]


class ZvejoDienorastisApp(tk.Tk):
    """Pagrindinis aplikacijos langas"""

    def __init__(self):
        super().__init__()
        self.title("🎣 Žvejo Dienoraštis")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])

        # OOP objektai
        self.db = DuomenuBaze()
        self.dienorastis = Dienorastis(self.db)
        self.pasirinktas_irasas = None
        self.nuotrauka_path = tk.StringVar()

        self._sukurti_stilius()
        self._sukurti_layout()
        self._atnaujinti_sarasa()

    def _sukurti_stilius(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("Panel.TFrame", background=COLORS["panel"])

        style.configure("TLabel",
                        background=COLORS["bg"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 10))

        style.configure("Title.TLabel",
                        background=COLORS["bg"],
                        foreground=COLORS["accent2"],
                        font=("Segoe UI", 18, "bold"))

        style.configure("Header.TLabel",
                        background=COLORS["panel"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 10, "bold"))

        style.configure("Card.TLabel",
                        background=COLORS["card"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 10))

        style.configure("Dim.TLabel",
                        background=COLORS["bg"],
                        foreground=COLORS["text_dim"],
                        font=("Segoe UI", 9))

        style.configure("Accent.TButton",
                        background=COLORS["accent"],
                        foreground="white",
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        focusthickness=0,
                        padding=(14, 8))
        style.map("Accent.TButton",
                  background=[("active", "#21867a"), ("pressed", "#1a6b61")])

        style.configure("Danger.TButton",
                        background=COLORS["danger"],
                        foreground="white",
                        font=("Segoe UI", 10),
                        borderwidth=0,
                        padding=(10, 6))
        style.map("Danger.TButton",
                  background=[("active", "#c55a3e")])

        style.configure("Treeview",
                        background=COLORS["card"],
                        foreground=COLORS["text"],
                        fieldbackground=COLORS["card"],
                        rowheight=32,
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=COLORS["panel"],
                        foreground=COLORS["text_dim"],
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map("Treeview",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", "white")])

        style.configure("TCombobox",
                        fieldbackground=COLORS["entry_bg"],
                        background=COLORS["entry_bg"],
                        foreground=COLORS["text"],
                        selectbackground=COLORS["accent"],
                        font=("Segoe UI", 10))

        style.configure("TEntry",
                        fieldbackground=COLORS["entry_bg"],
                        foreground=COLORS["text"],
                        insertcolor=COLORS["text"],
                        font=("Segoe UI", 10))

        style.configure("Horizontal.TScrollbar",
                        background=COLORS["panel"],
                        troughcolor=COLORS["bg"],
                        borderwidth=0)
        style.configure("Vertical.TScrollbar",
                        background=COLORS["panel"],
                        troughcolor=COLORS["bg"],
                        borderwidth=0)

    def _sukurti_layout(self):
        # Antraštė
        header = tk.Frame(self, bg=COLORS["bg"], pady=12)
        header.pack(fill="x", padx=20)

        tk.Label(header, text="🎣 Žvejo Dienoraštis",
                 bg=COLORS["bg"], fg=COLORS["accent2"],
                 font=("Segoe UI", 20, "bold")).pack(side="left")

        self.stat_label = tk.Label(header, text="",
                                   bg=COLORS["bg"], fg=COLORS["text_dim"],
                                   font=("Segoe UI", 10))
        self.stat_label.pack(side="right", padx=10)

        # Atskyrimas
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # Pagrindinis turinys
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # Kairė - sąrašas
        left = tk.Frame(main, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True)

        self._sukurti_sarasa_panel(left)

        # Dešinė - forma
        right = tk.Frame(main, bg=COLORS["panel"],
                         bd=0, relief="flat", width=380)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        self._sukurti_forma(right)

    def _sukurti_sarasa_panel(self, parent):
        # Toolbar
        toolbar = tk.Frame(parent, bg=COLORS["bg"])
        toolbar.pack(fill="x", pady=(0, 8))

        tk.Label(toolbar, text="Įrašai",
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        ttk.Button(toolbar, text="🗑 Ištrinti",
                   style="Danger.TButton",
                   command=self._istrinti).pack(side="right")

        ttk.Button(
            toolbar,
            text="✏ Kopijuoti",
            style="Accent.TButton",
            command=self._kopijuoti_irasa).pack(
            side="right",
            padx=(
                0,
                5))

        # Treeview
        cols = ("data", "vieta", "zuvis", "svoris", "masalas", "oras")
        self.tree = ttk.Treeview(parent, columns=cols,
                                 show="headings", selectmode="browse")

        headers = {
            "data": ("Data", 110),
            "vieta": ("Vieta", 130),
            "zuvis": ("Žuvis", 100),
            "svoris": ("Svoris (kg)", 90),
            "masalas": ("Masalas", 110),
            "oras": ("Oras", 110),
        }
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, minwidth=60)

        vsb = ttk.Scrollbar(parent, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._pasirinkti_irasa)

    def _sukurti_forma(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS["panel"],
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.forma_frame = tk.Frame(canvas, bg=COLORS["panel"])
        canvas_window = canvas.create_window(
            (0, 0), window=self.forma_frame, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window,
                              width=canvas.winfo_width())

        self.forma_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        # Bind mousewheel
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        self._sukurti_formos_laukus(self.forma_frame)

    def _entry(self, parent, row, label_text, var=None):
        tk.Label(parent, text=label_text,
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=row * 2, column=0, columnspan=2,
            sticky="w", padx=12, pady=(8, 0))

        if var is None:
            var = tk.StringVar()

        e = tk.Entry(parent, textvariable=var,
                     bg=COLORS["entry_bg"], fg=COLORS["text"],
                     insertbackground=COLORS["text"],
                     relief="flat", font=("Segoe UI", 10),
                     highlightthickness=1,
                     highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["accent"])
        e.grid(row=row * 2 + 1, column=0, columnspan=2,
               sticky="ew", padx=12, pady=(2, 0))
        return var

    def _combo(self, parent, row, label_text, values):
        tk.Label(parent, text=label_text,
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=row * 2, column=0, columnspan=2,
            sticky="w", padx=12, pady=(8, 0))

        var = tk.StringVar()
        cb = ttk.Combobox(parent, textvariable=var,
                          values=values, state="readonly",
                          font=("Segoe UI", 10))
        cb.grid(row=row * 2 + 1, column=0, columnspan=2,
                sticky="ew", padx=12, pady=(2, 0))
        return var

    def _sukurti_formos_laukus(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        tk.Label(parent, text="Naujas įrašas",
                 bg=COLORS["panel"], fg=COLORS["accent2"],
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2,
            sticky="w", padx=12, pady=(14, 4))

        # Laukeliai
        self.v_data = self._entry(parent, 1, "📅  Data ir laikas")
        self.v_data.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        self.v_vieta = self._entry(parent, 2, "📍  Vieta / telkinys")

        self.v_zuvis = self._combo(parent, 3, "🐟  Žuvies rūšis", ZUVIS_RUSYS)

        # Svoris ir ilgis šalia
        tk.Label(parent, text="⚖  Svoris (kg)",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=8, column=0, sticky="w", padx=12, pady=(8, 0))
        tk.Label(parent, text="📏  Ilgis (cm)",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=8, column=1, sticky="w", padx=6, pady=(8, 0))

        self.v_svoris = tk.StringVar()
        self.v_ilgis = tk.StringVar()

        tk.Entry(parent, textvariable=self.v_svoris,
                 bg=COLORS["entry_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"],
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1,
                 highlightbackground=COLORS["border"],
                 highlightcolor=COLORS["accent"]).grid(
            row=9, column=0, sticky="ew", padx=12, pady=(2, 0))

        tk.Entry(parent, textvariable=self.v_ilgis,
                 bg=COLORS["entry_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"],
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1,
                 highlightbackground=COLORS["border"],
                 highlightcolor=COLORS["accent"]).grid(
            row=9, column=1, sticky="ew", padx=(4, 12), pady=(2, 0))

        self.v_masalas = self._entry(parent, 5, "🪝  Masalas / įrankiai")

        self.v_oras = self._combo(parent, 6, "🌤  Oras", ORAS_TIPAI)

        self.v_temp = self._entry(parent, 7, "🌡  Temperatūra (°C)")

        # Nuotrauka
        tk.Label(parent, text="📷  Nuotrauka",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=16, column=0, columnspan=2,
            sticky="w", padx=12, pady=(8, 0))

        nuotr_frame = tk.Frame(parent, bg=COLORS["panel"])
        nuotr_frame.grid(row=17, column=0, columnspan=2,
                         sticky="ew", padx=12, pady=(2, 0))
        nuotr_frame.columnconfigure(0, weight=1)

        self.nuotr_label = tk.Label(
            nuotr_frame,
            textvariable=self.nuotrauka_path,
            bg=COLORS["entry_bg"],
            fg=COLORS["text_dim"],
            font=(
                "Segoe UI",
                9),
            anchor="w",
            width=22)
        self.nuotr_label.grid(row=0, column=0, sticky="ew")

        tk.Button(nuotr_frame, text="Pasirinkti",
                  bg=COLORS["accent"], fg="white",
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2",
                  command=self._pasirinkti_nuotrauka).grid(
            row=0, column=1, padx=(4, 0))

        # Pastabos
        tk.Label(parent, text="📝  Pastabos",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=18, column=0, columnspan=2,
            sticky="w", padx=12, pady=(8, 0))

        self.txt_pastabos = tk.Text(parent, height=3,
                                    bg=COLORS["entry_bg"], fg=COLORS["text"],
                                    insertbackground=COLORS["text"],
                                    relief="flat", font=("Segoe UI", 10),
                                    highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    highlightcolor=COLORS["accent"],
                                    wrap="word")
        self.txt_pastabos.grid(row=19, column=0, columnspan=2,
                               sticky="ew", padx=12, pady=(2, 0))

        # Trofėjinis įrašas
        tk.Frame(parent, bg=COLORS["border"], height=1).grid(
            row=22, column=0, columnspan=2,
            sticky="ew", padx=12, pady=(8, 0))

        self.v_trofejinis = tk.BooleanVar()
        trofej_check = tk.Checkbutton(
            parent, text="🏆  Trofėjinis laimikis",
            variable=self.v_trofejinis,
            bg=COLORS["panel"], fg=COLORS["accent2"],
            selectcolor=COLORS["entry_bg"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["accent2"],
            font=("Segoe UI", 10, "bold"),
            command=self._trofejinis_toggle)
        trofej_check.grid(row=23, column=0, columnspan=2,
                          sticky="w", padx=12, pady=(8, 0))

        self.trofej_frame = tk.Frame(parent, bg=COLORS["panel"])
        self.trofej_frame.grid(row=24, column=0, columnspan=2,
                               sticky="ew")
        self.trofej_frame.columnconfigure(0, weight=1)
        self.trofej_frame.columnconfigure(1, weight=1)
        self.trofej_frame.grid_remove()

        tk.Label(self.trofej_frame, text="🎖  Statusas",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=0, column=0, columnspan=2,
            sticky="w", padx=12, pady=(6, 0))

        self.v_trofejaus_statusas = tk.StringVar()
        ttk.Combobox(self.trofej_frame,
                     textvariable=self.v_trofejaus_statusas,
                     values=TrofejinisIrasas.STATUSAI,
                     state="readonly",
                     font=("Segoe UI", 10)).grid(
            row=1, column=0, columnspan=2,
            sticky="ew", padx=12, pady=(2, 0))

        tk.Label(self.trofej_frame, text="🏅  Vieta varžybose",
                 bg=COLORS["panel"], fg=COLORS["text_dim"],
                 font=("Segoe UI", 9)).grid(
            row=2, column=0, columnspan=2,
            sticky="w", padx=12, pady=(6, 0))

        self.v_vieta_varzbose = tk.StringVar()
        tk.Entry(self.trofej_frame, textvariable=self.v_vieta_varzbose,
                 bg=COLORS["entry_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"],
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1,
                 highlightbackground=COLORS["border"],
                 highlightcolor=COLORS["accent"]).grid(
            row=3, column=0, columnspan=2,
            sticky="ew", padx=12, pady=(2, 0))

        self.v_isleista_atgal = tk.BooleanVar()
        tk.Checkbutton(self.trofej_frame, text="🐟  Išleista atgal",
                       variable=self.v_isleista_atgal,
                       bg=COLORS["panel"], fg=COLORS["text"],
                       selectcolor=COLORS["entry_bg"],
                       activebackground=COLORS["panel"],
                       font=("Segoe UI", 10)).grid(
            row=4, column=0, columnspan=2,
            sticky="w", padx=12, pady=(6, 4))

        # Mygtukas
        tk.Button(parent, text="💾  Išsaugoti įrašą",
                  bg=COLORS["accent"], fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2",
                  activebackground="#21867a",
                  activeforeground="white",
                  pady=10,
                  command=self._issaugoti).grid(
            row=20, column=0, columnspan=2,
            sticky="ew", padx=12, pady=(16, 8))

        tk.Button(parent, text="✖  Išvalyti formą",
                  bg=COLORS["panel"], fg=COLORS["text_dim"],
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2",
                  activebackground=COLORS["card"],
                  command=self._isvályti_forma).grid(
            row=21, column=0, columnspan=2,
            sticky="ew", padx=12, pady=(0, 12))

    def _trofejinis_toggle(self):
        if self.v_trofejinis.get():
            self.trofej_frame.grid()
        else:
            self.trofej_frame.grid_remove()

    def _pasirinkti_nuotrauka(self):
        path = filedialog.askopenfilename(
            title="Pasirinkite nuotrauką",
            filetypes=[("Paveikslai", "*.jpg *.jpeg *.png *.bmp"),
                       ("Visi failai", "*.*")]
        )
        if path:
            # Kopijuojame į nuotraukų aplanką
            os.makedirs("nuotraukos", exist_ok=True)
            failo_vardas = os.path.basename(path)
            dest = os.path.join("nuotraukos", failo_vardas)
            shutil.copy2(path, dest)
            self.nuotrauka_path.set(dest)

    def _issaugoti(self):
        try:
            data = self.v_data.get().strip()
            vieta = self.v_vieta.get().strip()
            zuvis = self.v_zuvis.get().strip()

            if not data or not vieta or not zuvis:
                messagebox.showwarning(
                    "Trūksta duomenų",
                    "Privalomi laukai: Data, Vieta, Žuvis")
                return

            svoris = float(self.v_svoris.get() or 0)
            ilgis = float(self.v_ilgis.get() or 0)
            masalas = self.v_masalas.get().strip()
            pastabos = self.txt_pastabos.get("1.0", "end").strip()

            oras = OrasIrasas(
                temperatura=float(self.v_temp.get() or 0),
                oras_aprasas=self.v_oras.get()
            )

            if self.v_trofejinis.get():
                irasas = TrofejinisIrasas(
                    data=data, vieta=vieta,
                    zuvis_rusys=zuvis, svoris=svoris,
                    ilgis=ilgis, masalas=masalas,
                    oras=oras,
                    trofejaus_statusas=self.v_trofejaus_statusas.get(),
                    isleista_atgal=self.v_isleista_atgal.get(),
                    vieta_varzbose=self.v_vieta_varzbose.get().strip(),
                    nuotrauka_path=self.nuotrauka_path.get(),
                    pastabos=pastabos
                )
            else:
                irasas = ZvejybosIrasas(
                    data=data, vieta=vieta,
                    zuvis_rusys=zuvis, svoris=svoris,
                    ilgis=ilgis, masalas=masalas,
                    oras=oras,
                    nuotrauka_path=self.nuotrauka_path.get(),
                    pastabos=pastabos
                )

            self.dienorastis.prideti_irasa(irasas)
            self._atnaujinti_sarasa()
            self._isvályti_forma()
            messagebox.showinfo("✅ Išsaugota",
                                f"Įrašas sėkmingai išsaugotas!\n"
                                f"{zuvis} • {svoris} kg • {vieta}")

        except ValueError:
            messagebox.showerror(
                "Klaida",
                "Patikrinkite skaičių laukus (svoris, ilgis, temperatūra)"
            )

    def _istrinti(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Pasirinkite įrašą iš sąrašo")
            return

        item = self.tree.item(selection[0])
        irasas_id = item["tags"][0] if item["tags"] else None

        if irasas_id is None:
            return

        if messagebox.askyesno("Ištrinti",
                               "Ar tikrai norite ištrinti šį įrašą?"):
            self.dienorastis.istrinti(int(irasas_id))
            self._atnaujinti_sarasa()

    def _kopijuoti_irasa(self):
        """Užpildo formą pasirinkto įrašo duomenimis"""
        if self.pasirinktas_irasas is None:
            messagebox.showinfo("Info", "Pasirinkite įrašą iš sąrašo")
            return
        i = self.pasirinktas_irasas
        self.v_data.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.v_vieta.set(i.vieta)
        self.v_zuvis.set(i.zuvis_rusys)
        self.v_svoris.set(str(i.svoris))
        self.v_ilgis.set(str(i.ilgis))
        self.v_masalas.set(i.masalas)
        self.v_oras.set(i.oras.oras_aprasas)
        self.v_temp.set(str(i.oras.temperatura))
        self.txt_pastabos.delete("1.0", "end")
        self.txt_pastabos.insert("1.0", i.pastabos)

    def _pasirinkti_irasa(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        if item["tags"]:
            irasas_id = int(item["tags"][0])
            visi = self.dienorastis.gauti_visus()
            self.pasirinktas_irasas = next(
                (i for i in visi if i.irasas_id == irasas_id), None)

    def _atnaujinti_sarasa(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        irasai = self.dienorastis.gauti_visus()
        for i in irasai:
            trofejinis = isinstance(i, TrofejinisIrasas)
            self.tree.insert("", "end",
                             values=(
                                 ("🏆 " if trofejinis else "") + i.data,
                                 i.vieta,
                                 i.zuvis_rusys,
                                 f"{i.svoris} kg" if i.svoris else "—",
                                 i.masalas or "—",
                                 str(i.oras),
                             ),
                             tags=(str(i.irasas_id),)
                             )

        stat = self.dienorastis.statistika()
        if stat:
            self.stat_label.configure(
                text=f"Iš viso: {stat['viso_irasu']} įrašai  •  "
                f"Max: {stat['max_svoris']} kg  •  "
                f"Vidurkis: {stat['vid_svoris']} kg"
            )
        else:
            self.stat_label.configure(text="Kol kas įrašų nėra")

    def _isvályti_forma(self):
        self.v_data.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.v_vieta.set("")
        self.v_zuvis.set("")
        self.v_svoris.set("")
        self.v_ilgis.set("")
        self.v_masalas.set("")
        self.v_oras.set("")
        self.v_temp.set("")
        self.nuotrauka_path.set("")
        self.txt_pastabos.delete("1.0", "end")
        self.v_trofejinis.set(False)
        self.v_trofejaus_statusas.set("")
        self.v_isleista_atgal.set(False)
        self.v_vieta_varzbose.set("")
        self.trofej_frame.grid_remove()
        self.pasirinktas_irasas = None


# ─────────────────────────────────────────────
#  PALEIDIMAS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = ZvejoDienorastisApp()
    app.mainloop()
