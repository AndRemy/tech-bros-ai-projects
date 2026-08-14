"""Paso 2 del pipeline: estructura las ofertas de `raw_ofertas` con Claude.

Lee las ofertas sin procesar, extrae puesto / habilidades / estudios con salida
estructurada y puebla las tablas relacionales. Es reanudable: cada oferta se
marca `procesado = TRUE` solo si su transacción completa se confirmó.

Uso:
    python processor.py --limit 20        # prueba acotada
    python processor.py                   # procesa todo lo pendiente
    python processor.py --dry-run --limit 3
"""

import argparse
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Literal, Optional

import anthropic
import psycopg
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

MODELO = "claude-haiku-4-5"

# `effort` solo existe en Opus 4.5+ y Sonnet 4.6+; en Haiku 4.5 la API devuelve 400.
# Déjalo en None para Haiku, o en "low"/"medium"/"high" si vuelves a un modelo mayor.
EFFORT = None

MAX_TOKENS = 8000
MAX_CARACTERES_DESCRIPCION = 6000

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s"
)
logger = logging.getLogger("processor")

_cliente = None


def cliente() -> anthropic.Anthropic:
    """Cliente perezoso: permite importar este módulo sin ANTHROPIC_API_KEY.

    `manual_batch.py` reutiliza el esquema y `guardar()` de aquí sin llamar a la API.
    """
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic(max_retries=5)
    return _cliente


# --------------------------------------------------------------------------
# Taxonomía
# --------------------------------------------------------------------------

NivelPuesto = Literal[
    "Practicante", "Asistente", "Analista", "Especialista",
    "Jefatura", "Gerencia", "Direccion", "No especificado",
]
Modalidad = Literal["Presencial", "Remoto", "Hibrido", "No especificado"]
Categoria = Literal[
    "Programacion", "IA", "Datos", "Cloud", "Herramienta", "Tecnologia",
    "Metodologia", "Idioma", "Blanda", "Otro",
]
DominioIA = Literal[
    "Generative AI", "AI Agents", "Machine Learning", "Deep Learning",
    "NLP", "Computer Vision", "MLOps", "Data Engineering", "Analytics",
    "No aplica",
]
TipoHabilidad = Literal["Technical", "AI", "Data", "Soft", "Domain"]
NivelEstudio = Literal[
    "Estudiante", "Tecnico", "Egresado", "Bachiller", "Titulado",
    "Magister", "Doctorado", "No especificado",
]


class Habilidad(BaseModel):
    skill: str
    category: Categoria
    ai_domain: DominioIA
    skill_type: TipoHabilidad
    evidence: str
    source_section: str


class Estudio(BaseModel):
    nivel_estudio: NivelEstudio
    carrera_especialidad: str


class Puesto(BaseModel):
    title: str
    title_standardized: str
    company: str
    industry: str
    level: NivelPuesto
    city: str
    modality: Modalidad
    salary_min: Optional[float]
    salary_max: Optional[float]
    role_summary: str


class OfertaEstructurada(BaseModel):
    job: Puesto
    skills: list[Habilidad]
    studies: list[Estudio]


SYSTEM_PROMPT = """\
Analizas ofertas laborales del mercado peruano para un estudio sobre la demanda \
de habilidades de inteligencia artificial. Extraes datos estructurados a partir \
del texto de cada oferta.

Reglas de extracción:
- Usa solo lo que aparece en la oferta. Cuando un dato no esté presente, usa \
"No especificado" en los campos de taxonomía y una cadena vacía en los de texto \
libre. No infieras sueldos ni ciudades que la oferta no menciona.
- `title` es el título literal publicado; `title_standardized` es su forma \
canónica en español, sin nivel ni marca (por ejemplo "Analista de Datos Senior" \
→ "Analista de Datos").
- `level` describe la jerarquía del puesto, no los años de experiencia ni la \
dificultad técnica. Decídelo así, en este orden:
  1. Si el título nombra el nivel, ese manda, aunque el puesto sea muy técnico: \
"Practicante" → Practicante; "Asistente"/"Auxiliar" → Asistente; "Analista" → \
Analista; "Especialista" → Especialista; "Jefe"/"Líder"/"Lead"/"Head of" → \
Jefatura; "Gerente"/"Manager" → Gerencia; "Director"/"Chief"/"VP" → Direccion.
  2. Si el título no nombra el nivel (por ejemplo "Data Engineer", "AI Engineer", \
"Data Scientist"), usa la marca de seniority: "Jr"/"Junior"/"Trainee" → Analista; \
sin marca o "Semi Senior"/"Mid" → Analista; "Senior"/"Sr"/"Staff"/"Principal"/"Expert" \
→ Especialista.
  3. Solo si no hay ninguna señal, usa "No especificado".
- "Jefatura" y "Gerencia" no son lo mismo: Jefatura lidera un equipo dentro de un \
área; Gerencia dirige el área completa. Un "Tech Lead" o "Team Lead" es Jefatura, \
no Gerencia.
- "Especialista" no es el nivel por defecto de los puestos técnicos. Un "Data \
Engineer" sin marca de seniority es Analista, no Especialista.
- `industry` es el rubro de la empresa (banca, retail, salud, consultoría, \
minería, tecnología…), no el área del puesto.
- Los sueldos van en soles peruanos, como número. Si la oferta publica un monto \
en otra moneda o un rango por hora, deja ambos campos nulos.

Habilidades:
- Registra cada habilidad técnica, herramienta, tecnología o competencia \
relevante que la oferta pida, una entrada por habilidad. No agrupes varias en \
una sola entrada.
- `skill` es el nombre canónico de la habilidad ("Python", "SQL", "Power BI", \
"AWS", "Scrum"). Unifica variantes: "Phyton"/"python3" → "Python".
- `ai_domain` solo aplica a habilidades de IA o datos; para el resto usa \
"No aplica".
- `evidence` es la frase textual de la oferta que sustenta la habilidad.
- `source_section` indica de qué parte salió: "requisitos", "funciones", \
"beneficios", "descripcion" o "competencias".

Estudios:
- Una entrada por combinación de nivel y carrera solicitada. Si la oferta pide \
"Bachiller o Titulado en Ingeniería de Sistemas o Informática", genera las \
entradas que correspondan a cada combinación mencionada."""


# --------------------------------------------------------------------------
# Normalización del payload
# --------------------------------------------------------------------------

ETIQUETA_HTML = re.compile(r"<[^>]+>")
ESPACIOS = re.compile(r"[ \t]*\n[ \t\n]*")

# Cada fuente nombra los campos distinto: Laborum usa `description`, LinkedIn
# usa `descriptionText`. Leer solo `description` deja sin texto a las 630
# ofertas de LinkedIn.
CAMPOS_TEXTO = (
    ("descripcion", ("description", "descriptionText", "descriptionHtml")),
    ("requisitos", ("requirements",)),
    ("competencias", ("competencies",)),
    ("beneficios", ("benefits",)),
    ("detalle", ("detail_job",)),
)

CAMPOS_FECHA = ("publish_date", "postedAt")


def _aplanar(valor) -> str:
    """Convierte a texto los campos que llegan como lista o dict."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, list):
        return "\n".join(_aplanar(v) for v in valor)
    if isinstance(valor, dict):
        return "\n".join(_aplanar(v) for v in valor.values())
    return str(valor)


def limpiar(texto: str) -> str:
    texto = ETIQUETA_HTML.sub(" ", texto)
    texto = texto.replace("&nbsp;", " ").replace("&amp;", "&")
    texto = ESPACIOS.sub("\n", texto)
    return re.sub(r" {2,}", " ", texto).strip()


def armar_texto_oferta(payload: dict) -> str:
    """Reúne el texto útil de la oferta, sea de Laborum o de LinkedIn."""
    bloques = []

    titulo = payload.get("title") or ""
    empresa = payload.get("company") or payload.get("companyName") or ""
    ubicacion = payload.get("lugar") or payload.get("location") or ""
    area = payload.get("area") or payload.get("jobFunction") or ""
    jerarquia = payload.get("jerarquia") or payload.get("seniorityLevel") or ""
    rubro = _aplanar(payload.get("industries"))
    salario = payload.get("salary") or ""
    contrato = payload.get("employmentType") or payload.get("horario") or ""

    encabezado = [
        f"Título: {titulo}",
        f"Empresa: {empresa}",
        f"Ubicación: {_aplanar(ubicacion)}",
        f"Área: {_aplanar(area)}",
        f"Jerarquía declarada: {_aplanar(jerarquia)}",
        f"Rubro declarado: {rubro}",
        f"Sueldo declarado: {_aplanar(salario)}",
        f"Tipo de contrato: {_aplanar(contrato)}",
    ]
    bloques.append("\n".join(l for l in encabezado if not l.endswith(": ")))

    for etiqueta, claves in CAMPOS_TEXTO:
        for clave in claves:
            texto = limpiar(_aplanar(payload.get(clave)))
            if texto:
                bloques.append(f"[{etiqueta}]\n{texto}")
                break  # basta la primera variante presente

    return "\n\n".join(bloques)[:MAX_CARACTERES_DESCRIPCION]


def extraer_fecha(payload: dict) -> Optional[date]:
    for clave in CAMPOS_FECHA:
        crudo = payload.get(clave)
        if not isinstance(crudo, str) or not crudo:
            continue
        try:
            return datetime.fromisoformat(crudo.replace("Z", "+00:00")).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------
# Llamada a Claude
# --------------------------------------------------------------------------


def estructurar(texto: str) -> OfertaEstructurada:
    extra = {"output_config": {"effort": EFFORT}} if EFFORT else {}
    respuesta = cliente().messages.parse(
        model=MODELO,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        output_format=OfertaEstructurada,
        messages=[{"role": "user", "content": texto}],
        **extra,
    )
    if respuesta.stop_reason == "refusal":
        raise RuntimeError("Claude rechazó la solicitud")
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError("Respuesta truncada: sube MAX_TOKENS")
    return respuesta.parsed_output


# --------------------------------------------------------------------------
# Persistencia
# --------------------------------------------------------------------------


def leer_pendientes(limite: Optional[int]) -> list[tuple[int, dict]]:
    sql = "SELECT id, payload FROM raw_ofertas WHERE procesado = FALSE ORDER BY id"
    if limite:
        sql += f" LIMIT {int(limite)}"
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def guardar(conn, raw_id: int, payload: dict, datos: OfertaEstructurada) -> None:
    """Escribe una oferta en las tablas relacionales. Todo o nada."""
    job = datos.job
    job_id = str(raw_id)
    fecha = extraer_fecha(payload)
    dias_activos = (date.today() - fecha).days if fecha else None

    with conn.cursor() as cur:
        # --- jobs / skill_dictionary / job_skills (taxonomía de IA) ---
        cur.execute(
            """
            INSERT INTO jobs (job_id, title, company, location, modality,
                              salary_min, salary_max, industry, description, raw_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                title = EXCLUDED.title, company = EXCLUDED.company,
                location = EXCLUDED.location, modality = EXCLUDED.modality,
                salary_min = EXCLUDED.salary_min, salary_max = EXCLUDED.salary_max,
                industry = EXCLUDED.industry, description = EXCLUDED.description
            """,
            (job_id, job.title, job.company, job.city, job.modality,
             job.salary_min, job.salary_max, job.industry, job.role_summary, raw_id),
        )

        cur.execute("DELETE FROM job_skills WHERE job_id = %s", (job_id,))
        for h in datos.skills:
            cur.execute(
                """
                INSERT INTO skill_dictionary (canonical_skill, category, ai_domain, skill_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (canonical_skill) DO UPDATE
                    SET canonical_skill = EXCLUDED.canonical_skill
                RETURNING skill_id
                """,
                (h.skill, h.category, h.ai_domain, h.skill_type),
            )
            skill_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO job_skills (job_id, skill_id, evidence, source_section)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (job_id, skill_id) DO NOTHING
                """,
                (job_id, skill_id, h.evidence, h.source_section),
            )

        # --- puestos / estudios (modelo del documento del proyecto) ---
        # `estudios.puesto_id` tiene FK contra `puestos.id`, así que la fila de
        # `puestos` es obligatoria para poder registrar estudios — y al reprocesar
        # hay que borrar los estudios ANTES que el puesto, o la FK lo bloquea.
        cur.execute(
            "DELETE FROM estudios WHERE puesto_id IN "
            "(SELECT id FROM puestos WHERE raw_id = %s)", (raw_id,)
        )
        cur.execute("DELETE FROM puestos WHERE raw_id = %s", (raw_id,))
        cur.execute(
            """
            INSERT INTO puestos (raw_id, fecha_publicacion, dias_activos, nombre_empresa,
                                 rubro_inferido, nombre_puesto_original,
                                 nombre_puesto_estandarizado, nivel_puesto,
                                 descripcion_rol, ciudad, modalidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (raw_id, fecha, dias_activos, job.company, job.industry, job.title,
             job.title_standardized, job.level, job.role_summary, job.city, job.modality),
        )
        puesto_id = cur.fetchone()[0]

        for e in datos.studies:
            cur.execute(
                "INSERT INTO estudios (puesto_id, nivel_estudio, carrera_especialidad) "
                "VALUES (%s, %s, %s)",
                (puesto_id, e.nivel_estudio, e.carrera_especialidad),
            )

        cur.execute("UPDATE raw_ofertas SET procesado = TRUE WHERE id = %s", (raw_id,))
    conn.commit()


# --------------------------------------------------------------------------
# Orquestación
# --------------------------------------------------------------------------


def procesar_uno(item: tuple[int, dict]):
    raw_id, payload = item
    texto = armar_texto_oferta(payload)
    if len(texto) < 120:
        return raw_id, payload, None, "texto insuficiente en el payload"
    try:
        return raw_id, payload, estructurar(texto), None
    except Exception as exc:  # noqa: BLE001 - se reporta y se continúa
        return raw_id, payload, None, f"{type(exc).__name__}: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="máximo de ofertas a procesar")
    parser.add_argument("--batch-size", type=int, default=25,
                        help="ofertas por lote antes de escribir (default: 25)")
    parser.add_argument("--workers", type=int, default=5,
                        help="llamadas concurrentes a la API (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="extrae con Claude pero no escribe en la base")
    args = parser.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Falta ANTHROPIC_API_KEY en el .env")

    pendientes = leer_pendientes(args.limit)
    if not pendientes:
        logger.info("No hay ofertas pendientes.")
        return

    logger.info("Pendientes: %d | modelo=%s effort=%s", len(pendientes), MODELO, EFFORT)

    ok = 0
    fallidos: list[tuple[int, str]] = []
    conn = None if args.dry_run else psycopg.connect(DATABASE_URL)

    try:
        for inicio in range(0, len(pendientes), args.batch_size):
            lote = pendientes[inicio:inicio + args.batch_size]

            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                resultados = list(pool.map(procesar_uno, lote))

            for raw_id, payload, datos, error in resultados:
                if error:
                    fallidos.append((raw_id, error))
                    logger.warning("id=%s omitido: %s", raw_id, error)
                    continue
                if args.dry_run:
                    logger.info(
                        "id=%s [dry-run] %s | %s | %d habilidades, %d estudios",
                        raw_id, datos.job.title_standardized, datos.job.level,
                        len(datos.skills), len(datos.studies),
                    )
                    ok += 1
                    continue
                try:
                    guardar(conn, raw_id, payload, datos)
                    ok += 1
                except Exception as exc:  # noqa: BLE001
                    conn.rollback()
                    fallidos.append((raw_id, f"BD {type(exc).__name__}: {exc}"))
                    logger.error("id=%s no se pudo guardar: %s", raw_id, exc)

            logger.info("Avance: %d/%d procesadas", ok, len(pendientes))
    finally:
        if conn:
            conn.close()

    logger.info("Listo. Procesadas: %d | fallidas: %d", ok, len(fallidos))
    if fallidos:
        logger.info("Las fallidas siguen en procesado=FALSE; vuelve a correr para reintentar.")
        for raw_id, error in fallidos[:20]:
            logger.info("  id=%s -> %s", raw_id, error)


if __name__ == "__main__":
    main()
