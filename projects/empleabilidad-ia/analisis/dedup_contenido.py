"""Elimina avisos repetidos: mismo título y empresa con distinto `source_id`.

`dedup_db.py` deduplica por identificador del portal, pero LinkedIn publica el
mismo puesto con IDs distintos: FullStack repite sus 6 avisos entre 11 y 12 veces
cada uno, 65 filas sobrantes de una sola empresa. Eso sesga las cifras del estudio
hacia el perfil de quien más republica (los avisos duplicados son roles DevOps en
inglés, e inflaban `Inglés` +5 pts y `CI/CD` +6 pts).

Borra en cascada porque hay claves foráneas:
    job_skills → jobs → raw_ofertas    y    estudios → puestos → raw_ofertas

Por defecto solo muestra lo que haría. Usa --apply para borrar.

    python dedup_contenido.py
    python dedup_contenido.py --apply
"""

import argparse
import collections
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Se conserva la fila ya procesada (para no tirar el trabajo de extracción);
# entre varias procesadas o ninguna, gana el scrape más reciente.
SQL_FILAS = """
    SELECT id,
           fuente,
           lower(trim(COALESCE(payload->>'title', ''))),
           lower(trim(COALESCE(payload->>'company', payload->>'companyName', ''))),
           procesado,
           scraped_at
    FROM raw_ofertas
"""


def elegir_sobreviviente(filas: list) -> tuple:
    return sorted(filas, key=lambda f: (not f[4], -(f[5].timestamp() if f[5] else 0), f[0]))[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(SQL_FILAS)
        filas = cur.fetchall()

        grupos = collections.defaultdict(list)
        for f in filas:
            titulo, empresa = f[2], f[3]
            if not titulo:  # sin título no hay forma fiable de agrupar
                continue
            grupos[(f[1], titulo, empresa)].append(f)

        a_borrar, por_empresa = [], collections.Counter()
        for (fuente, titulo, empresa), miembros in grupos.items():
            if len(miembros) < 2:
                continue
            queda = elegir_sobreviviente(miembros)
            for m in miembros:
                if m[0] != queda[0]:
                    a_borrar.append(m[0])
                    por_empresa[empresa or "(sin empresa)"] += 1

        print(f"filas en raw_ofertas   : {len(filas)}")
        print(f"grupos título+empresa  : {len(grupos)}")
        print(f"filas a eliminar       : {len(a_borrar)}")
        print(f"corpus resultante      : {len(filas) - len(a_borrar)}")

        if not a_borrar:
            print("\nNo hay duplicados de contenido.")
            return

        print("\n=== filas sobrantes por empresa ===")
        for e, n in por_empresa.most_common(10):
            print(f"  {n:>4}  {e[:44]}")

        cur.execute("SELECT count(*) FROM raw_ofertas WHERE id = ANY(%s) AND procesado",
                    (a_borrar,))
        print(f"\n  de las eliminadas, ya procesadas: {cur.fetchone()[0]} "
              "(su extracción se descarta; el aviso sobrevive en otra fila)")

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para borrar.")
            return

        job_ids = [str(i) for i in a_borrar]

        cur.execute("DELETE FROM job_skills WHERE job_id = ANY(%s)", (job_ids,))
        print(f"\n  job_skills eliminadas : {cur.rowcount}")

        cur.execute("DELETE FROM jobs WHERE raw_id = ANY(%s)", (a_borrar,))
        print(f"  jobs eliminados       : {cur.rowcount}")

        cur.execute(
            "DELETE FROM estudios WHERE puesto_id IN "
            "(SELECT id FROM puestos WHERE raw_id = ANY(%s))", (a_borrar,))
        print(f"  estudios eliminados   : {cur.rowcount}")

        cur.execute("DELETE FROM puestos WHERE raw_id = ANY(%s)", (a_borrar,))
        print(f"  puestos eliminados    : {cur.rowcount}")

        cur.execute("DELETE FROM raw_ofertas WHERE id = ANY(%s)", (a_borrar,))
        print(f"  raw_ofertas eliminadas: {cur.rowcount}")

        # Habilidades que quedaron sin ninguna oferta que las respalde.
        cur.execute("""
            DELETE FROM skill_dictionary sd
            WHERE NOT EXISTS (SELECT 1 FROM job_skills js WHERE js.skill_id = sd.skill_id)
        """)
        print(f"  skills huérfanas      : {cur.rowcount}")

        conn.commit()

        cur.execute("SELECT count(*) FROM raw_ofertas")
        print(f"\nraw_ofertas : {cur.fetchone()[0]}")
        cur.execute("SELECT count(*) FROM jobs")
        print(f"jobs        : {cur.fetchone()[0]}")
        cur.execute("SELECT count(*) FROM skill_dictionary")
        print(f"skills      : {cur.fetchone()[0]}")


if __name__ == "__main__":
    main()
