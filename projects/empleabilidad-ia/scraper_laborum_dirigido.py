"""Scraper dirigido de Laborum: busca por taxonomía de IA/datos y sube a Neon.

La API `beesearch` que usaba la versión anterior fue dada de baja (404). Laborum
rehizo el sitio: ahora `/search-jobs?q=` renderiza en el servidor y deja el estado
de Apollo serializado dentro del HTML, con la oferta completa —descripción
incluida— en `basicEdition[0].description`. Este scraper parsea eso.

    python scraper_laborum_dirigido.py --dry-run    # muestra qué subiría
    python scraper_laborum_dirigido.py              # scrapea y sube
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime

import psycopg
from curl_cffi import requests as cffi
from dotenv import load_dotenv

import clean_db

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
logger = logging.getLogger("laborum")

BUSQUEDA = "https://www.laborum.pe/search-jobs"
VERSION = "laborum_html_v3"

SEARCH_KEYWORDS = [
    "inteligencia artificial", "machine learning", "deep learning",
    "ciencia de datos", "data scientist", "data engineer", "data analyst",
    "analista de datos", "ingeniero de datos", "arquitecto de datos",
    "business intelligence", "power bi", "analytics", "big data",
    "python", "SQL", "ETL", "automatizacion de procesos", "RPA",
    "MLOps", "LLM", "chatbot",
]

# Convocatorias docentes y programas académicos: son universidades contratando
# profesores de IA, no empresas contratando gente que haga IA. Incluirlas inflaría
# la demanda medida con oferta educativa.
ACADEMICO = re.compile(
    r"posgrado|maestr[íi]a|asignatura|docente|instructor|catedr|profesor|diplomado",
    re.I,
)

INICIO_OBJETO = re.compile(r'\{"_id":"[a-f0-9]{24}"')
ETIQUETA_HTML = re.compile(r"<[^>]+>")

# El buscador de Laborum también coincide por subcadena: 'RPA' devuelve "ca-RPA-s"
# y "Co-RPA-c". Se reutiliza el filtro de clean_db.py para no ensuciar la base,
# traduciendo \y (Postgres) a \b (Python).
_RX_FUERTE = re.compile(clean_db.REGEX_FUERTE.replace(r"\y", r"\b"), re.I)
_RX_TITULO = re.compile(clean_db.REGEX_TITULO.replace(r"\y", r"\b"), re.I)


# --------------------------------------------------------------------------
# Parseo del HTML
# --------------------------------------------------------------------------


def objetos_json(html: str) -> list[dict]:
    """Recorta objetos JSON completos contando llaves y respetando strings.

    Un regex no basta: los objetos están anidados varios niveles.
    """
    salida, fin_anterior = [], 0
    for m in INICIO_OBJETO.finditer(html):
        i = m.start()
        if i < fin_anterior:  # ya consumido dentro de un objeto previo
            continue
        prof, en_str, esc = 0, False, False
        for j in range(i, min(i + 80_000, len(html))):
            c = html[j]
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                en_str = not en_str
            elif not en_str:
                if c == "{":
                    prof += 1
                elif c == "}":
                    prof -= 1
                    if prof == 0:
                        try:
                            d = json.loads(html[i:j + 1])
                            if d.get("__typename") == "Job" and d.get("job_id"):
                                salida.append(d)
                        except json.JSONDecodeError:
                            pass
                        fin_anterior = j
                        break
    return salida


def _descripcion(o: dict) -> str:
    for bloque in o.get("basicEdition") or []:
        if isinstance(bloque, dict) and isinstance(bloque.get("description"), str):
            return bloque["description"]
    return ""


def _empresa(o: dict) -> str:
    dc = o.get("detailCompany") or {}
    for clave in ("name", "company_name", "companyName", "razon_social"):
        if isinstance(dc.get(clave), str) and dc[clave].strip():
            return dc[clave].strip()
    return ""


def _lista_titulo_valor(items) -> str:
    """Aplana [{title, value}] a texto legible."""
    partes = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        valor = it.get("value")
        if isinstance(valor, list):
            valor = ", ".join(str(v) for v in valor)
        if valor:
            partes.append(f"{it.get('title', '')}: {valor}")
    return " | ".join(partes)


def normalizar(o: dict) -> dict:
    """Devuelve el payload con las mismas claves que ya usan las filas de Laborum."""
    return {
        "job_id": o.get("job_id"),
        "title": o.get("title") or "",
        "company": _empresa(o),
        "company_id": o.get("company_id"),
        "description": _descripcion(o),
        "requirements": _lista_titulo_valor(o.get("requirements")),
        "benefits": _lista_titulo_valor(o.get("benefits")),
        "detail_job": _lista_titulo_valor(o.get("detailJob")),
        "lugar": o.get("Lugar") or "",
        "area": o.get("area") or "",
        "area_list": o.get("Area") or [],
        "jerarquia": o.get("Jerarquía") or "",
        "horario": o.get("Horario"),
        "publish_date": o.get("publishDate") or o.get("firstPublicationDate"),
        "expiration_date": o.get("expirationDate"),
        "status": o.get("status"),
        "visibility": o.get("visibility"),
        "url_original": f"https://www.laborum.pe/job/{o.get('job_id')}",
        "fuente": "la",
    }


def es_util(p: dict) -> tuple[bool, str]:
    texto_plano = ETIQUETA_HTML.sub(" ", p["description"])
    if len(texto_plano) < 200:
        return False, "sin descripción"
    if ACADEMICO.search(p["title"]) or ACADEMICO.search(texto_plano[:400]):
        return False, "convocatoria docente"
    if not (_RX_TITULO.search(p["title"]) or _RX_FUERTE.search(texto_plano)
            or _RX_FUERTE.search(p["requirements"])):
        return False, "sin señal de IA/datos"
    return True, ""


# --------------------------------------------------------------------------
# Scraping
# --------------------------------------------------------------------------


def buscar(keyword: str) -> list[dict]:
    try:
        r = cffi.get(BUSQUEDA, params={"q": keyword}, impersonate="chrome120", timeout=40)
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s: fallo de red (%s)", keyword, type(exc).__name__)
        return []
    if r.status_code != 200:
        logger.warning("%s: HTTP %s", keyword, r.status_code)
        return []
    return objetos_json(r.text)


def ids_existentes() -> set[str]:
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT source_id FROM raw_ofertas WHERE fuente = 'la'")
        return {r[0] for r in cur.fetchall()}


def subir(payloads: list[dict]) -> int:
    nuevas = 0
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        for p in payloads:
            cur.execute(
                """
                INSERT INTO raw_ofertas (fuente, source_id, payload, scraper_version, scraped_at)
                VALUES (%s, %s, %s::jsonb, %s, NOW())
                ON CONFLICT (fuente, source_id) DO NOTHING
                """,
                ("la", p["job_id"], json.dumps(p), VERSION),
            )
            nuevas += cur.rowcount
        conn.commit()
    return nuevas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="no escribe en la base")
    ap.add_argument("--pausa", type=float, default=1.2, help="segundos entre búsquedas")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    ya = ids_existentes()
    logger.info("Ya en la base: %d ofertas de Laborum", len(ya))

    crudas: dict[str, dict] = {}
    for kw in SEARCH_KEYWORDS:
        encontradas = buscar(kw)
        for o in encontradas:
            crudas[o["job_id"]] = o
        logger.info("  %-28s %3d ofertas", kw, len(encontradas))
        time.sleep(args.pausa)

    logger.info("Únicas extraídas: %d", len(crudas))

    utiles, descartes = [], {}
    for jid, o in crudas.items():
        if jid in ya:
            descartes["ya en la base"] = descartes.get("ya en la base", 0) + 1
            continue
        p = normalizar(o)
        ok, motivo = es_util(p)
        if ok:
            utiles.append(p)
        else:
            descartes[motivo] = descartes.get(motivo, 0) + 1

    print("\n=== RESUMEN ===")
    for motivo, n in sorted(descartes.items(), key=lambda x: -x[1]):
        print(f"  descartadas ({motivo}): {n}")
    print(f"  NUEVAS Y ÚTILES: {len(utiles)}")

    print("\n=== muestra ===")
    for p in utiles[:15]:
        print(f"  {p['title'][:58]:<58} | {p['lugar'][:22]}")

    if args.dry_run:
        print("\n[dry-run] Nada se escribió. Quita --dry-run para subir.")
        return

    if not utiles:
        print("\nNada nuevo que subir.")
        return

    n = subir(utiles)
    print(f"\nSubidas: {n} (el índice único descartó {len(utiles) - n} repetidas)")


if __name__ == "__main__":
    main()
