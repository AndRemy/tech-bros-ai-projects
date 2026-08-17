"""Genera el reporte HTML interactivo a partir de la base de datos.

Dos pasos:
  1. Consulta Postgres y arma un export intermedio en `../datos/data.json`
     (avisos + habilidades + estudios, uno por línea de `puestos`).
  2. Inyecta ese JSON en `plantilla.html` (que trae el marcador
     `__DATA_JSON__`) y escribe el resultado en `index.html`.

No requiere build step: el HTML final es autocontenido, con Chart.js desde
CDN. Correrlo de nuevo sobrescribe `index.html` con la data actual de la BD.

    python reporte/generar_reporte.py
"""

import json
import os
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

AQUI = Path(__file__).parent
DATOS_DIR = AQUI.parent / "datos"
PLANTILLA = AQUI / "plantilla.html"
SALIDA = AQUI / "index.html"


def region_de(ciudad: str) -> str:
    if not ciudad or ciudad.strip() == "" or ciudad.strip().lower() == "no especificado":
        return "No especificado"
    c = ciudad.lower()
    lima_hits = [
        "lima", "san isidro", "miraflores", "surco", "la molina", "callao",
        "la victoria", "san borja", "magdalena", "san miguel", "jesus maria",
        "jesús maría", "barranco", "chorrillos", "san juan de lurigancho",
        "los olivos", "independencia", "comas", "ate", "santa anita",
        "lima metropolitan", "pueblo libre", "lince", "surquillo", "breña",
    ]
    if any(h in c for h in lima_hits):
        return "Lima"
    if c.strip() in ("perú", "peru"):
        return "No especificado"
    return "Provincia"


def q(cur, sql, params=None):
    cur.execute(sql, params or ())
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def construir_registros(cur) -> list[dict]:
    puestos = q(
        cur,
        """
        SELECT p.id, p.raw_id, p.fecha_publicacion, p.dias_activos, p.nombre_empresa,
               p.rubro_inferido, p.nombre_puesto_estandarizado, p.nivel_puesto,
               p.ciudad, p.modalidad, p.tipo_oferta,
               j.salary_min, j.salary_max
        FROM puestos p
        LEFT JOIN jobs j ON j.job_id = p.raw_id::text
        """,
    )

    skills_rows = q(
        cur,
        """
        SELECT js.job_id, sd.canonical_skill, sd.category, sd.ai_domain, sd.skill_type
        FROM job_skills js
        JOIN skill_dictionary sd USING (skill_id)
        """,
    )
    skills_por_job: dict[str, list[dict]] = {}
    for r in skills_rows:
        skills_por_job.setdefault(r["job_id"], []).append(
            {
                "skill": r["canonical_skill"],
                "category": r["category"],
                "ai_domain": r["ai_domain"],
                "skill_type": r["skill_type"],
            }
        )

    estudios_rows = q(cur, "SELECT puesto_id, nivel_estudio, carrera_especialidad FROM estudios")
    estudios_por_puesto: dict[int, list[dict]] = {}
    for r in estudios_rows:
        estudios_por_puesto.setdefault(r["puesto_id"], []).append(
            {"nivel_estudio": r["nivel_estudio"], "carrera": r["carrera_especialidad"]}
        )

    sector_counts = Counter((p["rubro_inferido"] or "No especificado") for p in puestos)
    top_sectores = {s for s, _ in sector_counts.most_common(16)}

    def agrupar_sector(s):
        s = s or "No especificado"
        if s == "No especificado":
            return s
        return s if s in top_sectores else "Otros"

    registros = []
    for p in puestos:
        raw_id = p["raw_id"]
        job_id_str = str(raw_id)
        fecha = p["fecha_publicacion"].isoformat() if p["fecha_publicacion"] else None
        periodo = fecha[:7] if fecha else None
        registros.append(
            {
                "id": p["id"],
                "raw_id": raw_id,
                "empresa": p["nombre_empresa"],
                "puesto": p["nombre_puesto_estandarizado"],
                "sector": agrupar_sector(p["rubro_inferido"]),
                "ciudad": p["ciudad"] or "No especificado",
                "region": region_de(p["ciudad"]),
                "seniority": p["nivel_puesto"] or "No especificado",
                "modalidad": p["modalidad"] or "No especificado",
                "tipo_oferta": p["tipo_oferta"],
                "fecha": fecha,
                "periodo": periodo,
                "dias_activos": p["dias_activos"],
                "salary_min": float(p["salary_min"]) if p["salary_min"] is not None else None,
                "salary_max": float(p["salary_max"]) if p["salary_max"] is not None else None,
                "skills": skills_por_job.get(job_id_str, []),
                "estudios": estudios_por_puesto.get(p["id"], []),
            }
        )
    return registros


def main() -> None:
    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        registros = construir_registros(cur)

    DATOS_DIR.mkdir(exist_ok=True)
    data_json = json.dumps(registros, ensure_ascii=False)
    (DATOS_DIR / "data.json").write_text(data_json, encoding="utf-8")
    print(f"export intermedio: {DATOS_DIR / 'data.json'} ({len(registros)} avisos)")

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if "__DATA_JSON__" not in plantilla:
        raise SystemExit(f"{PLANTILLA} no tiene el marcador __DATA_JSON__")
    salida = plantilla.replace("__DATA_JSON__", data_json)
    SALIDA.write_text(salida, encoding="utf-8")
    print(f"reporte generado: {SALIDA} ({len(salida)} bytes)")


if __name__ == "__main__":
    main()
