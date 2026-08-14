"""Corrige la taxonomía de IA y clasifica cada oferta en tres tipos.

Dos problemas que inflan las cifras del estudio:

1. **Tecnología genérica marcada como IA.** `Python` (278 ofertas) estaba como
   `Machine Learning`, y `CI/CD`, `Terraform`, `Jenkins` y `GitHub Actions` como
   `MLOps`. Python es un lenguaje de propósito general de 1991 y CI/CD es DevOps
   de siempre. Ese solo error llevaba "Machine Learning" a 67.6% cuando lo real
   es ~21%, y MLOps a 24% cuando lo real es ~5%.

2. **Mezclar dos fenómenos distintos.** Un "Machine Learning Engineer" y un
   "Asistente Comercial al que le piden ChatGPT" no son lo mismo: el primero es
   un puesto que existe por la IA, el segundo es un puesto de siempre que ahora
   exige alfabetización en IA. Publicar un único "X% de ofertas de IA" que los
   sume es indefendible — y para el estudio del BID, la distinción ES el hallazgo.

    python clasificar_ofertas.py            # previsualiza
    python clasificar_ofertas.py --apply    # aplica
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

# Dominios que SÍ son inteligencia artificial. `Data Engineering` y `Analytics`
# quedan fuera a propósito: son trabajo de datos que precede a la IA por décadas.
IA_ESTRICTA = {"Generative AI", "AI Agents", "Machine Learning", "Deep Learning",
               "NLP", "Computer Vision", "MLOps"}
DATOS = {"Data Engineering", "Analytics"}

# Tecnología de propósito general mal etiquetada como IA. Se compara sin tildes,
# en minúsculas y sin separadores.
GENERICAS = {
    # lenguajes
    "python", "java", "javascript", "typescript", "c", "cpp", "csharp", "go",
    "golang", "rust", "scala", "php", "ruby", "kotlin", "swift", "bash", "shell",
    # devops / infra
    "cicd", "docker", "kubernetes", "terraform", "jenkins", "githubactions",
    "azuredevops", "gitlabci", "ansible", "linux", "nginx", "helm",
    # control de versiones
    "git", "github", "gitlab", "bitbucket",
    # nube genérica
    "aws", "azure", "gcp", "googlecloud", "cloudcomputing",
    # bases de datos genéricas
    "postgresql", "mysql", "mongodb", "sqlserver", "oracle", "redis",
    # web / apps
    "react", "nodejs", "angular", "vue", "django", "flask", "fastapi", "spring",
    "html", "css", "api", "apis", "rest", "restapi", "graphql", "microservicios",
    # metodologías y blandas
    "scrum", "agile", "kanban", "jira", "devops", "ingles", "espanol",
    "comunicacion", "liderazgo", "trabajoenequipo", "resoluciondeproblemas",
    # ofimática
    "excel", "powerpoint", "word", "officesuite", "microsoftoffice",
}

# El título delata que el puesto existe POR la IA.
TITULO_IA = re.compile(
    r"\b(ia|a\.?i\.?)\b|inteligencia artificial|machine learning|deep learning|"
    r"\bml\b|\bllm\b|\bnlp\b|data scien|cient[íi]fico de datos|computer vision|"
    r"visi[óo]n por computador|prompt engineer|\bmlops\b|generative|generativa|"
    r"agentic|\bagente[s]? de ia\b|redes neuronales",
    re.I,
)


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def clave(s: str) -> str:
    return re.sub(r"[\s\-_/\.\+#]+", "", sin_tildes(s).lower().strip())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        # ---- 1. destildar tecnología genérica -----------------------------
        cur.execute("""
            SELECT sd.skill_id, sd.canonical_skill, sd.ai_domain,
                   count(DISTINCT js.job_id)
            FROM skill_dictionary sd LEFT JOIN job_skills js USING (skill_id)
            WHERE sd.ai_domain <> 'No aplica'
            GROUP BY 1,2,3
        """)
        a_destildar = [(sid, nom, dom, n) for sid, nom, dom, n in cur.fetchall()
                       if clave(nom) in GENERICAS]

        print(f"habilidades marcadas como IA sin serlo: {len(a_destildar)}")
        for sid, nom, dom, n in sorted(a_destildar, key=lambda x: -x[3])[:14]:
            print(f"  {n:>4} ofertas  {nom[:30]:<30} {dom} → No aplica")

        # ---- 2. clasificar ofertas ---------------------------------------
        destildados = {s[0] for s in a_destildar}
        cur.execute("""
            SELECT js.job_id, js.skill_id, sd.ai_domain
            FROM job_skills js JOIN skill_dictionary sd USING (skill_id)
        """)
        doms = collections.defaultdict(set)
        for job_id, skill_id, dom in cur.fetchall():
            if skill_id not in destildados:  # ya con la corrección aplicada
                doms[job_id].add(dom)

        cur.execute("SELECT raw_id, nombre_puesto_original FROM puestos")
        titulos = {str(rid): t or "" for rid, t in cur.fetchall()}

        plan, conteo, ejemplos = {}, collections.Counter(), collections.defaultdict(list)
        for job_id, titulo in titulos.items():
            d = doms.get(job_id, set())
            if TITULO_IA.search(titulo):
                tipo = "Puesto de IA"
            elif d & IA_ESTRICTA:
                tipo = "Tradicional que pide IA"
            elif d & DATOS:
                tipo = "Datos sin IA"
            else:
                tipo = "Sin IA ni datos"
            plan[job_id] = tipo
            conteo[tipo] += 1
            if len(ejemplos[tipo]) < 6:
                ejemplos[tipo].append(titulo)

        total = sum(conteo.values())
        print(f"\n=== clasificación de {total} ofertas ===")
        for tipo, n in conteo.most_common():
            print(f"  {100*n/total:5.1f}%  {n:>4}  {tipo}")
        for tipo in ("Puesto de IA", "Tradicional que pide IA", "Datos sin IA"):
            print(f"\n  --- {tipo} ---")
            for t in ejemplos[tipo]:
                print(f"    {t[:62]}")

        print("\n=== dominios de IA, ya sin tecnología genérica ===")
        for dom in sorted(IA_ESTRICTA | DATOS):
            n = sum(1 for d in doms.values() if dom in d)
            print(f"  {100*n/total:5.1f}%  {n:>4}  {dom}")

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para aplicar.")
            return

        for sid, *_ in a_destildar:
            cur.execute("UPDATE skill_dictionary SET ai_domain = 'No aplica' "
                        "WHERE skill_id = %s", (sid,))

        cur.execute("ALTER TABLE puestos ADD COLUMN IF NOT EXISTS tipo_oferta TEXT")
        for job_id, tipo in plan.items():
            cur.execute("UPDATE puestos SET tipo_oferta = %s WHERE raw_id = %s",
                        (tipo, int(job_id)))
        conn.commit()

        print(f"\nhabilidades destildadas : {len(a_destildar)}")
        print(f"ofertas clasificadas    : {len(plan)}  (columna puestos.tipo_oferta)")


if __name__ == "__main__":
    main()
