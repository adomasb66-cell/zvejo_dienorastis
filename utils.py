import os
import shutil


def kopijuoti_nuotrauka(path: str) -> str:
    """Kopijuoja nuotrauką į nuotraukos/ aplanką.
    Grąžina naują kelią."""
    os.makedirs("nuotraukos", exist_ok=True)
    failo_vardas = os.path.basename(path)
    dest = os.path.join("nuotraukos", failo_vardas)
    shutil.copy2(path, dest)
    return dest
