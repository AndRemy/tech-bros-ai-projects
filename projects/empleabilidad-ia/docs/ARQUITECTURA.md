# Arquitectura

## Modelo de datos

Siete tablas en Postgres (Neon), en tres capas.

```
raw_ofertas ─── almacenamiento bruto, una fila por aviso scrapeado
    │           payload JSONB completo · UNIQUE (fuente, source_id)
    │
    ├─► jobs ──────────────► job_skills ──────► skill_dictionary
    │   job_id = raw_id      evidence            canonical_skill
    │   como texto           source_section      ai_domain · skill_type
    │
    └─► puestos ───────────► estudios
        nivel_puesto         nivel_estudio
        rubro_inferido       carrera_especialidad
        tipo_oferta
```

### Por qué hay dos modelos conviviendo

No es accidente ni deuda técnica: son dos vistas complementarias de la misma
oferta, y **el esquema obliga a mantener ambas**.

- **`jobs` / `job_skills` / `skill_dictionary`** es el modelo de habilidades. Es
  donde vive la taxonomía de IA (`ai_domain`) y la trazabilidad (`evidence`). Es lo
  que sostiene las cifras del tipo "el 36% de las ofertas pide IA generativa".

- **`puestos` / `estudios`** es el modelo del documento original del proyecto.
  Aporta tres dimensiones que `jobs` no tiene: `nivel_puesto`, `rubro_inferido` y
  `tipo_oferta`. Sin él no puedes cruzar habilidades contra seniority ni sector.

La restricción que fuerza la convivencia: **`estudios.puesto_id` tiene una clave
foránea contra `puestos.id`, no contra `jobs`**. Poblar `estudios` —que ambos
documentos del proyecto piden— es imposible sin poblar `puestos`. Por eso
`processor.py` escribe los dos modelos con una sola llamada al LLM.

`habilidades` es la séptima tabla y **no se usa**: duplica `job_skills` sin la
taxonomía de dominios de IA. Se crea solo para no romper scripts antiguos.

### Claves y restricciones que importan

| Restricción | Por qué existe |
|---|---|
| `UNIQUE (fuente, source_id)` en `raw_ofertas` | Impide reingestar el mismo aviso. Sin esto la deduplicación de los scrapers no sirve — fue el bug que dejó 265 duplicados |
| `PRIMARY KEY (job_id, skill_id)` en `job_skills` | Una habilidad aparece una sola vez por oferta |
| `UNIQUE (canonical_skill)` en `skill_dictionary` | Permite el upsert que reutiliza la habilidad existente |
| `estudios.puesto_id → puestos.id` | Obliga a borrar `estudios` **antes** que `puestos` al reprocesar. Saltarse ese orden causa `ForeignKeyViolation` |

### Cascada de borrado

Cualquier script que elimine una fila de `raw_ofertas` debe respetar este orden:

```
job_skills  →  jobs  →  raw_ofertas
estudios    →  puestos  →  raw_ofertas
```

`dedup_contenido.py` lo implementa correctamente. `processor.py` lo hace al
reprocesar una oferta que ya existía.

## Los scripts

### Scraping

| Script | Qué hace |
|---|---|
| `scraper_laborum_dirigido.py` | Busca por 22 keywords de IA/datos en Laborum. **Gratis.** Parsea el estado de Apollo serializado en el HTML |
| `scraper_linkedin.py` | Busca por 15 keywords (7 español + 8 inglés) vía Apify. **Consume crédito** |

Ambos son idempotentes: filtran contra lo que ya está en la base y el índice único
descarta lo demás. Re-ejecutarlos hoy no agrega nada ni duplica.

### Ingesta

| Script | Qué hace |
|---|---|
| `setup_db.py` | Crea las 7 tablas y el índice único. Idempotente |
| `uploader.py` | Carga los JSON de `data_raw/` a la base. Solo se necesita si scrapeaste a archivo |
| `dedup_db.py` | Migración puntual: repobla `source_id` y elimina duplicados por identificador nativo |

### Extracción

| Script | Qué hace |
|---|---|
| `processor.py` | El corazón. Lee ofertas sin procesar, llama a Claude con salida estructurada y puebla los dos modelos |
| `manual_batch.py` | Vía alternativa **sin API**: la extracción la hace un asistente en sesión, reutilizando el esquema y `guardar()` de `processor.py` |

### Limpieza

| Script | Qué hace |
|---|---|
| `clean_db.py` | Descarta ofertas sin señal técnica de IA/datos. Solo aplica a portales generalistas |
| `dedup_contenido.py` | Elimina avisos repetidos por título+empresa (LinkedIn les da `source_id` distinto) |
| `consolidar_skills.py` | Fusiona variantes ("Inglés"/"English") y corrige dominios contradictorios |
| `nivel_desde_titulo.py` | Deriva `nivel_puesto` del título con regex. Solo pisa al LLM cuando el título da señal |
| `clasificar_ofertas.py` | Destilda tecnología genérica mal marcada como IA y clasifica la oferta en 3 tipos |

## Cómo `processor.py` extrae

Usa **salida estructurada** de la API de Anthropic: un esquema Pydantic
(`OfertaEstructurada`) se convierte en JSON Schema y la API garantiza que la
respuesta valide contra él. No hay parsing frágil ni reintentos por JSON malformado.

```python
respuesta = cliente().messages.parse(
    model=MODELO,
    system=SYSTEM_PROMPT,
    output_format=OfertaEstructurada,   # ← el esquema es el contrato
    messages=[{"role": "user", "content": texto}],
)
```

Tres detalles de implementación que importan:

1. **El cliente es perezoso.** Se construye en la primera llamada, no al importar.
   Así `manual_batch.py` puede reutilizar el esquema sin necesitar `ANTHROPIC_API_KEY`.

2. **`effort` es condicional.** Haiku 4.5 no acepta `output_config.effort` —
   devuelve 400. La constante `EFFORT = None` lo omite; ponla en `"medium"` si
   cambias a un modelo mayor.

3. **Escribe y confirma oferta por oferta.** Si el proceso se corta a mitad, lo ya
   extraído queda guardado y una nueva corrida retoma donde quedó.

## Normalización de fuentes

Cada portal nombra los campos distinto. `armar_texto_oferta()` los unifica:

| Concepto | Laborum | LinkedIn |
|---|---|---|
| Identificador | `job_id` | `id` |
| Descripción | `description` | `descriptionText` |
| Empresa | `company` | `companyName` |
| Ubicación | `lugar` | `location` |
| Fecha | `publish_date` | `postedAt` |

Este mapeo no es cosmético: leer solo `description` dejaba **630 ofertas de
LinkedIn entrando al LLM como "Sin descripción"**. Era el 46% del corpus.
