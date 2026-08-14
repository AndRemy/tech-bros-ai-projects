"""Scraper de LinkedIn vía Apify, dirigido a Perú y con control de gasto.

Correcciones sobre la versión anterior, que dejó el corpus sesgado:
  · De 9 keywords configuradas solo se ejecutaron 2, y "Machine Learning Engineer"
    aportó el 97% de las ofertas. Ahora hay tope por keyword para que el crédito
    alcance para todas y ninguna monopolice la muestra.
  · `tipo_remoto` miraba solo `location`, pero LinkedIn pone "Remote - Latin
    America" en el TÍTULO. Salía False en las 467 ofertas, incluidas las
    regionales de BairesDev y FullStack (33% del corpus). Ahora mira ambos.
  · `maxItems` no se respetaba. Ahora se recorta también del lado del cliente.

Por defecto NO gasta crédito: muestra el plan. Usa --apply para ejecutar.

    python scraper_linkedin.py                    # plan, sin gastar
    python scraper_linkedin.py --apply            # ejecuta
    python scraper_linkedin.py --apply --max-total 200
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime

import psycopg
from apify_client import ApifyClient
from dotenv import load_dotenv

import clean_db

load_dotenv()

APIFY_API_KEY = os.environ.get("APIFY_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
ACTOR = "curious_coder/linkedin-jobs-scraper"
VERSION = "linkedin_apify_v2"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
logger = logging.getLogger("linkedin")

# Orden deliberado: primero español, que es el hueco real del corpus. Las 467
# ofertas actuales salen de búsquedas en inglés y por eso están dominadas por
# consultoras regionales; las empresas peruanas publican en español.
SEARCH_KEYWORDS = [
    # Español — el hueco medido: las 467 ofertas actuales salen de búsquedas en
    # inglés, por eso el corpus está dominado por consultoras regionales
    # (BairesDev 18% + FullStack 15%). Las empresas peruanas publican en español.
    "Analista de Datos",
    "Ingeniero de Datos",
    "Científico de Datos",
    "Inteligencia Artificial",
    "Analista de Inteligencia de Negocios",
    "Ciencia de Datos",
    "Automatización RPA",
    # Inglés — roles de IA que NUNCA se buscaron. Computer Vision aparece hoy en
    # 2.7% de las ofertas y NLP en 8%: no es que Perú no los demande, es que
    # nadie los buscó.
    "AI Engineer",
    "Data Scientist",
    "MLOps Engineer",
    "Prompt Engineer",
    "Computer Vision Engineer",
    "NLP Engineer",
    "AI Product Manager",
    "LLM Engineer",
    "Data Analyst",
]

REMOTO_REGIONAL = re.compile(r"remote|latam|latin america|américa latina", re.I)
ETIQUETA_HTML = re.compile(r"<[^>]+>")

_RX_FUERTE = re.compile(clean_db.REGEX_FUERTE.replace(r"\y", r"\b"), re.I)
_RX_TITULO = re.compile(clean_db.REGEX_TITULO.replace(r"\y", r"\b"), re.I)


# --------------------------------------------------------------------------


def etiquetar(item: dict) -> dict:
    """Marca procedencia. `tipo_remoto` mira título Y ubicación, no solo ubicación."""
    location = item.get("location") or ""
    title = item.get("title") or ""
    item["es_local_peru"] = bool(re.search(r"peru|perú|lima", location, re.I))
    item["tipo_remoto"] = bool(REMOTO_REGIONAL.search(location)
                               or REMOTO_REGIONAL.search(title))
    item["fuente"] = "li"
    return item


def es_util(item: dict) -> tuple[bool, str]:
    if not item.get("id"):
        return False, "sin identificador"
    texto = ETIQUETA_HTML.sub(" ", item.get("descriptionText")
                              or item.get("descriptionHtml") or "")
    if len(texto) < 200:
        return False, "sin descripción"
    if not item.get("es_local_peru"):
        return False, "fuera de Perú"
    if not (_RX_TITULO.search(item.get("title") or "") or _RX_FUERTE.search(texto)):
        return False, "sin señal de IA/datos"
    return True, ""


def ids_existentes() -> set[str]:
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT source_id FROM raw_ofertas WHERE fuente = 'li'")
        return {r[0] for r in cur.fetchall()}


def guardar_respaldo(items: list[dict], keyword: str) -> str:
    """Respalda la data cruda: Apify se paga, no se puede perder por un fallo de BD.

    OJO: data_raw/ es crudo y sin filtrar. Reprocesarlo con uploader.py reinserta
    ofertas que clean_db.py haya purgado.
    """
    os.makedirs("data_raw", exist_ok=True)
    slug = re.sub(r"\W+", "_", keyword)
    ruta = f"data_raw/li_{slug}_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return ruta


def subir(items: list[dict]) -> int:
    nuevas = 0
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        for it in items:
            cur.execute(
                """
                INSERT INTO raw_ofertas (fuente, source_id, payload, scraper_version, scraped_at)
                VALUES (%s, %s, %s::jsonb, %s, NOW())
                ON CONFLICT (fuente, source_id) DO NOTHING
                """,
                ("li", str(it["id"]), json.dumps(it), VERSION),
            )
            nuevas += cur.rowcount
        conn.commit()
    return nuevas


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="ejecuta y GASTA crédito de Apify")
    ap.add_argument("--max-por-keyword", type=int, default=30)
    ap.add_argument("--max-total", type=int, default=350,
                    help="tope global de resultados pedidos a Apify")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    ya = ids_existentes()
    print(f"Ofertas de LinkedIn ya en la base: {len(ya)}")
    print(f"Keywords a buscar: {len(SEARCH_KEYWORDS)}")
    print(f"Tope por keyword : {args.max_por_keyword}")
    print(f"Tope total       : {args.max_total}")
    print(f"Máximo teórico   : {min(args.max_total, len(SEARCH_KEYWORDS) * args.max_por_keyword)} resultados\n")

    for i, kw in enumerate(SEARCH_KEYWORDS, 1):
        idioma = "es" if i <= 7 else "en"
        print(f"  {i:>2}. [{idioma}] {kw}")

    if not args.apply:
        print("\n[plan] No se llamó a Apify ni se gastó crédito. Usa --apply para ejecutar.")
        return

    if not APIFY_API_KEY:
        raise SystemExit("Falta APIFY_API_KEY en el .env")

    cliente = ApifyClient(APIFY_API_KEY)
    acumulado = 0
    utiles_totales: list[dict] = []
    descartes: dict[str, int] = {}
    por_keyword: dict[str, int] = {}

    for kw in SEARCH_KEYWORDS:
        if acumulado >= args.max_total:
            logger.info("Tope total alcanzado (%d); no se buscan más keywords.", args.max_total)
            break

        cupo = min(args.max_por_keyword, args.max_total - acumulado)
        url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location=Peru"
        logger.info("Buscando '%s' (cupo %d)…", kw, cupo)

        try:
            run = cliente.actor(ACTOR).call(run_input={"urls": [url], "maxItems": cupo})
            items = list(cliente.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as exc:  # noqa: BLE001
            logger.error("  '%s' falló: %s — se continúa con la siguiente", kw, exc)
            continue

        # El actor no siempre respeta maxItems: se recorta también aquí.
        items = [etiquetar(it) for it in items[:cupo]]
        acumulado += len(items)
        por_keyword[kw] = len(items)

        if items:
            guardar_respaldo(items, kw)

        nuevas_kw = []
        for it in items:
            ok, motivo = es_util(it)
            if not ok:
                descartes[motivo] = descartes.get(motivo, 0) + 1
            elif str(it["id"]) in ya:
                descartes["ya en la base"] = descartes.get("ya en la base", 0) + 1
            else:
                ya.add(str(it["id"]))
                nuevas_kw.append(it)

        # Se sube keyword por keyword, no al final: si el proceso se corta
        # (laptop cerrada, red caída), lo ya pagado queda guardado en Neon.
        subidas_kw = subir(nuevas_kw) if nuevas_kw else 0
        utiles_totales.extend(nuevas_kw)

        logger.info("  recibidas %d | nuevas y útiles %d | SUBIDAS %d | acumulado %d/%d",
                    len(items), len(nuevas_kw), subidas_kw, acumulado, args.max_total)

    print("\n=== RESUMEN ===")
    for kw, n in por_keyword.items():
        print(f"  {kw:<36} {n:>4} recibidas")
    print()
    for motivo, n in sorted(descartes.items(), key=lambda x: -x[1]):
        print(f"  descartadas ({motivo}): {n}")
    print(f"\n  Resultados pedidos a Apify : {acumulado}")
    print(f"  NUEVAS Y ÚTILES            : {len(utiles_totales)}  (ya subidas por keyword)")

    regionales = sum(1 for it in utiles_totales if it.get("tipo_remoto"))
    if utiles_totales:
        print(f"\n  De las nuevas, {regionales} son remotas regionales "
              f"({100 * regionales / len(utiles_totales):.0f}%) — revisa el sesgo antes de analizar.")


if __name__ == "__main__":
    main()
