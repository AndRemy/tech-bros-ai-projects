"""Elimina de `raw_ofertas` las ofertas sin señal técnica de IA / datos.

Solo aplica a fuentes generalistas (Laborum, Computrabajo…): LinkedIn se scrapea
con búsquedas ya dirigidas, así que se conserva completo.

Por defecto solo muestra lo que haría. Usa --apply para borrar de verdad.

    python clean_db.py                 # previsualiza
    python clean_db.py --apply         # ejecuta el borrado
"""

import argparse
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

FUENTES_GENERALISTAS = ("la", "ct")

# El filtro anterior usaba ILIKE '%IA%', que en español encuentra "IA" dentro de
# auxil-IA-r, comerc-IA-les, industr-IA-l y gerenc-IA: 673 de 751 títulos de
# Laborum sobrevivían solo por eso. Aquí se usa regex con \y (límite de palabra).
#
# Los términos van en dos niveles porque, medido sobre el corpus, las siglas
# cortas solo generan ruido dentro de las descripciones:
#   \ydatos\y -> 37 falsos positivos ("base de datos", "los datos del cliente")
#   \ydata\y  -> 26 falsos positivos (atributos HTML: data-max-lines="5")
#   \yML\y    -> 19 falsos positivos (mililitros y etiquetas HTML)
# En el título, en cambio, esas mismas siglas sí son señal fiable.

# Nivel 1: inequívocos. Se buscan en título y descripción.
TERMINOS_FUERTES = [
    # IA
    r"inteligencia artificial", r"machine learning", r"deep learning",
    r"aprendizaje automático", r"aprendizaje automatico", r"redes neuronales",
    r"\yLLM\y", r"\yNLP\y", r"\yGPT\y", r"\yRAG\y", r"\yMLOps\y",
    r"generative ai", r"ia generativa", r"computer vision",
    r"visión por computador", r"vision por computador",
    r"procesamiento de lenguaje", r"tensorflow", r"pytorch", r"scikit",
    r"langchain", r"hugging face", r"chatbot", r"copilot",
    r"modelos? predictivos?",
    # Datos: siempre en compuesto, nunca "datos" a secas
    r"ciencia de datos", r"data scien", r"data engineer", r"data analyst",
    r"ingenier[oa] de datos", r"analista de datos", r"análisis de datos",
    r"analisis de datos", r"científico de datos", r"cientifico de datos",
    r"arquitect[oa] de datos", r"minería de datos", r"mineria de datos",
    r"big data", r"data warehouse", r"data lake", r"data mining",
    r"business intelligence", r"inteligencia de negocios",
    r"power bi", r"\ytableau\y", r"\yqlik\y", r"\ylooker\y", r"analytics",
    r"analítica de datos", r"analitica de datos",
    # Tecnología
    r"\ySQL\y", r"\yNoSQL\y", r"\yETL\y", r"\yELT\y", r"\ypython\y",
    r"\yPySpark\y", r"\yspark\y", r"\yhadoop\y", r"databricks", r"snowflake",
    r"\yairflow\y", r"\yRPA\y", r"\yUiPath\y", r"blue prism", r"power automate",
    r"automatización robótica", r"automatizacion robotica",
]

# Nivel 2: siglas ambiguas. Solo cuentan si aparecen en el título, donde sí son
# señal fiable ("ANALISTA IA", "AI SPECIALIST", "Analista BI").
#
# 'data' y 'datos' quedan fuera incluso aquí: los cargos reales ya los cubren los
# compuestos del nivel 1 ("analista de datos", "ingeniero de datos", "ciencia de
# datos"), y sueltos solo rescataban puestos de digitación ("validador de datos").
TERMINOS_TITULO = [
    r"\yIA\y", r"\yAI\y", r"\yML\y", r"\yBI\y",
]

REGEX_FUERTE = "|".join(TERMINOS_FUERTES)
REGEX_TITULO = "|".join(TERMINOS_FUERTES + TERMINOS_TITULO)

# El HTML se elimina antes de comparar: si no, los atributos del marcado de
# LinkedIn (data-*, class=…) se cuentan como coincidencias.
def _texto(campo: str) -> str:
    return f"regexp_replace(COALESCE(payload->>'{campo}', ''), '<[^>]+>', ' ', 'g')"


# Se busca también en la descripción: un puesto de marketing que pida Power BI
# también es demanda de habilidades de datos, que es justo lo que mide el estudio.
CONDICION = f"""
    (
        {_texto('title')} ~* %(rx_titulo)s
        OR {_texto('description')} ~* %(rx_fuerte)s
        OR {_texto('descriptionText')} ~* %(rx_fuerte)s
        OR {_texto('requirements')} ~* %(rx_fuerte)s
    )
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="ejecuta el borrado (por defecto solo previsualiza)")
    args = parser.parse_args()

    params = {
        "rx_fuerte": REGEX_FUERTE,
        "rx_titulo": REGEX_TITULO,
        "fuentes": list(FUENTES_GENERALISTAS),
    }

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT fuente, count(*) FROM raw_ofertas GROUP BY fuente ORDER BY fuente")
        print("Antes:", dict(cur.fetchall()))

        cur.execute(
            f"SELECT count(*) FROM raw_ofertas WHERE fuente = ANY(%(fuentes)s) AND NOT {CONDICION}",
            params,
        )
        a_borrar = cur.fetchone()[0]

        cur.execute(
            f"SELECT count(*) FROM raw_ofertas WHERE fuente = ANY(%(fuentes)s) AND {CONDICION}",
            params,
        )
        a_conservar = cur.fetchone()[0]

        print(f"\nEn fuentes generalistas {FUENTES_GENERALISTAS}:")
        print(f"  se conservan: {a_conservar}")
        print(f"  se eliminan : {a_borrar}")

        cur.execute(
            f"""SELECT left(payload->>'title', 62) FROM raw_ofertas
                WHERE fuente = ANY(%(fuentes)s) AND {CONDICION} LIMIT 10""",
            params,
        )
        print("\n  Ejemplos que SE CONSERVAN:")
        for (t,) in cur.fetchall():
            print("   +", t)

        cur.execute(
            f"""SELECT left(payload->>'title', 62) FROM raw_ofertas
                WHERE fuente = ANY(%(fuentes)s) AND NOT {CONDICION} LIMIT 10""",
            params,
        )
        print("\n  Ejemplos que SE ELIMINAN:")
        for (t,) in cur.fetchall():
            print("   -", t)

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para ejecutar.")
            return

        cur.execute(
            f"DELETE FROM raw_ofertas WHERE fuente = ANY(%(fuentes)s) AND NOT {CONDICION}",
            params,
        )
        print(f"\nEliminadas: {cur.rowcount}")
        conn.commit()

        cur.execute("SELECT fuente, count(*) FROM raw_ofertas GROUP BY fuente ORDER BY fuente")
        print("Después:", dict(cur.fetchall()))


if __name__ == "__main__":
    main()
