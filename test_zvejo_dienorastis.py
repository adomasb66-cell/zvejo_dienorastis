import unittest
import os
from zvejo_dienorastis import (
    BazinisIrasas, ZvejybosIrasas, TrofejinisIrasas,
    OrasIrasas, Dienorastis, DuomenuBaze
)


def sukurti_irasa(**kwargs):
    """Pagalbinė funkcija - sukuria standartinį įrašą"""
    oras = OrasIrasas(temperatura=15.0, oras_aprasas="Saulėta")
    numatytieji = dict(
        data="2024-06-01 10:00",
        vieta="Kauno marios",
        zuvis_rusys="Karšis",
        svoris=2.5,
        ilgis=35.0,
        masalas="Sliekas",
        oras=oras
    )
    numatytieji.update(kwargs)
    return ZvejybosIrasas(**numatytieji)


def sukurti_trofeji(**kwargs):
    """Pagalbinė funkcija - sukuria trofėjinį įrašą"""
    oras = OrasIrasas(temperatura=20.0, oras_aprasas="Debesuota")
    numatytieji = dict(
        data="2024-07-15 08:00",
        vieta="Nemunas",
        zuvis_rusys="Lydeka",
        svoris=8.0,
        ilgis=95.0,
        masalas="Blizgė",
        oras=oras,
        trofejaus_statusas="Asmeninis rekordas",
        isleista_atgal=False,
        vieta_varzbose="1 vieta"
    )
    numatytieji.update(kwargs)
    return TrofejinisIrasas(**numatytieji)


# ─────────────────────────────────────────────
#  OrasIrasas testai
# ─────────────────────────────────────────────

class TestOrasIrasas(unittest.TestCase):

    def test_sukurimas(self):
        oras = OrasIrasas(temperatura=18.5, oras_aprasas="Lietinga")
        self.assertEqual(oras.temperatura, 18.5)
        self.assertEqual(oras.oras_aprasas, "Lietinga")

    def test_str(self):
        oras = OrasIrasas(temperatura=10.0, oras_aprasas="Vėjuota")
        self.assertIn("10.0", str(oras))
        self.assertIn("Vėjuota", str(oras))

    def test_numatytosios_reiksmes(self):
        oras = OrasIrasas()
        self.assertEqual(oras.temperatura, 0.0)
        self.assertEqual(oras.oras_aprasas, "")


# ─────────────────────────────────────────────
#  ZvejybosIrasas testai
# ─────────────────────────────────────────────

class TestZvejybosIrasas(unittest.TestCase):

    def test_sukurimas(self):
        irasas = sukurti_irasa()
        self.assertEqual(irasas.vieta, "Kauno marios")
        self.assertEqual(irasas.zuvis_rusys, "Karšis")
        self.assertEqual(irasas.svoris, 2.5)

    def test_santrauka(self):
        irasas = sukurti_irasa()
        santrauka = irasas.santrauka()
        self.assertIn("Kauno marios", santrauka)
        self.assertIn("Karšis", santrauka)
        self.assertIn("2.5", santrauka)

    def test_str_naudoja_santrauka(self):
        irasas = sukurti_irasa()
        self.assertEqual(str(irasas), irasas.santrauka())

    def test_svoris_setter_teigiamas(self):
        irasas = sukurti_irasa()
        irasas.svoris = 5.0
        self.assertEqual(irasas.svoris, 5.0)

    def test_svoris_setter_neigiamas(self):
        irasas = sukurti_irasa()
        with self.assertRaises(ValueError):
            irasas.svoris = -1.0

    def test_pastabos_setter(self):
        irasas = sukurti_irasa()
        irasas.pastabos = "Gera diena žvejybai"
        self.assertEqual(irasas.pastabos, "Gera diena žvejybai")

    def test_nuotrauka_numatyta_tuscia(self):
        irasas = sukurti_irasa()
        self.assertEqual(irasas.nuotrauka_path, "")

    def test_abstrakti_klase_negalima_sukurti(self):
        """BazinisIrasas yra abstrakti — negalima sukurti tiesiogiai"""
        with self.assertRaises(TypeError):
            BazinisIrasas("2024-01-01", "Vieta")


# ─────────────────────────────────────────────
#  TrofejinisIrasas testai (Polymorphism)
# ─────────────────────────────────────────────

class TestTrofejinisIrasas(unittest.TestCase):

    def test_sukurimas(self):
        trofejus = sukurti_trofeji()
        self.assertEqual(trofejus.trofejaus_statusas, "Asmeninis rekordas")
        self.assertEqual(trofejus.vieta_varzbose, "1 vieta")
        self.assertFalse(trofejus.isleista_atgal)

    def test_paveldejimas(self):
        """TrofejinisIrasas paveldi iš ZvejybosIrasas"""
        trofejus = sukurti_trofeji()
        self.assertIsInstance(trofejus, ZvejybosIrasas)
        self.assertIsInstance(trofejus, BazinisIrasas)

    def test_polymorphism_santrauka(self):
        """Polymorphism — santrauka() skirtinga nei ZvejybosIrasas"""
        paprastas = sukurti_irasa(zuvis_rusys="Karšis", svoris=2.5)
        trofejus = sukurti_trofeji(zuvis_rusys="Lydeka", svoris=8.0)

        self.assertNotEqual(paprastas.santrauka(), trofejus.santrauka())
        self.assertIn("🏆", trofejus.santrauka())
        self.assertNotIn("🏆", paprastas.santrauka())

    def test_isleista_atgal(self):
        trofejus = sukurti_trofeji(isleista_atgal=True)
        self.assertTrue(trofejus.isleista_atgal)
        self.assertIn("išleista atgal", trofejus.santrauka())

    def test_statusai_sarasas(self):
        """Patikrinti kad STATUSAI sąrašas nėra tuščias"""
        self.assertGreater(len(TrofejinisIrasas.STATUSAI), 0)
        self.assertIn("Asmeninis rekordas", TrofejinisIrasas.STATUSAI)


# ─────────────────────────────────────────────
#  DuomenuBaze Singleton testai
# ─────────────────────────────────────────────

class TestDuomenuBazeSingleton(unittest.TestCase):

    def test_singleton(self):
        """Du DuomenuBaze() kvietimai grąžina tą patį objektą"""
        db1 = DuomenuBaze("test_singleton.db")
        db2 = DuomenuBaze("test_singleton.db")
        self.assertIs(db1, db2)

    def tearDown(self):
        # Singleton reset tarp testų
        DuomenuBaze._instance = None
        if os.path.exists("test_singleton.db"):
            os.remove("test_singleton.db")


# ─────────────────────────────────────────────
#  Dienorastis testai
# ─────────────────────────────────────────────

class TestDienorastis(unittest.TestCase):

    def setUp(self):
        DuomenuBaze._instance = None
        self.db = DuomenuBaze("test_dienorastis.db")
        self.dienorastis = Dienorastis(self.db)

    def tearDown(self):
        DuomenuBaze._instance = None
        if os.path.exists("test_dienorastis.db"):
            os.remove("test_dienorastis.db")

    def test_prideti_irasa(self):
        irasas = sukurti_irasa()
        irasas_id = self.dienorastis.prideti_irasa(irasas)
        self.assertIsNotNone(irasas_id)
        self.assertGreater(irasas_id, 0)

    def test_gauti_visus_tucias(self):
        irasai = self.dienorastis.gauti_visus()
        self.assertEqual(len(irasai), 0)

    def test_gauti_visus_su_irasais(self):
        self.dienorastis.prideti_irasa(sukurti_irasa())
        self.dienorastis.prideti_irasa(sukurti_irasa(vieta="Neris"))
        irasai = self.dienorastis.gauti_visus()
        self.assertEqual(len(irasai), 2)

    def test_istrinti(self):
        irasas = sukurti_irasa()
        irasas_id = self.dienorastis.prideti_irasa(irasas)
        self.dienorastis.istrinti(irasas_id)
        irasai = self.dienorastis.gauti_visus()
        self.assertEqual(len(irasai), 0)

    def test_statistika_tuscia(self):
        stat = self.dienorastis.statistika()
        self.assertEqual(stat, {})

    def test_statistika_su_irasais(self):
        self.dienorastis.prideti_irasa(sukurti_irasa(svoris=2.0))
        self.dienorastis.prideti_irasa(sukurti_irasa(svoris=4.0))
        stat = self.dienorastis.statistika()
        self.assertEqual(stat["viso_irasu"], 2)
        self.assertEqual(stat["max_svoris"], 4.0)
        self.assertEqual(stat["vid_svoris"], 3.0)

    def test_trofejinis_issaugomas_ir_grąžinamas(self):
        trofejus = sukurti_trofeji()
        self.dienorastis.prideti_irasa(trofejus)
        irasai = self.dienorastis.gauti_visus()
        self.assertEqual(len(irasai), 1)
        self.assertIsInstance(irasai[0], TrofejinisIrasas)
        self.assertEqual(irasai[0].trofejaus_statusas, "Asmeninis rekordas")


# ─────────────────────────────────────────────
#  PALEIDIMAS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
