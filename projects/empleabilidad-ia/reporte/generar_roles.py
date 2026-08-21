"""Genera `roles.html`: el reporte interactivo de categorías funcionales de roles de IA.

Complementa a `generar_reporte.py` (que produce `index.html`, la vista general del
mercado). Este toma como eje **el rol**: qué significa trabajar en IA, qué habilidades
pide cada tipo de trabajo y qué hace cada sector con la IA.

Se apoya en `analisis/categorias_funcionales.py` para la clasificación multi-etiqueta.

    python reporte/generar_roles.py
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import psycopg
from dotenv import load_dotenv

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "analisis"))
from categorias_funcionales import (  # noqa: E402
    CATEGORIAS, cargar_y_clasificar,
)

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
DATOS_DIR = RAIZ / "datos"
PLANTILLA = AQUI / "plantilla_roles.html"
SALIDA = AQUI / "roles.html"

# --- descripciones de cada categoría -------------------------------------
# El texto explicativo es redacción propia; las frases de `ejemplos` son citas
# textuales de avisos del corpus, elegidas por representatividad.
DEFINICIONES = {
    "Construir IA": {
        "resumen": "Crear el sistema de IA: diseñar, desarrollar y entrenar modelos, agentes y aplicaciones que antes no existían.",
        "detalle": "Es la categoría más grande y también la más amplia: abarca desde entrenar un modelo de machine learning hasta armar una aplicación sobre un LLM. Casi todo lo demás cuelga de ella.",
        "ejemplos": [
            "Diseñar e implementar servidores de Model Context Protocol (MCP) para extender las capacidades de modelos de lenguaje grandes.",
            "Diseñar, desarrollar e implementar soluciones basadas en IA generativa sobre AWS, integrando modelos LLM.",
            "Desarrolla modelos predictivos para iniciativas estratégicas de RR.HH.",
        ],
    },
    "Operar IA en producción": {
        "resumen": "Llevar la IA a producción y mantenerla viva: desplegar, escalar, monitorear. El territorio de MLOps.",
        "detalle": "Es lo que separa un piloto de un sistema real. Aparece en la mitad de los avisos, y es la categoría que más claramente distingue al perfil senior del junior.",
        "ejemplos": [
            "Diseñar y operar pipelines de datos en producción, construir arquitecturas lakehouse sobre AWS y Databricks.",
            "Al menos 2 años de experiencia en el desarrollo y/o despliegue de modelos de machine learning.",
            "Responsable del desarrollo, implementación y mantenimiento de soluciones de IA conversacional end-to-end.",
        ],
    },
    "IA para automatizar procesos": {
        "resumen": "Usar IA para que un proceso del negocio ocurra solo: flujos, orquestación, RPA con capa inteligente.",
        "detalle": "No busca construir un modelo nuevo, sino conectar piezas para eliminar trabajo manual. Su stack lo delata: RPA, Power Automate, Zapier, n8n, Make.",
        "ejemplos": [
            "Automatizar procesos mediante herramientas tecnológicas e inteligencia artificial, crear dashboards y presentar hallazgos a gerencia.",
            "Liderar la estrategia y adopción de IA, IA generativa, automatización, RPA y robótica para optimizar los servicios tecnológicos.",
            "Usar herramientas de IA para automatizar validaciones de datos.",
        ],
    },
    "IA para analizar y decidir": {
        "resumen": "Usar IA para entender qué pasa y qué va a pasar: predicción, forecasting, segmentación, insights.",
        "detalle": "Es la puerta de entrada más común desde el mundo del análisis de datos tradicional. Su stack pesa hacia estadística y modelos predictivos más que hacia infraestructura.",
        "ejemplos": [
            "Diseña e implementa soluciones analíticas y modelos predictivos para optimizar procesos y generar valor de negocio.",
            "Provee a los líderes de marketing insights y recomendaciones, construyendo modelos, pronósticos y reportes.",
            "Crear analítica descriptiva, modelos predictivos, estadísticas descriptivas y gráficos.",
        ],
    },
    "Liderar/gobernar IA": {
        "resumen": "Decidir qué IA se hace y bajo qué reglas: estrategia, estándares, roadmap, ética y gobierno.",
        "detalle": "Casi nunca es un rol puramente directivo: 88% de quienes lideran también construyen. En Perú todavía no existe el gerente de IA que sólo gestiona.",
        "ejemplos": [
            "Lidera y diseña las iniciativas de inteligencia artificial y analítica avanzada del corporativo, asesorando a ejecutivos en estrategias, casos de uso y roadmaps.",
            "Participar en la definición de estándares, mejores prácticas y lineamientos para el desarrollo de soluciones de IA Generativa.",
            "Gobernar e implementar IA en todas las iniciativas de la organización, definiendo casos, reglas, controles y evidencia.",
        ],
    },
    "IA para programar": {
        "resumen": "Escribir software con asistentes de IA: Copilot, Cursor, Claude Code como parte del flujo diario.",
        "detalle": "La categoría más pequeña y la más sorprendente: sólo 1 de cada 14 avisos de IA lo pide explícitamente. No se puede saber si el mercado aún no lo exige o si ya lo da por sentado.",
        "ejemplos": [
            "Buscamos una mentalidad AI-native: que uses herramientas avanzadas de generación y asistencia de código (Claude Code, opencode, Cursor o similares) como parte habitual de tu flujo de trabajo.",
            "Apply critical judgment to AI-generated code and agentic attestations before merge.",
            "Experiencia utilizando GitHub Copilot o Microsoft Copilot.",
        ],
    },
    "Usar herramientas de IA": {
        "resumen": "Manejar IA generativa como herramienta de trabajo, sin construirla ni operarla.",
        "detalle": "Es marginal como puesto en sí (3%). Aparece casi siempre como requisito secundario dentro de otro rol, no como el trabajo principal.",
        "ejemplos": [
            "Uso de herramientas de IA como ChatGPT, Claude, entre otros.",
            "Manejo de IA generativa (ChatGPT, Gemini, Claude, etc.).",
            "Familiaridad con el uso de inteligencia artificial generativa para potenciar la productividad.",
        ],
    },
}

LIMA_HITS = ["lima", "san isidro", "miraflores", "surco", "la molina", "callao", "la victoria",
             "san borja", "magdalena", "san miguel", "jesus maria", "jesús maría", "barranco",
             "chorrillos", "san juan de lurigancho", "los olivos", "independencia", "comas",
             "ate", "santa anita", "lima metropolitan", "pueblo libre", "lince", "surquillo", "breña"]

INDUSTRIA_REGLAS = [
    (r"it services|software|information services|tecnolog|computer and network|outsourcing|offshoring", "Tecnología"),
    (r"consultor|business consulting", "Consultoría"),
    (r"^banca|banking|banca y", "Banca"),
    (r"financial services|servicios financieros", "Servicios Financieros"),
    (r"seguros|insurance", "Seguros"),
    (r"telecomunicaciones|telecommunication|satelit", "Telecomunicaciones"),
    (r"salud|health", "Salud"),
    (r"retail|venta al consumidor|consumo|comercio", "Retail / Consumo"),
    (r"aliment|bebida|food|beverage|agroexport|agricultura|pesca|ganader", "Alimentos / Agro"),
    (r"manufactur|fabricacion|machinery|packaging|glass|ceramics|concrete|plastico|textil|quimica|defense", "Manufactura"),
    (r"logistic|transport|supply chain|storage|almacen", "Logística / Transporte"),
    (r"mineria|mining|oil and gas|petroleo|gas|energia|energy|utilities|electrica|renovable", "Minería / Energía"),
    (r"educacion|education|e-learning|research services", "Educación"),
    (r"publicidad|advertising|marketing|medios|rrpp", "Publicidad / Medios"),
    (r"construccion|ingenieria civil|real estate|obras|infraestructura|facilities", "Construcción / Inmobiliario"),
    (r"recursos humanos|staffing|human resources", "Recursos Humanos"),
    (r"farmac", "Farmacéutico"),
    (r"entretenimiento|hoteler", "Entretenimiento / Hotelería"),
    (r"servicios profesionales|servicios legales|legal", "Servicios Profesionales"),
]


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn").lower()


def region_de(ciudad):
    if not ciudad or not ciudad.strip() or ciudad.strip().lower() == "no especificado":
        return "No especificado"
    c = ciudad.lower()
    if any(h in c for h in LIMA_HITS):
        return "Lima"
    if c.strip() in ("perú", "peru"):
        return "No especificado"
    return "Provincia"


def industria_de(rubro):
    """Normaliza los 94 valores crudos de `rubro_inferido` a ~20 industrias."""
    if not rubro or not rubro.strip():
        return "No especificado"
    base = re.sub(r"\s+", " ", sin_tildes(rubro)).strip()
    for patron, canon in INDUSTRIA_REGLAS:
        if re.search(patron, base):
            return canon
    return "Otros"


def main() -> None:
    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        clasificado = cargar_y_clasificar(cur)

        cur.execute("""SELECT raw_id, nivel_puesto, rubro_inferido, ciudad,
                              nombre_puesto_estandarizado, nombre_empresa
                       FROM puestos""")
        puestos = {str(r[0]): {"nivel": r[1], "rubro": r[2], "ciudad": r[3],
                               "puesto": r[4], "empresa": r[5]} for r in cur.fetchall()}

        habilidades = defaultdict(list)
        cur.execute("""SELECT js.job_id, sd.canonical_skill FROM job_skills js
                       JOIN skill_dictionary sd USING (skill_id)""")
        for job_id, skill in cur.fetchall():
            habilidades[job_id].append(skill)

        carreras = defaultdict(list)
        cur.execute("""SELECT p.raw_id, e.carrera_especialidad FROM estudios e
                       JOIN puestos p ON p.id = e.puesto_id
                       WHERE e.carrera_especialidad IS NOT NULL AND e.carrera_especialidad <> ''""")
        for raw_id, carrera in cur.fetchall():
            carreras[str(raw_id)].append(carrera)

    registros = []
    for job_id, info in clasificado.items():
        if not info["tiene_ia"]:
            continue                       # el reporte trata sobre roles de IA
        p = puestos.get(job_id)
        if not p:
            continue
        registros.append({
            "cats": sorted(info["cats"].keys()),
            "titulo": info["title"],
            "puesto": p["puesto"],
            "empresa": p["empresa"],
            "industria": industria_de(p["rubro"]),
            "region": region_de(p["ciudad"]),
            "seniority": p["nivel"] or "No especificado",
            "skills": sorted(set(habilidades.get(job_id, []))),
            "carreras": sorted(set(carreras.get(job_id, []))),
        })

    # títulos de puesto típicos por categoría, para hacer tangible cada definición
    titulos_por_cat = {}
    for c in CATEGORIAS:
        cuenta = Counter(r["puesto"] for r in registros if c in r["cats"] and r["puesto"])
        titulos_por_cat[c] = [t for t, _ in cuenta.most_common(6)]

    payload = {
        "registros": registros,
        "categorias": CATEGORIAS,
        "definiciones": DEFINICIONES,
        "titulos_por_categoria": titulos_por_cat,
        "total_corpus": len(clasificado),
        "total_con_ia": len(registros),
    }

    DATOS_DIR.mkdir(exist_ok=True)
    data_json = json.dumps(payload, ensure_ascii=False)
    (DATOS_DIR / "roles.json").write_text(data_json, encoding="utf-8")
    print(f"export intermedio: {DATOS_DIR/'roles.json'} ({len(registros)} avisos con IA)")

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if "__DATA_JSON__" not in plantilla:
        raise SystemExit(f"{PLANTILLA} no tiene el marcador __DATA_JSON__")
    SALIDA.write_text(plantilla.replace("__DATA_JSON__", data_json), encoding="utf-8")
    print(f"reporte generado : {SALIDA} ({SALIDA.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
