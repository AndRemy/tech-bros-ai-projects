"""Crea el esquema completo del proyecto en Postgres (Neon).

Es idempotente: usa CREATE TABLE IF NOT EXISTS, así que se puede correr sobre
una base ya poblada sin perder datos.

El esquema tiene dos modelos que conviven a propósito (ver docs/ARQUITECTURA.md):

  raw_ofertas          almacenamiento bruto del scraping (JSONB sin procesar)
    ├── jobs           ─┬─ modelo de habilidades con taxonomía de IA
    │   └── job_skills  │
    │       └── skill_dictionary
    └── puestos        ─┬─ modelo del documento original del proyecto
        └── estudios    │  (aporta nivel_puesto, rubro_inferido, tipo_oferta)

`habilidades` existe por compatibilidad con el diseño original pero NO se usa:
duplica `job_skills` sin la taxonomía de dominios de IA.

    python setup_db.py
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

DDL = """
-- Capa 1: almacenamiento bruto -------------------------------------------
CREATE TABLE IF NOT EXISTS raw_ofertas (
    id              SERIAL PRIMARY KEY,
    fuente          VARCHAR(50),      -- 'la' Laborum · 'li' LinkedIn · 'gob' Get on Board
    source_id       TEXT,             -- identificador nativo del portal
    ingestion_id    UUID,
    scraper_version VARCHAR(50),
    payload         JSONB,            -- oferta completa tal como la devolvió el portal
    payload_hash    TEXT,
    scraped_at      TIMESTAMP DEFAULT NOW(),
    procesado       BOOLEAN DEFAULT FALSE
);

-- Impide reingestar el mismo aviso. Sin este índice la deduplicación de los
-- scrapers no sirve de nada: fue el bug que dejó 265 duplicados en la base.
CREATE UNIQUE INDEX IF NOT EXISTS raw_ofertas_fuente_source_id_key
    ON raw_ofertas (fuente, source_id);

-- Capa 2a: modelo de habilidades con taxonomía de IA -----------------------
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,     -- == raw_ofertas.id como texto
    title       TEXT,
    company     TEXT,
    location    TEXT,
    modality    TEXT,
    salary_min  NUMERIC,
    salary_max  NUMERIC,
    industry    TEXT,
    description TEXT,
    raw_id      INTEGER REFERENCES raw_ofertas(id)
);

CREATE TABLE IF NOT EXISTS skill_dictionary (
    skill_id        SERIAL PRIMARY KEY,
    canonical_skill TEXT UNIQUE,      -- nombre canónico; lo consolida consolidar_skills.py
    category        TEXT,             -- Programacion · IA · Datos · Cloud · Idioma · Blanda …
    ai_domain       TEXT,             -- Generative AI · AI Agents · Machine Learning · … · No aplica
    skill_type      TEXT              -- Technical · AI · Data · Soft · Domain
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id         TEXT    NOT NULL REFERENCES jobs(job_id),
    skill_id       INTEGER NOT NULL REFERENCES skill_dictionary(skill_id),
    evidence       TEXT,              -- frase textual de la oferta que sustenta la habilidad
    source_section TEXT,              -- requisitos · funciones · beneficios · descripcion
    PRIMARY KEY (job_id, skill_id)
);

-- Capa 2b: modelo del documento original ----------------------------------
CREATE TABLE IF NOT EXISTS puestos (
    id                          SERIAL PRIMARY KEY,
    raw_id                      INTEGER REFERENCES raw_ofertas(id),
    fecha_publicacion           DATE,
    dias_activos                INTEGER,
    nombre_empresa              TEXT,
    rubro_inferido              TEXT,
    nombre_puesto_original      TEXT,
    nombre_puesto_estandarizado TEXT,
    nivel_puesto                TEXT,  -- lo fija nivel_desde_titulo.py, no el LLM
    descripcion_rol             TEXT,
    ciudad                      TEXT,
    modalidad                   TEXT,
    tipo_oferta                 TEXT   -- lo fija clasificar_ofertas.py
);

CREATE TABLE IF NOT EXISTS estudios (
    id                   SERIAL PRIMARY KEY,
    puesto_id            INTEGER REFERENCES puestos(id),
    nivel_estudio        TEXT,
    carrera_especialidad TEXT
);

-- Tabla del diseño original que NO se usa: duplica job_skills sin taxonomía
-- de IA. Se crea solo para no romper scripts antiguos que la referencien.
CREATE TABLE IF NOT EXISTS habilidades (
    id                             SERIAL PRIMARY KEY,
    puesto_id                      INTEGER REFERENCES puestos(id),
    descripcion_habilidad_raw      TEXT,
    nombre_habilidad_estandarizado TEXT,
    categoria                      TEXT,
    anos_experiencia               INTEGER
);
"""


def main() -> None:
    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        conn.commit()

        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name
            """
        )
        tablas = [r[0] for r in cur.fetchall()]
        print("Esquema listo. Tablas:")
        for t in tablas:
            cur.execute(f'SELECT count(*) FROM "{t}"')
            print(f"  {t:<20} {cur.fetchone()[0]:>6} filas")


if __name__ == "__main__":
    main()
