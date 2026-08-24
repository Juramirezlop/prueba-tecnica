"""
Prepara la base de datos completa a partir del Excel original: limpieza,
tablas, usuarios y carga de datos, en un solo comando.

Que hace:
1. Lee las hojas SECOP y CC2026 de data/PRUEBA_TECNICA.xlsx.
2. Limpia cada hoja:
   - Elimina columnas con mas del 95% de valores vacios.
   - Elimina filas sin valor en la columna llave.
   - Elimina filas de paginacion (artefacto del scraping original de SECOP:
     filas donde todas las columnas repiten el mismo numero corto y no hay
     URL de detalle; no son procesos reales).
   - Elimina duplicados por llave (se conserva el primero).
   - Normaliza nombres de columnas a snake_case.
   - Selecciona el subconjunto final de columnas con informacion util.
3. Guarda el resultado limpio como CSV en data/ (evidencia del proceso de
   depuracion para la sustentacion tecnica, ver docs/quickstart.md).
4. Crea las tablas en PostgreSQL si no existen.
5. Crea los 3 usuarios de prueba (uno por rol) si no existen.
6. Carga los datos limpios si las tablas estan vacias.

Requiere que data/PRUEBA_TECNICA.xlsx exista (colocar el archivo original
ahi antes de ejecutar).

Uso:
    python scripts/setup_db.py
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import CC2026, Secop, Usuario  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "PRUEBA_TECNICA.xlsx"

# Umbral: si una columna tiene menos de este porcentaje de datos, se descarta.
MIN_FILL_RATIO = 0.05

# Columnas que se conservan en el esquema final, ya con nombre normalizado.
# El resto de columnas que sobreviven al filtro de nulos son ruido de la
# exportacion original (iconos, banderas, texto constante) y no aportan
# informacion para el aplicativo, por lo que se descartan aqui explicitamente.
SECOP_FINAL_COLUMNS = {
    "pais": "pais",
    "entidad_estatal": "entidad_estatal",
    "referencia": "referencia",
    "descripcion": "descripcion",
    "fase_actual": "fase_actual",
    "fecha_de_publicacion": "fecha_publicacion",
    "fecha_de_presentacion_de_ofertas": "fecha_presentacion_ofertas",
    "column_8_url": "url_detalle",
}

CC2026_FINAL_COLUMNS = {
    "no": "numero",
    "radicacion": "radicacion",
    "ponente": "ponente",
    "norma_demandada": "norma_demandada",
    "demandante": "demandante",
    "fecha": "fecha",
    "url_proceso": "url_proceso",
    "url_demanda": "url_demanda",
    "capture_date": "capture_date",
}

# Usuarios de prueba, uno por rol. Cambiar la contrasena antes de exponer
# el servicio publicamente.
USUARIOS_INICIALES = [
    {"username": "admin", "password": "admin123", "rol": "administrador"},
    {"username": "digitador", "password": "digitador123", "rol": "digitador"},
    {"username": "consulta", "password": "consulta123", "rol": "consulta"},
]


# ---------------------------------------------------------------------------
# Limpieza
# ---------------------------------------------------------------------------

def normalize_column_name(name: str) -> str:
    """Convierte un nombre de columna de Excel a snake_case ascii."""
    name = str(name).strip()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name


def drop_empty_columns(df: pd.DataFrame, min_fill_ratio: float) -> pd.DataFrame:
    """Elimina columnas cuyo porcentaje de valores no nulos es menor al umbral."""
    total_rows = len(df)
    keep_columns = []
    for col in df.columns:
        fill_ratio = df[col].notna().sum() / total_rows if total_rows else 0
        if fill_ratio >= min_fill_ratio:
            keep_columns.append(col)
    return df[keep_columns]


def clean_secop(raw: pd.DataFrame) -> pd.DataFrame:
    df = drop_empty_columns(raw, MIN_FILL_RATIO)
    df.columns = [normalize_column_name(c) for c in df.columns]

    key_col = "referencia"
    df = df.dropna(subset=[key_col])
    df[key_col] = df[key_col].astype(str).str.strip()
    df = df[df[key_col] != ""]

    # Artefactos de paginacion del scraping original: filas donde todas las
    # columnas principales repiten el mismo numero corto (1, 2, 3, ...) y no
    # tienen URL de detalle. No son procesos reales, se descartan.
    es_contador_paginacion = df[key_col].str.match(r"^\d{1,3}$") & df["column_8_url"].isna()
    df = df[~es_contador_paginacion]

    df = df.drop_duplicates(subset=[key_col], keep="first")

    df = df[[c for c in SECOP_FINAL_COLUMNS if c in df.columns]]
    df = df.rename(columns=SECOP_FINAL_COLUMNS)

    return df.reset_index(drop=True)


def clean_cc2026(raw: pd.DataFrame) -> pd.DataFrame:
    df = drop_empty_columns(raw, MIN_FILL_RATIO)
    df.columns = [normalize_column_name(c) for c in df.columns]

    key_col = "radicacion"
    df = df.dropna(subset=[key_col])
    df[key_col] = df[key_col].astype(str).str.strip()
    df = df[df[key_col] != ""]
    df = df.drop_duplicates(subset=[key_col], keep="first")

    df = df[[c for c in CC2026_FINAL_COLUMNS if c in df.columns]]
    df = df.rename(columns=CC2026_FINAL_COLUMNS)

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

def crear_tablas():
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas u ok si ya existian.")


def crear_usuarios(db):
    for datos in USUARIOS_INICIALES:
        existe = db.query(Usuario).filter(Usuario.username == datos["username"]).first()
        if existe:
            continue
        usuario = Usuario(
            username=datos["username"],
            password_hash=hash_password(datos["password"]),
            rol=datos["rol"],
        )
        db.add(usuario)
    db.commit()
    print("Usuarios de prueba listos:")
    for datos in USUARIOS_INICIALES:
        print(f"  - {datos['username']} / {datos['password']} ({datos['rol']})")


def cargar_secop(db, df: pd.DataFrame):
    if db.query(Secop).count() > 0:
        print("SECOP ya tiene datos, se omite la carga.")
        return
    for _, fila in df.fillna("").astype(str).iterrows():
        db.add(Secop(**fila.to_dict()))
    db.commit()
    print(f"SECOP: {len(df)} registros cargados.")


def cargar_cc2026(db, df: pd.DataFrame):
    if db.query(CC2026).count() > 0:
        print("CC2026 ya tiene datos, se omite la carga.")
        return
    for _, fila in df.fillna("").astype(str).iterrows():
        db.add(CC2026(**fila.to_dict()))
    db.commit()
    print(f"CC2026: {len(df)} registros cargados.")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontro {INPUT_FILE}. Coloca el archivo PRUEBA_TECNICA.xlsx en data/ "
            "antes de ejecutar este script."
        )

    raw_secop = pd.read_excel(INPUT_FILE, sheet_name="SECOP")
    raw_cc2026 = pd.read_excel(INPUT_FILE, sheet_name="CC2026")

    secop = clean_secop(raw_secop)
    cc2026 = clean_cc2026(raw_cc2026)

    secop_out = DATA_DIR / "secop_clean.csv"
    cc2026_out = DATA_DIR / "cc2026_clean.csv"
    secop.to_csv(secop_out, index=False)
    cc2026.to_csv(cc2026_out, index=False)

    print("Limpieza completada.")
    print(f"SECOP:  {raw_secop.shape[0]} filas originales -> {secop.shape[0]} filas limpias "
          f"-> {secop_out}")
    print(f"CC2026: {raw_cc2026.shape[0]} filas originales -> {cc2026.shape[0]} filas limpias "
          f"-> {cc2026_out}")

    crear_tablas()
    db = SessionLocal()
    try:
        crear_usuarios(db)
        cargar_secop(db, secop)
        cargar_cc2026(db, cc2026)
    finally:
        db.close()


if __name__ == "__main__":
    main()
