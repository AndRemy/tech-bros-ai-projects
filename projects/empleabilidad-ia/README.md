# EmpleabilidadIA 🇵🇪 📊

> **¿La IA está creando empleos nuevos en Perú, o transformando los que ya existían?**
> Medimos 544 ofertas laborales reales para responderlo con datos, no con opinión.

## El problema

Todo el mundo repite que "la IA está cambiando el mercado laboral", pero en Perú
nadie tiene el número. Los reportes disponibles son globales, o de LinkedIn, o
extrapolan de Estados Unidos.

Y hay una trampa de medición: si cuentas como "oferta de IA" todo aviso que
mencione Python o análisis de datos, inflas la cifra hasta que deja de significar
algo. Un Analista de Datos no es un puesto de IA — el puesto existe desde hace
décadas.

Este proyecto scrapea ofertas peruanas reales, las estructura con un LLM y las
clasifica en tres tipos para poder distinguir **creación** de empleo de
**transformación** de empleo.

## El hallazgo

Sobre 544 ofertas peruanas de 269 empresas:

| Tipo de oferta | Ofertas | % |
|---|---:|---:|
| 🤖 **Puesto de IA** — nació con la IA (ML Engineer, AI Engineer, Científico de Datos) | 165 | **30.3%** |
| 🔄 **Tradicional que pide IA** — existía antes, ahora la exige | 157 | **28.9%** |
| 📈 **Datos sin IA** — analítica de siempre, *no* cuenta como IA | 210 | 38.6% |
| — Sin IA ni datos | 12 | 2.2% |

**Casi 3 de cada 10 ofertas son puestos de siempre que ahora exigen IA.** Un
Asistente Comercial en Miraflores al que le piden ChatGPT, un Analista de Gestión
de Eventos que debe manejar Claude, un Analista Comercial en logística que necesita
"herramientas de IA aplicadas al análisis". Eso no es un puesto de IA: es
alfabetización en IA convertida en requisito de contratación.

**Habilidades más demandadas** (% de ofertas que la piden):

```
Python              55.0%   ████████████████████████████
SQL                 43.8%   ██████████████████████
Inglés              37.7%   ███████████████████
Power BI            33.3%   █████████████████
Análisis de datos   21.3%   ███████████
Machine Learning    19.9%   ██████████
```

**Demanda por dominio de IA:**

```
Data Engineering    70.6%      Generative AI       36.0%
Analytics           63.4%      AI Agents           15.3%
Machine Learning    36.2%      MLOps               12.9%
                               Deep Learning        8.6%
```

## Estructura del proyecto

```
empleabilidad-ia/
├── ingesta/     scraping y carga a BD
│                  scraper_laborum_dirigido.py · scraper_linkedin.py
│                  setup_db.py · uploader.py · dedup_db.py · clean_db.py
├── analisis/    extracción con LLM, limpieza y clasificación
│                  processor.py · manual_batch.py · dedup_contenido.py
│                  consolidar_skills.py · nivel_desde_titulo.py · clasificar_ofertas.py
├── reporte/     generación y salida del HTML
│                  generar_reporte.py · plantilla.html · index.html
├── datos/       exports intermedios (gitignored, ej. data.json)
├── docs/        arquitectura, pipeline, hallazgos, decisiones
├── .env         credenciales, nunca versionado
└── README.md
```

## Cómo funciona

```
  Scraping (ingesta/)       Ingesta (ingesta/)   Extracción (analisis/)   Limpieza (analisis/)
  ────────────────────      ──────────────────   ──────────────────────  ─────────────────────

  Laborum (HTML)      →   raw_ofertas    →   processor.py         →   dedup_contenido.py
  parser de Apollo        (JSONB crudo)      Claude + Pydantic        consolidar_skills.py
                          índice único       salida estructurada      nivel_desde_titulo.py
  LinkedIn (Apify)    →   por fuente     →   lotes concurrentes   →   clasificar_ofertas.py
  15 keywords ES/EN       + source_id        reanudable                    ↓
                                                  ↓                  jobs · job_skills
                                             544 ofertas             skill_dictionary
                                             8.344 habilidades       puestos · estudios
                                                                          ↓
                                                                  reporte/generar_reporte.py
                                                                          ↓
                                                                  reporte/index.html
```

Cada habilidad extraída guarda **la frase textual de la oferta que la sustenta** y
de qué sección salió. Eso permite rastrear cualquier cifra del reporte hasta el
aviso original.

## Decisión de diseño: LLM solo donde aporta

La lección más importante del proyecto. El LLM es bueno leyendo prosa ambigua y
malo en tareas que una regla resuelve mejor:

| Etapa | ¿LLM o código? | Por qué |
|---|---|---|
| Extraer habilidades de la descripción | 🤖 LLM | Prosa libre, sinónimos, contexto |
| Inferir rubro de la empresa | 🤖 LLM | Requiere conocimiento del mundo |
| **Nivel del puesto** | ⚙️ **Regex** | El LLM acertaba 42% en "Analista" y 28% en "Jefatura" |
| Deduplicar avisos | ⚙️ Código | Comparación exacta, sin ambigüedad |
| Consolidar variantes de habilidad | ⚙️ Código | "Inglés"/"English" es normalización, no criterio |
| Clasificar tipo de oferta | ⚙️ Código | Regla explícita y auditable |

El caso del nivel de puesto es ilustrativo: Haiku mandaba `JEFE DE DATA E IA` a
"Gerencia" pese a una regla explícita en el prompt. Un regex que lee la palabra del
título acierta **100% en "Analista" y 96% en "Jefatura"** — es más barato, más
exacto y reproducible. Detalle en [`docs/DECISIONES.md`](docs/DECISIONES.md).

## Empezar

Todos los comandos se corren **desde `empleabilidad-ia/`** (el `.env` vive en
esta raíz; los scripts lo encuentran aunque estén en una subcarpeta).

```bash
pip install -r requirements.txt
cp .env.example .env             # completar credenciales
python ingesta/setup_db.py       # crea las 7 tablas (idempotente)
```

### 1. Ingesta — scraping y carga a BD (`ingesta/`)

```bash
# Laborum es gratis; LinkedIn consume crédito de Apify
python ingesta/scraper_laborum_dirigido.py --dry-run   # previsualiza sin escribir
python ingesta/scraper_laborum_dirigido.py
python ingesta/scraper_linkedin.py                     # muestra el plan, NO gasta
python ingesta/scraper_linkedin.py --apply             # ejecuta y gasta crédito

# Solo si scrapeaste a archivo (data_raw/) en vez de escribir directo a la BD
python ingesta/uploader.py
```

### 2. Análisis — extracción con LLM, limpieza y clasificación (`analisis/`)

```bash
python analisis/processor.py --dry-run --limit 3       # valida credenciales
python analisis/processor.py

# Limpieza — SIEMPRE en este orden, SIEMPRE después de procesar
python analisis/dedup_contenido.py --apply
python analisis/consolidar_skills.py --apply
python analisis/nivel_desde_titulo.py --apply
python analisis/clasificar_ofertas.py --apply
```

> ⚠️ **El orden de limpieza no es opcional.** Cada corrida de `processor.py`
> regenera variantes de habilidades ("Inglés" y "English" como entradas distintas)
> y niveles de puesto mal asignados. Si te saltas un paso, las cifras del estudio
> quedan mal — el inglés aparentaba 31% cuando el valor real era 50%.

**Todos los scripts destructivos previsualizan por defecto** y requieren `--apply`
para escribir. Los scrapers usan `--dry-run` para el comportamiento inverso.

### 3. Reporte — generación del HTML (`reporte/`)

```bash
python reporte/generar_reporte.py
```

Consulta la BD, escribe el export intermedio en `datos/data.json` (gitignored)
y regenera `reporte/index.html` inyectando ese JSON en `reporte/plantilla.html`.
Correrlo de nuevo sobrescribe `index.html` con la data actual — no hace falta
tocar el HTML a mano.

## Reporte

[`reporte/index.html`](reporte/index.html) — reporte interactivo autocontenido
(sin build step, gráficos con Chart.js vía CDN). Filtros por sector, región,
seniority y periodo; vistas separadas "Para postulantes" y "Para reclutadores";
cada gráfico declara qué mide, sobre cuántos avisos (n=X) y una lectura en una
frase. Ábrelo directamente en el navegador, no necesita servidor.

## Documentación

| Documento | Qué responde |
|---|---|
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Modelo de datos, por qué hay dos modelos conviviendo, qué hace cada script |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | Orden de ejecución y qué pasa si te lo saltas |
| [`docs/HALLAZGOS.md`](docs/HALLAZGOS.md) | Resultados del estudio y consultas SQL para reproducirlos |
| [`docs/DECISIONES.md`](docs/DECISIONES.md) | Decisiones de ingeniería, bugs encontrados y fuentes descartadas |

## Estado y limitaciones

**Qué está listo:** 544 ofertas peruanas extraídas y limpias, con integridad
verificada (0 huérfanas, 0 duplicados, 0 nombres repetidos en el diccionario).
Pipeline completo y re-ejecutable. Reporte interactivo publicado en
[`reporte/index.html`](reporte/index.html).

**Qué falta:** el post de LinkedIn.

**Limitaciones honestas del dataset:**

- **Sesgo de fuente.** LinkedIn aporta la mayoría del corpus. Las búsquedas
  iniciales fueron todas en inglés, lo que sobre-representó consultoras regionales
  (BairesDev, FullStack). Se corrigió con 6 búsquedas en español que trajeron
  mercado local (BCP, Interbank, Yape, BBVA, Sodimac, Entel, cbc, UNACEM).
- **Huecos conocidos.** Computer Vision aparece en 2.7% y NLP en 8.6%. No sabemos
  si Perú no los demanda o si nunca se buscaron: las keywords `Computer Vision
  Engineer`, `NLP Engineer`, `Prompt Engineer`, `LLM Engineer` y `AI Product
  Manager` quedaron sin ejecutar cuando se agotó el crédito de Apify.
- **Corte temporal.** Ofertas activas en agosto de 2026. No hay serie histórica,
  así que el estudio es una foto, no una tendencia.
- **`salary_min`/`salary_max` casi siempre nulos.** Los avisos peruanos rara vez
  publican sueldo, y cuando lo hacen en otra moneda el extractor lo descarta a
  propósito para no mezclar unidades.

## Referencia

Estudio BID (2026): *What Jobs are Being Created in Latin America?* — el marco de
"empleo creado vs. empleo transformado" que motiva la clasificación en tres tipos.
