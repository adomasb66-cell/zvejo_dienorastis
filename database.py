import sqlite3

from models import OrasIrasas, ZvejybosIrasas, TrofejinisIrasas


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
        trofejaus_statusas = (
            irasas.trofejaus_statusas if trofejinis else "")
        isleista_atgal = int(irasas.isleista_atgal) if trofejinis else 0
        vieta_varzbose = irasas.vieta_varzbose if trofejinis else ""
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("""
                INSERT INTO irasai
                (data, vieta, zuvis_rusys, svoris, ilgis, masalas,
                 temperatura, oras_aprasas, nuotrauka_path, pastabos,
                 trofejinis, trofejaus_statusas,
                 isleista_atgal, vieta_varzbose)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                irasas.data, irasas.vieta, irasas.zuvis_rusys,
                irasas.svoris, irasas.ilgis, irasas.masalas,
                irasas.oras.temperatura, irasas.oras.oras_aprasas,
                irasas.nuotrauka_path, irasas.pastabos,
                int(trofejinis), trofejaus_statusas,
                isleista_atgal, vieta_varzbose
            ))
            return cur.lastrowid

    def gauti_visus(self) -> list:
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


class Dienorastis:
    """Dienoraščio valdiklis - agregacija (saugo ZvejybosIrasas sąrašą)"""

    def __init__(self, db: DuomenuBaze):
        self._db = db
        self._irasai: list = []

    def prideti_irasa(self, irasas: ZvejybosIrasas) -> int:
        irasas_id = self._db.issaugoti(irasas)
        irasas.irasas_id = irasas_id
        self._irasai.append(irasas)
        return irasas_id

    def gauti_visus(self) -> list:
        self._irasai = self._db.gauti_visus()
        return self._irasai

    def istrinti(self, irasas_id: int):
        self._db.istrinti(irasas_id)
        self._irasai = [
            i for i in self._irasai if i.irasas_id != irasas_id]

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
