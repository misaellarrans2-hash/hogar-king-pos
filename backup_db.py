"""Respaldo simple de la base de datos.

Copia el archivo SQLite a la carpeta backups/ con la fecha y hora en el
nombre. Pensado para ejecutarse a diario (por ejemplo con el Programador
de tareas de Windows) una vez el sistema tenga datos reales.

Uso:
    python backup_db.py
"""

import shutil
from datetime import datetime
from pathlib import Path

from config import Config

BASE_DIR = Path(__file__).resolve().parent
BACKUPS_DIR = BASE_DIR / "backups"


def backup():
    db_path = Path(Config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", ""))

    if not db_path.exists():
        print(f"No se encontro la base de datos en: {db_path}")
        return

    BACKUPS_DIR.mkdir(exist_ok=True)

    marca_de_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = BACKUPS_DIR / f"hogar_king_{marca_de_tiempo}.db"

    shutil.copy2(db_path, destino)
    print(f"Respaldo creado: {destino}")


if __name__ == "__main__":
    backup()
