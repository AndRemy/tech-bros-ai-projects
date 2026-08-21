"""Clasifica cada aviso por lo que HACE con la IA (categoría funcional, multi-etiqueta).

Es un eje distinto al de `clasificar_ofertas.py`: aquel decide *si* el puesto es de IA
(`puestos.tipo_oferta`); este decide *qué hace* con ella. Un mismo aviso puede construir
modelos Y operarlos en producción, así que la clasificación es multi-etiqueta.

Cómo se derivaron las categorías
--------------------------------
No son a priori: salieron de extraer los verbos que aparecen cerca de menciones de IA en
las 544 descripciones. Los dominantes fueron diseñar (79), desarrollar (66), implementar
(62), construir (48), automatización (41), optimizar (35).

Regla de asignación
-------------------
El verbo y el objeto de IA deben coexistir en la MISMA frase. Se segmenta título,
descripción y cada `job_skills.evidence` por puntuación. Una primera versión buscaba
proximidad por caracteres sobre el texto concatenado y sobre-etiquetaba (3-5 categorías
por aviso): unir todas las evidencias creaba vecindad artificial entre un verbo y una
mención de IA que no estaban relacionados.

Dos trampas del español que este módulo evita
---------------------------------------------
1. **Subcadenas sin límite de palabra.** El patrón `(ide|ides)` para detectar "IDE con IA"
   matcheaba *ident*ificar, l*íde*r y cons*ide*rando: 119 falsos positivos que inflaban
   "IA para programar" de 22 a 54 avisos (2.5x). Es el mismo bug que `docs/DECISIONES.md`
   §2 documenta para `ILIKE '%IA%'`. Todos los patrones usan `\b`.
2. **"productividad" no es "producción".** `productiv` marcaba como "Operar IA en
   producción" a un Asistente Comercial al que le pedían ChatGPT "para potenciar la
   productividad".

Validación
----------
Las reglas leen la descripción; las habilidades vienen de una extracción independiente
(`job_skills`). Que coincidan es evidencia de que la categoría captura algo real:

    IA para automatizar  -> RPA x3.1, Zapier x3.1, Power Automate x2.7
    Operar en producción -> MLOps x2.0, Airflow x2.0, MLflow x2.0
    Analizar y decidir   -> Modelos predictivos x2.4, Análisis Exploratorio x2.6
    IA para programar    -> Cursor x17.1, Claude x6.8

Precisión estimada ~75% sobre una muestra de 20 asignaciones revisadas a mano. Sirve para
leer estructura, no para citar porcentajes al decimal. "Construir IA" es la categoría más
laxa y probablemente la más inflada.

    python analisis/categorias_funcionales.py          # resumen por consola
"""

import os
import re
import unicodedata
from collections import Counter, defaultdict

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

CATEGORIAS = [
    "Construir IA",
    "Operar IA en producción",
    "IA para automatizar procesos",
    "IA para analizar y decidir",
    "Liderar/gobernar IA",
    "IA para programar",
    "Usar herramientas de IA",
]

IA_ESTRICTA = {"Generative AI", "AI Agents", "Machine Learning", "Deep Learning",
               "NLP", "Computer Vision", "MLOps"}

# Objeto de IA inequívoco: basta que aparezca para que la frase "hable de IA".
IA_OBJ = re.compile(
    r"\b(ia|ai)\b|inteligencia artificial|machine learning|\bml\b|deep learning|\bllm[s]?\b|"
    r"modelo[s]? de lenguaje|gen ?ai|generativ[ao]|\brag\b|agente[s]? (?:de ia|ai|autonomo|conversacional)|"
    r"red(?:es)? neuronal|\bnlp\b|vision por computador|computer vision|embedding[s]?|transformer|"
    r"chatgpt|claude|gemini|copilot|modelo[s]? predictiv|aprendizaje automatico")

# Objeto ambiguo: sólo cuenta si el aviso YA tiene dominio de IA confirmado por skills.
# Sin ese respaldo, "modelo" sería un modelo de datos y no de machine learning.
IA_OBJ_CTX = re.compile(
    r"\bmodelo[s]?\b|algoritmo[s]?|sistema[s]? autonomo|arquitectura cognitiva|entrenamiento|"
    r"inferencia|feature[s]? engineering|proyeccion(?:es)?|scoring")

V_CONSTRUIR = re.compile(
    r"\b(desarroll|construir|constru|crear|crea\b|disen|implementa|entrenar|entrena|"
    r"modelar|prototip|fine.?tun|elaborar)")
# "produccion|productivo" sí; "productividad" no.
V_OPERAR = re.compile(
    r"\b(desplegar|despliegue|deploy|en produccion|produccion\b|productivo|productiva\b|"
    r"escalar|escalab|monitorear|monitoreo|mantener|mantenimiento|operacionaliza|"
    r"mlops|observabilidad|ciclo de vida|optimizacion de entrenamiento)")
V_AUTOMATIZAR = re.compile(
    r"\b(automatiza|automatizar|automatico|automatizacion|\brpa\b|orquesta|"
    r"flujo[s]? de trabajo|workflow)")
V_ANALIZAR = re.compile(
    r"\b(analiz|analisis|insight|reporte|reporteria|dashboard|forecast|pronostic|"
    r"prediccion|predictiv|segmenta|recomendacion|proyeccion)")
V_LIDERAR = re.compile(
    r"\b(liderar|lidera\b|liderazgo|estrategia|gobierno|governance|estandare|"
    r"lineamiento|roadmap|dirigir|mejores practicas|definir la vision|etica)")

# Asistencia de IA al desarrollo de software. Todos los tokens con \b: sin eso,
# "ide" matchea "identificar" (ver docstring).
P_PROGRAMAR = re.compile(
    r"\b(github copilot|cursor|codeium|tabnine|claude code|codex)\b|"
    r"\bide[s]?\b[^.]{0,40}\b(ia|ai)\b|"
    r"\b(ia|ai)\b[^.]{0,50}(escritura de codigo|generacion de codigo|escribir codigo|"
    r"refactoriza|autocompletad|generated code)|"
    r"herramientas de \b(ia|ai)\b[^.]{0,60}(codigo|desarrollo de software|test|refactor)|"
    r"\b(ai|ia).?native\b|\b(ai|ia).?assisted (coding|development)\b|agentic (coding|development)|"
    r"(asistid|impulsad|potenciad|acelerad)[oa] por \b(ia|ai)\b[^.]{0,40}(desarroll|codigo|programa)")
# Plataformas para CONSTRUIR agentes, no asistentes de código.
P_PROGRAMAR_NO = re.compile(r"copilot studio|ai foundry|power platform")

P_HERRAMIENTA = re.compile(
    r"\b(chatgpt|claude|gemini|microsoft copilot|perplexity|midjourney|prompt engineering|"
    r"ingenieria de prompt)\b|herramientas de \b(ia|ai)\b")

# (categoría, patrón, ¿el título puede fundarla?)
# "Operar en producción" no se funda en el título: "Forward Deployed AI Scientist" es un
# nombre de rol, no una función.
REGLAS = [
    ("Construir IA", V_CONSTRUIR, True),
    ("Operar IA en producción", V_OPERAR, False),
    ("IA para automatizar procesos", V_AUTOMATIZAR, True),
    ("IA para analizar y decidir", V_ANALIZAR, True),
    ("Liderar/gobernar IA", V_LIDERAR, True),
]


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn").lower()


def limpiar_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def segmentar(titulo: str, descripcion: str, evidencias: list[str]) -> list[tuple[str, bool]]:
    """Devuelve [(frase_normalizada, es_titulo)]."""
    segs = [(sin_tildes(titulo), True)]
    partes = re.split(r"(?<=[.;:!?])\s+|\s+[•\-–]\s+", limpiar_html(descripcion))
    segs += [(sin_tildes(p), False) for p in partes if len(p.strip()) > 12]
    segs += [(sin_tildes(e), False) for e in evidencias if len(e.strip()) > 12]
    return [(f, t) for f, t in segs if f]


def clasificar(titulo, descripcion, evidencias, dominios):
    """Devuelve {categoria: [frases que la sustentan]}. Multi-etiqueta."""
    segs = segmentar(titulo, descripcion, evidencias)
    tiene_ia = bool(set(dominios) & IA_ESTRICTA)
    cats = defaultdict(list)

    for frase, es_titulo in segs:
        habla_de_ia = bool(IA_OBJ.search(frase)) or (tiene_ia and bool(IA_OBJ_CTX.search(frase)))
        if not habla_de_ia:
            continue
        for nombre, patron, usa_titulo in REGLAS:
            if es_titulo and not usa_titulo:
                continue
            if patron.search(frase):
                cats[nombre].append(frase)

    if "MLOps" in dominios:
        cats["Operar IA en producción"].append("[skill: MLOps]")

    for frase, _ in segs:
        if P_PROGRAMAR.search(frase) and not P_PROGRAMAR_NO.search(frase):
            cats["IA para programar"].append(frase)

    # Sólo "usa" IA si no la construye ni la opera.
    if not ({"Construir IA", "Operar IA en producción"} & set(cats)):
        for frase, _ in segs:
            if P_HERRAMIENTA.search(frase):
                cats["Usar herramientas de IA"].append(frase)
                break

    return dict(cats)


def cargar_y_clasificar(cur):
    """Clasifica todo el corpus. Devuelve {job_id: {'cats':…, 'tiene_ia': bool}}."""
    cur.execute("SELECT job_id, title, description FROM jobs")
    jobs = {r[0]: {"title": r[1], "description": r[2]} for r in cur.fetchall()}

    evidencias = defaultdict(list)
    cur.execute("SELECT job_id, evidence FROM job_skills WHERE evidence IS NOT NULL AND evidence <> ''")
    for job_id, ev in cur.fetchall():
        evidencias[job_id].append(ev)

    dominios = defaultdict(set)
    cur.execute("""SELECT js.job_id, sd.ai_domain FROM job_skills js
                   JOIN skill_dictionary sd USING (skill_id)""")
    for job_id, dom in cur.fetchall():
        dominios[job_id].add(dom)

    salida = {}
    for job_id, j in jobs.items():
        doms = dominios.get(job_id, set())
        salida[job_id] = {
            "cats": clasificar(j["title"], j["description"], evidencias.get(job_id, []), doms),
            "tiene_ia": bool(doms & IA_ESTRICTA),
            "title": j["title"],
        }
    return salida


def main() -> None:
    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        res = cargar_y_clasificar(cur)

    con_ia = [v for v in res.values() if v["tiene_ia"]]
    sin_cat = [v for v in con_ia if not v["cats"]]
    print(f"corpus            : {len(res)}")
    print(f"con IA estricta   : {len(con_ia)}")
    print(f"clasificados      : {len(con_ia)-len(sin_cat)} ({100*(len(con_ia)-len(sin_cat))/len(con_ia):.1f}%)")
    print(f"categorías/aviso  : {dict(sorted(Counter(len(v['cats']) for v in con_ia).items()))}")

    cuenta = Counter()
    for v in con_ia:
        for c in v["cats"]:
            cuenta[c] += 1
    print(f"\n=== frecuencia (n={len(con_ia)}) ===")
    for c, n in cuenta.most_common():
        print(f"  {n:>4}  {100*n/len(con_ia):>5.1f}%  {c}")


if __name__ == "__main__":
    main()
