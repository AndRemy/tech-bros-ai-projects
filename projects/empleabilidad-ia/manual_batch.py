"""Procesamiento asistido: la extracción la hace Claude Code en sesión, no la API.

Alternativa sin costo de API a `processor.py`. Reutiliza su esquema Pydantic y su
función `guardar()`, así que las filas quedan idénticas por cualquiera de los dos
caminos.

    python manual_batch.py --fetch 25            # saca el siguiente lote a extraer
    python manual_batch.py --write lote.json     # valida y escribe a la base
    python manual_batch.py --status              # avance

Formato de `lote.json`: {"<raw_id>": {job:{...}, skills:[...], studies:[...]}, ...}
"""

import argparse
import json
import os
import re

import psycopg
from dotenv import load_dotenv

from processor import OfertaEstructurada, armar_texto_oferta, guardar

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Núcleo del estudio: ofertas con señal explícita de IA.
IA = re.compile(
    r"inteligencia artificial|machine learning|deep learning|\bllm\b|\bgpt\b|"
    r"generative ai|ia generativa|\brag\b|\bnlp\b|computer vision|redes neuronales|"
    r"tensorflow|pytorch|scikit|langchain|\bmlops\b|\bai\b|agentic|copilot",
    re.I,
)


def _texto_crudo(p: dict) -> str:
    partes = [p.get("title") or ""]
    for k in ("description", "descriptionText", "requirements", "competencies"):
        v = p.get(k)
        if isinstance(v, str):
            partes.append(v)
        elif isinstance(v, list):
            partes.append(" ".join(map(str, v)))
    return re.sub(r"<[^>]+>", " ", " ".join(partes))


def pendientes(solo_ia: bool = True) -> list[tuple[int, dict]]:
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, payload FROM raw_ofertas WHERE procesado = FALSE ORDER BY id")
        filas = cur.fetchall()
    if not solo_ia:
        return filas
    return [(i, p) for i, p in filas if IA.search(_texto_crudo(p))]


# Compatibilidad con el nombre anterior.
def pendientes_ia() -> list[tuple[int, dict]]:
    return pendientes(solo_ia=True)


def cmd_fetch(n: int, solo_ia: bool = True) -> None:
    lote = pendientes(solo_ia)[:n]
    if not lote:
        print("No quedan ofertas de IA pendientes.")
        return
    print(f"### LOTE: {len(lote)} ofertas ###\n")
    for raw_id, payload in lote:
        print(f"===== RAW_ID {raw_id} =====")
        print(armar_texto_oferta(payload))
        print()


def cmd_write(ruta: str) -> None:
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)

    ok, errores = 0, []
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, payload FROM raw_ofertas WHERE id = ANY(%s)",
                        ([int(k) for k in datos],))
            payloads = dict(cur.fetchall())

        for clave, bruto in datos.items():
            raw_id = int(clave)
            if raw_id not in payloads:
                errores.append((raw_id, "no existe en raw_ofertas"))
                continue
            try:
                validado = OfertaEstructurada.model_validate(bruto)
                guardar(conn, raw_id, payloads[raw_id], validado)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                errores.append((raw_id, f"{type(exc).__name__}: {exc}"))

    print(f"Escritas: {ok} | fallidas: {len(errores)}")
    for raw_id, err in errores:
        print(f"  id={raw_id}: {err[:130]}")


def cmd_status() -> None:
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw_ofertas WHERE procesado")
        proc = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM raw_ofertas")
        tot = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM jobs")
        jobs = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM job_skills")
        js = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM skill_dictionary")
        sd = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM estudios")
        est = cur.fetchone()[0]
    ia_pend = len(pendientes_ia())
    print(f"raw_ofertas procesadas : {proc}/{tot}")
    print(f"ofertas IA pendientes  : {ia_pend}")
    print(f"jobs                   : {jobs}")
    print(f"job_skills             : {js}")
    print(f"skill_dictionary       : {sd}")
    print(f"estudios               : {est}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", type=int, metavar="N")
    ap.add_argument("--todas", action="store_true",
                    help="incluye pendientes sin señal explícita de IA (datos/BI)")
    ap.add_argument("--write", metavar="ARCHIVO.json")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    if a.fetch:
        cmd_fetch(a.fetch, solo_ia=not a.todas)
    elif a.write:
        cmd_write(a.write)
    else:
        cmd_status()
