# Žvejo Dienoraštis — Kursinio Darbo Ataskaita

---

## 1. Įvadas

### 1.1 Kas yra ši programa?

**Žvejo Dienoraštis** — tai grafinė Python programa skirta žvejams saugoti ir tvarkyti savo žvejybos įrašus. Programa leidžia fiksuoti kiekvieną žvejybą: sugautą žuvį, vietą, orą, naudotą masalą ir kitus duomenis. Ypatingi laimikiai gali būti pažymėti kaip trofėjiniai įrašai su papildomu aprašymu.

Programa sukurta naudojant objektinio programavimo (OOP) principus ir saugo duomenis lokaliai SQLite duomenų bazėje.

### 1.2 Kaip paleisti programą?

**Reikalavimai:**

- Python 3.10 arba naujesnė versija
- Tkinter biblioteka (integruota į Python)
- SQLite (integruota į Python)

**Paleidimas iš komandinės eilutės:**

```bash
python zvejo_dienorastis.py
```

**Paleidimas kaip vykdomasis failas:**

Jei programa sukompiliuota su PyInstaller, tiesiog paleisti:

```
ZvejoDienorastis.exe
```

**Kompiliavimas į .exe:**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ZvejoDienorastis" zvejo_dienorastis.py
```

Sukompiliuotas failas atsiras `dist/` aplanke.

### 1.3 Kaip naudotis programa?

1. **Naujo įrašo pridėjimas** — dešinėje esančioje formoje užpildyti laukus: data, vieta, žuvies rūšis, svoris, ilgis, masalas, oras, temperatūra. Paspausti mygtuką „Išsaugoti įrašą".
2. **Trofėjinis įrašas** — pažymėti varnelę „Trofėjinis laimikis" ir užpildyti papildomus laukus: statusą, vietą varžybose, ar žuvis išleista atgal.
3. **Nuotraukos pridėjimas** — paspausti „Pasirinkti" šalia nuotraukos lauko ir pasirinkti paveikslėlį iš kompiuterio.
4. **Įrašo kopijavimas** — pasirinkti įrašą sąraše ir paspausti „Kopijuoti", forma užsipildys tais duomenimis.
5. **Įrašo trynimas** — pasirinkti įrašą sąraše ir paspausti „Ištrinti".
6. **Statistika** — rodoma automatiškai lango viršuje: iš viso įrašų, maksimalus ir vidutinis svoris.

---

## 2. Analizė

### 2.1 Funkcinių reikalavimų įgyvendinimas

#### Modulių struktūra

Programos kodas padalintas į atskirus modulius:

| Failas | Aprašymas |
|---|---|
| `constants.py` | Spalvos, žuvų ir orų sąrašai |
| `models.py` | OOP klasės (`BazinisIrasas`, `ZvejybosIrasas`, `TrofejinisIrasas`, `OrasIrasas`) |
| `database.py` | `DuomenuBaze` ir `Dienorastis` klasės |
| `utils.py` | Pagalbinės funkcijos (nuotraukų kopijavimas) |
| `gui.py` | Grafinės sąsajos klasė `ZvejoDienorastisApp` |
| `zvejo_dienorastis.py` | Pagrindinis failas — tik programos paleidimas |

#### OOP principai

Programa realizuoja visus keturis OOP principus:

**Abstrakcija (Abstraction)**

`BazinisIrasas` yra abstrakti klasė, kuri apibrėžia bendrą įrašo struktūrą. Joje deklaruotas abstraktus metodas `santrauka()`, kurį privalo realizuoti kiekviena paveldinti klasė. Abstrakčios klasės objekto tiesiogiai sukurti negalima.

```python
class BazinisIrasas(ABC):
    @abstractmethod
    def santrauka(self) -> str:
        pass
```

**Paveldėjimas (Inheritance)**

`ZvejybosIrasas` paveldi iš `BazinisIrasas` ir realizuoja `santrauka()` metodą. `TrofejinisIrasas` paveldi iš `ZvejybosIrasas` ir prideda trofėjiniams įrašams būdingus atributus.

```
BazinisIrasas
    └── ZvejybosIrasas
            └── TrofejinisIrasas
```

**Inkapsuliacija (Encapsulation)**

Visi klasių atributai yra privatūs (prasideda `_`). Prieiga prie jų realizuota per `@property` ir `setter` metodus. Pvz., `svoris` setter tikrina, kad reikšmė nebūtų neigiama:

```python
@svoris.setter
def svoris(self, value: float):
    if value < 0:
        raise ValueError("Svoris negali būti neigiamas")
    self._svoris = value
```

**Polimorfizmas (Polymorphism)**

`santrauka()` metodas veikia skirtingai priklausomai nuo objekto tipo. `ZvejybosIrasas` grąžina paprastą eilutę, o `TrofejinisIrasas` — išplėstą su trofėjaus informacija ir 🏆 simboliu:

```python
# ZvejybosIrasas
def santrauka(self) -> str:
    return f"{self._data} | {self._vieta} | {self._zuvis_rusys} {self._svoris}kg"

# TrofejinisIrasas
def santrauka(self) -> str:
    return f"🏆 {self._data} | {self._vieta} | {self._zuvis_rusys} ..."
```

#### Kompozicija ir agregacija

- **Kompozicija** — `OrasIrasas` objektas sukuriamas ir saugomas `ZvejybosIrasas` viduje. Jei įrašas ištrinamas, oro duomenys taip pat dingsta.
- **Agregacija** — `Dienorastis` klasė saugo `ZvejybosIrasas` objektų sąrašą. Objektai egzistuoja nepriklausomai duomenų bazėje.

#### Design Pattern — Singleton

`DuomenuBaze` klasė realizuoja Singleton šabloną — garantuoja, kad per visą programos veikimą egzistuoja tik vienas duomenų bazės objektas:

```python
class DuomenuBaze:
    _instance = None

    def __new__(cls, db_path="zvejo_dienorastis.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

#### Darbas su failais

- **Rašymas į failą** — `DuomenuBaze.issaugoti()` metodas rašo įrašus į `zvejo_dienorastis.db` SQLite failą.
- **Skaitymas iš failo** — `DuomenuBaze.gauti_visus()` metodas skaito visus įrašus iš duomenų bazės failo.
- **Nuotraukų kopijavimas** — `shutil.copy2()` kopijuoja pasirinktas nuotraukas į `nuotraukos/` aplanką.

#### Grafinė vartotojo sąsaja (GUI)

Programa naudoja `Tkinter` biblioteką. Pagrindinis langas suskirstytas į dvi dalis:

- **Kairė** — įrašų sąrašas `Treeview` lentelėje su filtravimo ir valdymo mygtukais.
- **Dešinė** — forma naujam įrašui su slinkties galimybe.

#### Unit testai

Parašyti 18 unit testų naudojant `unittest` biblioteką, apimantys:

- `OrasIrasas` sukūrimą ir `__str__` metodą
- `ZvejybosIrasas` atributus, setter validaciją ir abstrakčios klasės patikrinimą
- `TrofejinisIrasas` paveldėjimą ir polimorfizmą
- `DuomenuBaze` Singleton šabloną
- `Dienorastis` CRUD operacijas ir statistiką

Testų paleidimas:

```bash
python test_zvejo_dienorastis.py
```

#### PEP8

Visas programos kodas atitinka PEP8 stilių. Patikrinta su `flake8`:

```bash
flake8 zvejo_dienorastis.py
```

---

## 3. Rezultatai ir išvados

### 3.1 Rezultatai

Programa sėkmingai įgyvendinta su šiomis funkcijomis:

| Funkcija | Būsena |
|---|---|
| Įrašų pridėjimas | ✅ |
| Įrašų peržiūra | ✅ |
| Įrašų trynimas | ✅ |
| Trofėjiniai įrašai | ✅ |
| Nuotraukų pridėjimas ir peržiūra | ✅ |
| Statistika | ✅ |
| SQLite duomenų bazė | ✅ |
| 4 OOP principai | ✅ |
| Singleton design pattern | ✅ |
| Modulių struktūra (6 failai) | ✅ |
| Unit testai (18 vnt.) | ✅ |
| PEP8 atitikimas | ✅ |

### 3.2 Išvados

Kurso darbo metu sukurta pilnavertė Python programa su grafine sąsaja. Realizuoti visi keturi OOP principai: abstrakcija, paveldėjimas, inkapsuliacija ir polimorfizmas. Panaudotas Singleton projektavimo šablonas duomenų bazės valdymui. Programa veikia stabiliai, duomenys išsaugomi tarp paleidimų, o kodas atitinka PEP8 stilių.

### 3.3 Galimi programos plėtiniai

- **Paieška ir filtravimas** — galimybė filtruoti įrašus pagal žuvies rūšį, datą ar vietą
- **Eksportas į CSV/PDF** — įrašų eksportavimas ataskaitoms
- **Žemėlapis** — žvejybos vietų žymėjimas interaktyviame žemėlapyje
- **Grafikai** — laimikių statistikos vizualizacija (pvz., svoris pagal mėnesį)
- **Vartotojų paskyros** — kelių žvejų duomenų atskyrimas

---

## 4. Šaltiniai

- Python dokumentacija — <https://docs.python.org/3/>
- Tkinter dokumentacija — <https://docs.python.org/3/library/tkinter.html>
- SQLite dokumentacija — <https://www.sqlite.org/docs.html>
- PEP8 stilių gidas — <https://peps.python.org/pep-0008/>
- unittest dokumentacija — <https://docs.python.org/3/library/unittest.html>
