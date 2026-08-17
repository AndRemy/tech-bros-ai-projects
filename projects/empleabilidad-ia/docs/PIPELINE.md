# Pipeline: orden de ejecución

## Regla de oro

**Después de cada corrida de `processor.py`, corre los cuatro scripts de limpieza
en este orden:**

```bash
python analisis/dedup_contenido.py --apply
python analisis/consolidar_skills.py --apply
python analisis/nivel_desde_titulo.py --apply
python analisis/clasificar_ofertas.py --apply
```

No es una recomendación de estilo. Cada extracción con LLM **regenera** los mismos
problemas, porque el modelo no tiene memoria de las decisiones tomadas en corridas
anteriores.

## Qué pasa si te saltas un paso

| Si omites | El síntoma | El daño |
|---|---|---|
| `dedup_contenido.py` | Nada visible | Un aviso repetido 12 veces cuenta 12 veces. FullStack publicaba 6 avisos ~12 veces cada uno: 65 filas sobrantes de una sola empresa, que inflaban `Inglés` +5 pts y `CI/CD` +6 pts |
| `consolidar_skills.py` | Nada visible | "Inglés" (154) y "English" (61) cuentan aparte. El inglés aparentaba **31%** cuando el real era **50%** |
| `nivel_desde_titulo.py` | Nada visible | `Especialista` absorbe el 53% de los puestos. La dimensión de seniority queda inservible |
| `clasificar_ofertas.py` | Nada visible | `Python` cuenta como Machine Learning. "ML" aparentaba **67.6%** cuando el real era **35.9%** |

**Ninguno falla ruidosamente.** Todos producen cifras que se ven razonables y están
mal. Por eso el orden está documentado y no confiado a la memoria.

## Por qué ese orden y no otro

```
1. dedup_contenido      Primero se quitan las filas sobrantes; no tiene sentido
                        consolidar habilidades de avisos que van a desaparecer.

2. consolidar_skills    Después se fusionan variantes. Debe ir tras el dedup
                        porque borra habilidades que quedan sin uso.

3. nivel_desde_titulo   Independiente de las habilidades; toca solo `puestos`.

4. clasificar_ofertas   Va al final porque su clasificación en 3 tipos depende
                        de los dominios de IA ya corregidos.
```

## Ciclo completo desde cero

```bash
# Preparación
pip install -r requirements.txt
cp .env.example .env       # completar credenciales
python ingesta/setup_db.py

# Scraping (ingesta/)
python ingesta/scraper_laborum_dirigido.py --dry-run     # previsualiza
python ingesta/scraper_laborum_dirigido.py               # gratis
python ingesta/scraper_linkedin.py                       # muestra plan, no gasta
python ingesta/scraper_linkedin.py --apply               # gasta crédito Apify

# Filtrado de ruido (solo portales generalistas)
python ingesta/clean_db.py                               # previsualiza
python ingesta/clean_db.py --apply

# Extracción (analisis/)
python analisis/processor.py --dry-run --limit 3         # valida credenciales
python analisis/processor.py

# Limpieza (los cuatro, en orden)
python analisis/dedup_contenido.py --apply
python analisis/consolidar_skills.py --apply
python analisis/nivel_desde_titulo.py --apply
python analisis/clasificar_ofertas.py --apply

# Reporte (reporte/)
python reporte/generar_reporte.py
```

## Convención de banderas

| Tipo de script | Por defecto | Para escribir |
|---|---|---|
| Limpieza (`clean_db`, `dedup_*`, `consolidar_*`, `nivel_*`, `clasificar_*`) | Previsualiza | `--apply` |
| `scraper_laborum_dirigido` | Escribe | `--dry-run` para previsualizar |
| `scraper_linkedin` | Muestra el plan, **no gasta** | `--apply` |
| `processor` | Escribe | `--dry-run` para probar sin escribir |

La asimetría es deliberada: los scripts que **borran** o que **gastan dinero** son
los que previsualizan por defecto.

## Sin crédito de API: la vía manual

`processor.py` necesita saldo en Anthropic. Si no hay, `manual_batch.py` permite
que un asistente haga la extracción en sesión, reutilizando el mismo esquema
Pydantic y la misma función `guardar()` — así las filas quedan idénticas por
cualquiera de los dos caminos.

```bash
python analisis/manual_batch.py --status              # avance
python analisis/manual_batch.py --fetch 3 --todas     # saca el siguiente lote
python analisis/manual_batch.py --write lote.json     # valida y escribe
```

Formato de `lote.json`:

```json
{
  "<raw_id>": {
    "job":     { "title": "...", "level": "Analista", "...": "..." },
    "skills":  [ { "skill": "Python", "ai_domain": "No aplica", "evidence": "..." } ],
    "studies": [ { "nivel_estudio": "Bachiller", "carrera_especialidad": "..." } ]
  }
}
```

Se usó para 92 ofertas cuando se agotó el crédito. Es lento (unas 3-4 ofertas por
vuelta) pero produce data idéntica.

## Costos por corrida

Medidos sobre este proyecto:

| Concepto | Costo real |
|---|---|
| Laborum | **$0** — parsea HTML público con `curl_cffi` |
| LinkedIn vía Apify | **~$0.85 por keyword** (20 resultados). $5 alcanzó para 6 búsquedas |
| Extracción con Haiku 4.5 | **~$0.25 por 100 ofertas** |
| Extracción con Opus 5 | ~$1.20 por 100 ofertas |
| Limpieza completa | **$0** — todo determinista |

El modelo se cambia en `processor.py`, constante `MODELO`. Si subes de Haiku,
recuerda poner `EFFORT = "medium"` (Haiku 4.5 rechaza ese parámetro con un 400).
