"""Repara `source_id` y elimina las ofertas duplicadas de `raw_ofertas`.

Arrastre del bug de `uploader.py`: leía `item['id']`, pero Laborum publica su
identificador como `job_id`, así que las 751 filas de Laborum quedaron con
source_id = "None". Como los scrapers deduplican consultando esa columna, nunca
detectaron nada y se acumularon reingestas del mismo aviso.

Hace tres cosas, en orden:
  1. Repuebla `source_id` desde el identificador nativo del payload.
  2. Borra los duplicados por (fuente, source_id), conservando el scrape más reciente.
  3. Crea un índice único (fuente, source_id) para que no vuelva a ocurrir.

Por defecto solo muestra lo que haría. Usa --apply para escribir.

    python dedup_db.py                 # previsualiza
    python dedup_db.py --apply         # ejecuta
"""

import argparse
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Identificador nativo por payload, en orden de preferencia. Debe coincidir con
# CLAVES_ID de uploader.py.
ID_NATIVO = "COALESCE(payload->>'job_id', payload->>'id', payload->>'jobId', payload->>'refId')"

# Conserva el scrape más reciente de cada grupo; desempata por id mayor.
SQL_DUPLICADOS = f"""
    SELECT id FROM (
        SELECT id, row_number() OVER (
            PARTITION BY fuente, {ID_NATIVO}
            ORDER BY scraped_at DESC NULLS LAST, id DESC
        ) AS rn
        FROM raw_ofertas
        WHERE {ID_NATIVO} IS NOT NULL
    ) s WHERE rn > 1
"""


def resumen(cur, etiqueta: str) -> None:
    cur.execute("""
        SELECT fuente, count(*), count(DISTINCT source_id)
        FROM raw_ofertas GROUP BY fuente ORDER BY fuente
    """)
    filas = cur.fetchall()
    print(f"\n{etiqueta}")
    for f, tot, uniq in filas:
        print(f"  {f}: {tot} filas | {uniq} source_id distintos")
    print(f"  TOTAL: {sum(r[1] for r in filas)} filas")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="ejecuta los cambios (por defecto solo previsualiza)")
    args = parser.parse_args()

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        resumen(cur, "=== ANTES ===")

        # Salvaguarda: no borrar trabajo ya procesado ni romper claves foráneas.
        cur.execute(f"SELECT count(*) FROM raw_ofertas WHERE id IN ({SQL_DUPLICADOS}) AND procesado")
        procesados = cur.fetchone()[0]
        cur.execute(f"SELECT count(*) FROM jobs WHERE raw_id IN ({SQL_DUPLICADOS})")
        jobs_dep = cur.fetchone()[0]
        cur.execute(f"SELECT count(*) FROM puestos WHERE raw_id IN ({SQL_DUPLICADOS})")
        puestos_dep = cur.fetchone()[0]

        cur.execute(f"SELECT count(*) FROM ({SQL_DUPLICADOS}) s")
        n_dup = cur.fetchone()[0]
        cur.execute(f"SELECT count(*) FROM raw_ofertas WHERE {ID_NATIVO} IS NULL")
        n_sin_id = cur.fetchone()[0]

        print("\n=== PLAN ===")
        print(f"  duplicados a eliminar : {n_dup}")
        print(f"  filas sin id nativo   : {n_sin_id} (se conservan intactas)")
        print(f"  de esos, ya procesados: {procesados}")
        print(f"  dependencias en jobs  : {jobs_dep}")
        print(f"  dependencias en puestos: {puestos_dep}")

        if procesados or jobs_dep or puestos_dep:
            raise SystemExit(
                "\nABORTADO: hay filas duplicadas ya procesadas o con dependencias. "
                "Revísalas a mano antes de deduplicar."
            )

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para ejecutar.")
            return

        print("\n=== APLICANDO ===")

        cur.execute(f"UPDATE raw_ofertas SET source_id = {ID_NATIVO} WHERE {ID_NATIVO} IS NOT NULL")
        print(f"  1. source_id repoblado en {cur.rowcount} filas")

        cur.execute(f"DELETE FROM raw_ofertas WHERE id IN ({SQL_DUPLICADOS})")
        print(f"  2. duplicados eliminados: {cur.rowcount}")

        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS raw_ofertas_fuente_source_id_key
            ON raw_ofertas (fuente, source_id)
        """)
        print("  3. índice único (fuente, source_id) creado")

        conn.commit()
        resumen(cur, "=== DESPUÉS ===")


if __name__ == "__main__":
    main()
