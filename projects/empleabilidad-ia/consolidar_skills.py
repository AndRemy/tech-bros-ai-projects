"""Consolida `skill_dictionary`: fusiona variantes y resuelve dominios contradictorios.

El extractor canoniza bien lo grueso, pero deja tres fugas que sí tuercen las
cifras del estudio:
  1. Idioma: "Inglés"(154) y "English"(61) son la misma habilidad contada aparte.
  2. Mayúsculas y puntuación: Git/GIT, GitHub/Github, CI/CD vs CI-CD.
  3. Calificadores de nivel: "SQL Avanzado" cuenta separado de "SQL".
Y 32 habilidades tienen `ai_domain` contradictorio entre ofertas (Power BI aparece
como 'Analytics' y como 'No aplica'), lo que rompe cualquier agrupación por dominio.

Es re-ejecutable: córrelo después de cada tanda de `processor.py`.

    python consolidar_skills.py            # previsualiza
    python consolidar_skills.py --apply    # consolida
"""

import argparse
import collections
import os
import re
import unicodedata

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Pares español/inglés de la misma habilidad. Se canoniza al español porque el
# estudio se publica en español; los términos técnicos se dejan en su forma usual
# (nadie escribe "aprendizaje automático" en una oferta peruana).
SINONIMOS = {
    "english": "Inglés",
    "spanish": "Español",
    "portuguese": "Portugués",
    "problem solving": "Resolución de problemas",
    "problemsolving": "Resolución de problemas",
    "teamwork": "Trabajo en equipo",
    "team work": "Trabajo en equipo",
    "communication": "Comunicación",
    "communication skills": "Comunicación",
    "leadership": "Liderazgo",
    "critical thinking": "Pensamiento crítico",
    "time management": "Gestión del tiempo",
    "data analysis": "Análisis de datos",
    "data analytics": "Análisis de datos",
    "project management": "Gestión de proyectos",
    "adaptability": "Adaptabilidad",
    "collaboration": "Colaboración",
    "attention to detail": "Atención al detalle",
}

# Calificadores de nivel: no distinguen la habilidad, solo su profundidad.
NIVELES = re.compile(
    r"\b(avanzado|avanzada|intermedio|intermedia|b[áa]sico|b[áa]sica|"
    r"advanced|intermediate|basic|nivel|deseable|s[óo]lido|fuerte|"
    r"conocimiento(s)?\s+(de|en)|manejo\s+(de|en)|dominio\s+(de|en)|experiencia\s+(en|con))\b",
    re.I,
)

# Habilidades demasiado cortas para normalizar sin riesgo de fusionar distintas.
MIN_LONGITUD = 3

# `puestos.rubro_inferido` sufre la misma fragmentación español/inglés que las
# habilidades: "Tecnología"(163) e "IT Services and IT Consulting"(111) son el
# mismo rubro y, separados, subestiman la concentración del sector.
RUBROS = {
    "it services and it consulting": "Tecnología",
    "information technology": "Tecnología",
    "it": "Tecnología",
    "technology": "Tecnología",
    "software development": "Tecnología",
    "software": "Tecnología",
    "tecnologia de la informacion": "Tecnología",
    "tecnologias de la informacion": "Tecnología",
    "consultoria de tecnologia": "Tecnología",
    "banking": "Banca",
    "financial services": "Servicios Financieros",
    "servicios financieros": "Servicios Financieros",
    "insurance": "Seguros",
    "consulting": "Consultoría",
    "business consulting and services": "Consultoría",
    "retail": "Retail",
    "telecommunications": "Telecomunicaciones",
    "healthcare": "Salud",
    "hospital & health care": "Salud",
    "education": "Educación",
    "higher education": "Educación",
    "mining": "Minería",
    "manufacturing": "Manufactura",
    "logistics": "Logística",
    "transportation": "Transporte",
    "staffing and recruiting": "Recursos Humanos",
    "human resources": "Recursos Humanos",
}


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def clave(nombre: str) -> str:
    """Forma normalizada para agrupar variantes de la misma habilidad."""
    s = sin_tildes(nombre).lower().strip()
    s = NIVELES.sub(" ", s)
    s = re.sub(r"[\s\-_/\.\+#]+", "", s)
    return s


def clave_con_sinonimos(nombre: str) -> str:
    base = sin_tildes(nombre).lower().strip()
    base = re.sub(r"\s+", " ", NIVELES.sub(" ", base)).strip()
    if base in SINONIMOS:
        return clave(SINONIMOS[base])
    return clave(nombre)


def cargar(cur):
    cur.execute("""
        SELECT sd.skill_id, sd.canonical_skill, sd.category, sd.ai_domain,
               sd.skill_type, count(js.job_id) AS usos
        FROM skill_dictionary sd
        LEFT JOIN job_skills js USING (skill_id)
        GROUP BY 1,2,3,4,5
    """)
    return cur.fetchall()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        filas = cargar(cur)
        print(f"habilidades antes: {len(filas)}")

        # --- agrupar variantes -------------------------------------------
        grupos = collections.defaultdict(list)
        for sid, nombre, cat, dom, tipo, usos in filas:
            if len(nombre.strip()) < MIN_LONGITUD:
                grupos[f"__corta__{sid}"].append((sid, nombre, cat, dom, tipo, usos))
            else:
                grupos[clave_con_sinonimos(nombre)].append(
                    (sid, nombre, cat, dom, tipo, usos))

        fusiones = {k: v for k, v in grupos.items() if len(v) > 1}
        a_borrar = sum(len(v) - 1 for v in fusiones.values())

        # --- dominios contradictorios ------------------------------------
        cambios_dominio = []
        plan_fusion = []
        renombrar: dict[int, str] = {}
        for k, miembros in fusiones.items():
            # Sobrevive la variante más usada; empata por nombre más corto.
            miembros = sorted(miembros, key=lambda m: (-m[5], len(m[1])))
            ganador = miembros[0]

            # La tabla SINONIMOS manda sobre el conteo: si el grupo tiene una
            # forma preferida, esa es la etiqueta, aunque otra variante se use
            # más. Si no, "Problem Solving"(26) le ganaría a las dos variantes
            # de "Resolución de problemas"(17+14=31) por contarlas por separado.
            preferida = next(
                (SINONIMOS[b] for b in
                 (re.sub(r"\s+", " ", NIVELES.sub(" ", sin_tildes(m[1]).lower())).strip()
                  for m in miembros)
                 if b in SINONIMOS),
                None,
            )
            if preferida and preferida != ganador[1]:
                igual = next((m for m in miembros if m[1] == preferida), None)
                if igual is not None:
                    # La forma preferida ya existe: que sea ella la que sobreviva.
                    miembros = [igual] + [m for m in miembros if m[0] != igual[0]]
                    ganador = igual
                else:
                    renombrar[ganador[0]] = preferida
            # El dominio se decide por votos ponderados por uso, prefiriendo
            # cualquier dominio real sobre "No aplica".
            votos = collections.Counter()
            for _, _, _, dom, _, usos in miembros:
                votos[dom] += usos or 1
            mejor = max(votos, key=lambda d: (d != "No aplica", votos[d]))
            plan_fusion.append((ganador, miembros[1:], mejor))
            if mejor != ganador[3]:
                cambios_dominio.append((ganador[1], ganador[3], mejor))

        print(f"grupos con variantes  : {len(fusiones)}")
        print(f"entradas a eliminar   : {a_borrar}")
        print(f"habilidades después   : {len(filas) - a_borrar}")
        print(f"dominios a corregir   : {len(cambios_dominio)}")

        print("\n=== fusiones de mayor impacto ===")
        orden = sorted(plan_fusion, key=lambda p: -(p[0][5] + sum(m[5] for m in p[1])))
        for ganador, absorbidos, dom in orden[:18]:
            total = ganador[5] + sum(m[5] for m in absorbidos)
            det = ", ".join(f"{m[1]}({m[5]})" for m in absorbidos[:4])
            print(f"  {total:>4}  {ganador[1]}({ganador[5]})  ←  {det[:78]}")

        print("\n=== dominios que cambian ===")
        for nombre, antes, despues in cambios_dominio[:12]:
            print(f"  {nombre[:38]:<38} {antes} → {despues}")

        if renombrar:
            print("\n=== renombradas a la forma preferida (tabla SINONIMOS) ===")
            nombres = {f[0]: f[1] for f in filas}
            for sid, nuevo in renombrar.items():
                print(f"  {nombres[sid][:38]:<38} → {nuevo}")

        # --- rubros -------------------------------------------------------
        cur.execute("SELECT rubro_inferido, count(*) FROM puestos GROUP BY 1")
        rubros = cur.fetchall()
        plan_rubros = {}
        for rubro, n in rubros:
            if not rubro:
                continue
            base = re.sub(r"\s+", " ", sin_tildes(rubro).lower()).strip()
            destino = RUBROS.get(base)
            if destino and destino != rubro:
                plan_rubros[rubro] = (destino, n)

        print(f"\n=== rubros: {len(rubros)} distintos, "
              f"{len(plan_rubros)} a unificar ===")
        for origen, (destino, n) in sorted(plan_rubros.items(), key=lambda x: -x[1][1])[:12]:
            print(f"  {n:>4}  {origen[:38]:<38} → {destino}")

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para consolidar.")
            return

        # --- aplicar ------------------------------------------------------
        movidas = eliminadas = 0
        for ganador, absorbidos, dom in plan_fusion:
            destino = ganador[0]
            for sid, *_ in absorbidos:
                cur.execute(
                    """
                    INSERT INTO job_skills (job_id, skill_id, evidence, source_section)
                    SELECT job_id, %s, evidence, source_section
                    FROM job_skills WHERE skill_id = %s
                    ON CONFLICT (job_id, skill_id) DO NOTHING
                    """,
                    (destino, sid),
                )
                movidas += cur.rowcount
                cur.execute("DELETE FROM job_skills WHERE skill_id = %s", (sid,))
                cur.execute("DELETE FROM skill_dictionary WHERE skill_id = %s", (sid,))
                eliminadas += 1
            cur.execute("UPDATE skill_dictionary SET ai_domain = %s WHERE skill_id = %s",
                        (dom, destino))

        for sid, nuevo in renombrar.items():
            cur.execute("UPDATE skill_dictionary SET canonical_skill = %s WHERE skill_id = %s",
                        (nuevo, sid))

        filas_rubro = 0
        for origen, (destino, _) in plan_rubros.items():
            cur.execute("UPDATE puestos SET rubro_inferido = %s WHERE rubro_inferido = %s",
                        (destino, origen))
            filas_rubro += cur.rowcount
        conn.commit()
        print(f"\nrubros unificados       : {filas_rubro} filas")

        cur.execute("SELECT count(*) FROM skill_dictionary")
        quedan = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM job_skills")
        rel = cur.fetchone()[0]
        print(f"\nreferencias reasignadas : {movidas}")
        print(f"entradas eliminadas     : {eliminadas}")
        print(f"skill_dictionary        : {quedan}")
        print(f"job_skills              : {rel}")


if __name__ == "__main__":
    main()
