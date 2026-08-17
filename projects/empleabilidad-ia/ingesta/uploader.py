"""Carga los JSON de `data_raw/` a la tabla `raw_ofertas` de Neon.

La deduplicación depende de que `source_id` quede bien poblado: cada portal
nombra su identificador distinto (Laborum usa `job_id`, LinkedIn y Get on Board
usan `id`), y los scrapers consultan esa columna para no volver a subir lo mismo.
"""

import glob
import json
import os
import re

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Orden de preferencia del identificador nativo de cada portal.
CLAVES_ID = ("job_id", "id", "jobId", "refId")

# Prefijo del nombre de archivo -> código de fuente.
FUENTES = {"laborum": "la", "la": "la", "li": "li", "linkedin": "li", "gob": "gob",
           "getonboard": "gob"}


def detectar_fuente(item: dict, ruta: str) -> str:
    """Prefiere la fuente que declaró el scraper; si no, la deduce del archivo."""
    if item.get("fuente"):
        return item["fuente"]
    nombre = os.path.basename(ruta).lower()
    for prefijo, codigo in FUENTES.items():
        if nombre.startswith(prefijo):
            return codigo
    raise ValueError(
        f"No puedo deducir la fuente de '{os.path.basename(ruta)}'. "
        f"Renombra el archivo con un prefijo conocido {tuple(FUENTES)} "
        f"o agrega 'fuente' al JSON."
    )


def extraer_source_id(item: dict) -> str | None:
    for clave in CLAVES_ID:
        valor = item.get(clave)
        # Antes se usaba str(item.get("id", ...)) sin validar: como Laborum no
        # tiene 'id', las 751 filas quedaron con source_id = "None" y la
        # deduplicación de todos los scrapers dejó de funcionar.
        if valor not in (None, ""):
            return str(valor)
    return None


def subir(ruta: str) -> tuple[int, int, int]:
    print(f"\nProcesando: {ruta}")
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]

    nuevos = repetidos = sin_id = 0
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for item in data:
                fuente = detectar_fuente(item, ruta)
                source_id = extraer_source_id(item)
                if source_id is None:
                    sin_id += 1
                    print(f"  omitida sin identificador: {item.get('title', 'N/A')[:60]}")
                    continue
                cur.execute(
                    """
                    INSERT INTO raw_ofertas (fuente, source_id, payload, scraper_version, scraped_at)
                    VALUES (%s, %s, %s::jsonb, %s, NOW())
                    ON CONFLICT (fuente, source_id) DO NOTHING
                    """,
                    (fuente, source_id, json.dumps(item), "mini_proy_ia_v2"),
                )
                if cur.rowcount:
                    nuevos += 1
                else:
                    repetidos += 1
            conn.commit()

    print(f"  nuevas: {nuevos} | ya existían: {repetidos} | sin id: {sin_id}")
    return nuevos, repetidos, sin_id


if __name__ == "__main__":
    archivos = sorted(glob.glob("data_raw/*.json"))
    if not archivos:
        raise SystemExit("No se encontraron archivos JSON en data_raw/")

    totales = [0, 0, 0]
    for ruta in archivos:
        for i, v in enumerate(subir(ruta)):
            totales[i] += v

    print(f"\nTotal -> nuevas: {totales[0]} | repetidas: {totales[1]} | sin id: {totales[2]}")
