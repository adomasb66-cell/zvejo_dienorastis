from abc import ABC, abstractmethod


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
                         masalas, oras, nuotrauka_path, pastabos,
                         irasas_id)
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
