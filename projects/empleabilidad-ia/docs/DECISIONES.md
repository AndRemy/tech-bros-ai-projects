# Decisiones de ingeniería

Registro de por qué el código es como es. Escrito para que nadie —incluido el
autor en tres meses— repita el trabajo de averiguarlo.

## 1. Nivel de puesto: regex le gana al LLM

**El problema.** Con el prompt pidiendo explícitamente que "si el título nombra el
nivel, ese manda", Haiku 4.5 seguía mandando `JEFE DE DATA E IA` a *Gerencia* y
`Analista de Ciencia de Datos` a *Especialista*. `Especialista` se volvió un
sumidero: absorbía el 53% de los puestos.

**Medición.**

| Señal en el título | LLM | Regex |
|---|---:|---:|
| Practicante | 97% | **100%** |
| Analista | 42% | **100%** |
| Jefatura | 28% | **96%** |
| Gerencia | 71% | **86%** |

**La decisión.** `nivel_desde_titulo.py` deriva el nivel del título con reglas
deterministas. Dos detalles del diseño importan:

1. **Solo pisa al LLM cuando el título da señal.** Si dice "Data Engineer" sin
   marca de seniority, se respeta lo que infirió el modelo — ahí sí aporta. De 485
   puestos, corrigió 52, confirmó 195 y dejó intactos 238.
2. **La jerarquía gana sobre el seniority.** En "Senior AI-Native Engineering
   Lead" manda "Lead" (Jefatura), no "Senior" (Especialista).

**La lección general:** para campos derivables del texto de forma determinista, el
regex le gana al LLM en exactitud, costo y reproducibilidad. Reserva el LLM para
prosa ambigua.

## 2. Filtros por subcadena: el bug que arruinó el corpus

**`ILIKE '%IA%'` no filtra nada en español.** "IA" es subcadena de aux**ia**ir,
comerc**ia**les, industr**ia**l, gerenc**ia**. De 751 títulos de Laborum, **673
sobrevivieron al filtro solo por esa palabra**. El corpus tenía *Auxiliar de
Almacén*, *Cocinero* y *Mercaderista* en un estudio sobre IA.

**Corregido** con regex y límite de palabra (`\y` en Postgres), en dos niveles:

- **Términos inequívocos** (`machine learning`, `power bi`, `RAG`) buscan en título
  y descripción.
- **Siglas ambiguas** (`IA`, `AI`, `ML`, `BI`) solo cuentan en el título, donde sí
  son señal fiable.

`data` y `datos` sueltos quedaron fuera incluso del título: los cargos reales ya los
cubren los compuestos ("analista de datos", "ciencia de datos"), y sueltos solo
rescataban puestos de digitación.

**El mismo bug existe fuera de nuestro código.** El buscador de Laborum también
coincide por subcadena: la keyword `RPA` devuelve "ca**rpa**" y "Co**rpa**c". Por
eso `scraper_laborum_dirigido.py` aplica el filtro de relevancia *antes* de subir.

## 3. El HTML crudo genera falsos positivos

Buscar términos sobre el HTML sin limpiar produjo:

- `\ydata\y` → 26 falsos positivos por atributos del marcado (`data-max-lines="5"`)
- `\yML\y` → 19 falsos positivos por **mililitros** y etiquetas HTML

Todos los filtros aplican `regexp_replace(campo, '<[^>]+>', ' ', 'g')` antes de
comparar.

## 4. Deduplicar por `source_id` no alcanza

`uploader.py` leía `item['id']`, pero Laborum publica su identificador como
`job_id`. Las 751 filas quedaron con `source_id = "None"` — un solo valor
distinto. Como todos los scrapers deduplican consultando esa columna, **la
deduplicación nunca funcionó**.

Corregido en tres frentes:

1. `extraer_source_id()` prueba `job_id → id → jobId → refId` y omite el ítem si
   no encuentra ninguno (antes escribía el string `"None"`).
2. Índice `UNIQUE (fuente, source_id)` — la base ahora rechaza el duplicado aunque
   el código falle.
3. `dedup_contenido.py` para el caso que el `source_id` no cubre: LinkedIn le da
   **IDs distintos al mismo aviso**. FullStack publicaba 6 avisos entre 11 y 12
   veces cada uno.

## 5. Taxonomía de IA: Python no es Machine Learning

El extractor marcaba `Python` con `ai_domain = "Machine Learning"`. Python es un
lenguaje de propósito general de 1991. Ese solo error arrastraba 278 ofertas al
dominio y producía un falso **67.6% de Machine Learning**.

Lo mismo con MLOps: `CI/CD`, `Terraform`, `Jenkins` y `GitHub Actions` son DevOps
de siempre.

`clasificar_ofertas.py` destilda 8 tecnologías genéricas. Efecto:

| Dominio | Antes | Después |
|---|---:|---:|
| Machine Learning | 67.6% | **35.9%** |
| MLOps | 23.9% | **14.2%** |
| Generative AI | 37.5% | 37.5% *(ya estaba limpio)* |

`Generative AI` y `Deep Learning` no cambiaron porque sus habilidades sí eran
específicas (Prompt Engineering, RAG, LLMs, Claude, LangChain / PyTorch,
TensorFlow, Keras). Esos números se pueden defender.

## 6. Bug de clave foránea al reprocesar

`processor.py` hacía `DELETE FROM puestos WHERE raw_id = %s` sin borrar antes los
`estudios` que dependen de ese puesto. Al reprocesar una oferta que ya existía,
Postgres lo bloqueaba con `ForeignKeyViolation`.

Pasó desapercibido porque en la primera corrida todas las ofertas eran nuevas (no
había `puestos` que borrar). Apareció al reprocesar, y **hizo fracasar en silencio
parte de una corrida** cuyo log estaba filtrado.

Lección de proceso: no filtres el log de un proceso largo a solo las líneas que
esperas ver. Revisa el resultado en vez de asumirlo.

## 7. Fuentes evaluadas y descartadas

No las vuelvas a intentar sin leer esto.

### Get on Board — descartada

API viva (`/api/v0/categories/{cat}/jobs`; el parámetro `expand` devuelve 500). Pero
es un portal **chileno**: de 752 ofertas escaneadas, **357 son de Chile y solo 15 de
Perú**, de las cuales ~6 son de IA/datos.

El script `scraping_getonboard.py` que existía **nunca estuvo implementado** — el
bucle de scraping era un comentario. Se eliminó del repo.

### Laborum API `beesearch` — muerta

`scraping_laborum.py` llamaba a
`/api/v1/beesearch/laborExchange/{id}/jobs`, que hoy devuelve **404**. También
requería una `BROWSERLESS_API_KEY` para saltar Cloudflare. Se eliminó del repo.

**Reemplazo:** Laborum rehizo el sitio. La ruta nueva es `/search-jobs?q=`,
renderizada en servidor, sin XHR de datos que interceptar. Los datos vienen en el
HTML como estado de Apollo serializado. `scraper_laborum_dirigido.py` los extrae
con un parser de llaves balanceadas buscando `{"_id":"<24 hex>"` y filtrando
`__typename == "Job"`. **La descripción completa vive en
`basicEdition[0].description`.**

### Ruido propio de Laborum: convocatorias docentes

De 13 resultados para "inteligencia artificial", 6 eran *"Posgrado … Asignatura:
…"*, más *"Docente Especialista en IA"* e *"Instructores para IA"*. Son
universidades contratando profesores de IA, no empresas contratando gente que haga
IA. Incluirlas infla la demanda medida con oferta educativa.

El regex `ACADEMICO` en `scraper_laborum_dirigido.py` las descarta.

## 8. `data_raw/` no está en el repo

Los JSON del scraping crudo (11.8 MB) están en `.gitignore` por tres razones:

1. **Es data pre-limpieza.** Reprocesarlos con `uploader.py` reinserta avisos que
   `clean_db.py` ya purgó. Pasó una vez: metió 811 filas basura de vuelta.
2. Son contenido de terceros (avisos de portales de empleo).
3. El pipeline los regenera: los scrapers escriben directo a la base.

Si scrapeas a archivo, corre `clean_db.py --apply` después de `uploader.py`.

## 9. Convención de banderas

Los scripts que **borran** o que **gastan dinero** previsualizan por defecto y
requieren `--apply`. Los scrapers gratuitos escriben por defecto y usan `--dry-run`
para lo contrario.

La asimetría es deliberada: el default seguro depende de qué es lo caro de
equivocarse.
