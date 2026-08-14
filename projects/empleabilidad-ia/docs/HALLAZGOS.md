# Hallazgos

Corpus: **544 ofertas peruanas · 269 empresas · agosto 2026.**
Cada cifra viene con la consulta que la reproduce.

## 1. El hallazgo central: transformación, no solo creación

```
30.3%  165  Puesto de IA               ← nació con la IA
28.9%  157  Tradicional que pide IA    ← existía antes, ahora la exige
38.6%  210  Datos sin IA               ← analítica de siempre
 2.2%   12  Sin IA ni datos
```

```sql
SELECT tipo_oferta,
       count(*)                                   AS ofertas,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM puestos
GROUP BY 1 ORDER BY 2 DESC;
```

**Por qué importa.** Si sumas los dos primeros grupos y publicas "el 59% de las
ofertas peruanas son de IA", el número es indefendible: un Asistente Comercial al
que le piden ChatGPT no es un puesto de IA. Separarlos es lo que hace el estudio
citable.

El segundo grupo es el hallazgo interesante, y encaja con el marco del estudio BID
2026 sobre empleo creado vs. transformado en Latinoamérica.

Ejemplos reales del grupo "Tradicional que pide IA":

| Puesto | Empresa | Sector | Qué pide |
|---|---|---|---|
| Analista de Gestión de Eventos | Zapler | Comercio | ChatGPT, Claude |
| Asistente Comercial | Niubox | Consultoría | IA generativa para propuestas |
| Analista Comercial | Contrans | Logística | IA aplicada al análisis |
| Data Analyst | U. César Vallejo | Educación | ChatGPT, Microsoft Copilot |
| Analista de Control de Gestión | Continental Standford | Manufactura | "IA aplicable a sus tareas diarias" |

## 2. Habilidades más demandadas

```
55.0%  299  Python                43.8%  238  SQL
37.7%  205  Inglés                33.3%  181  Power BI
21.3%  116  Análisis de datos     19.9%  108  Machine Learning
17.8%   97  AWS                   16.0%   87  Excel
12.7%   69  ETL                   12.1%   66  Automatización de procesos
```

```sql
SELECT sd.canonical_skill,
       count(DISTINCT js.job_id) AS ofertas,
       round(100.0 * count(DISTINCT js.job_id) /
             (SELECT count(*) FROM jobs), 1) AS pct
FROM job_skills js
JOIN skill_dictionary sd USING (skill_id)
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

> ⚠️ Estos porcentajes solo son válidos si `consolidar_skills.py` y
> `dedup_contenido.py` corrieron. Sin ellos, "Inglés" y "English" cuentan aparte y
> el idioma aparenta 31% en vez de 50%.

## 3. Demanda por dominio de IA

```
70.6%  384  Data Engineering      36.0%  196  Generative AI
63.4%  345  Analytics             15.3%   83  AI Agents
36.2%  197  Machine Learning      12.9%   70  MLOps
                                   8.6%   47  Deep Learning
                                   2.7%   ~15 Computer Vision
```

```sql
SELECT sd.ai_domain,
       count(DISTINCT js.job_id) AS ofertas,
       round(100.0 * count(DISTINCT js.job_id) /
             (SELECT count(*) FROM jobs), 1) AS pct
FROM job_skills js
JOIN skill_dictionary sd USING (skill_id)
WHERE sd.ai_domain <> 'No aplica'
GROUP BY 1 ORDER BY 2 DESC;
```

**Cómo leerlo.** `Data Engineering` y `Analytics` **no son IA** — son trabajo de
datos que precede a la IA por décadas. Para hablar de IA estricta, usa los dominios
`Generative AI`, `AI Agents`, `Machine Learning`, `Deep Learning`, `NLP`,
`Computer Vision` y `MLOps`.

**IA generativa en el 36% de las ofertas** es el titular más fuerte y más
defendible: sus habilidades son inequívocas (Prompt Engineering, RAG, LLMs, Claude,
LangChain), no hay tecnología genérica inflando el número.

## 4. Nivel de puesto

```
Especialista  ████████████████  ~48%      Jefatura      ██   ~6%
Analista      ███████           ~20%      Gerencia      █    ~2%
Practicante   ███                ~9%      Dirección     █    ~1%
Asistente     ██                 ~7%      No especificado    ~6%
```

```sql
SELECT nivel_puesto, count(*) AS ofertas,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM puestos GROUP BY 1 ORDER BY 2 DESC;
```

Confiable **solo si corrió `nivel_desde_titulo.py`**. Sin él, `Especialista`
absorbe el 53% y la dimensión no sirve.

## 5. Sectores

```
Tecnología ~50%  ·  Banca  ·  Telecomunicaciones  ·  Seguros
Servicios Financieros  ·  Consultoría  ·  Salud  ·  Retail
```

```sql
SELECT rubro_inferido, count(*) AS ofertas
FROM puestos GROUP BY 1 ORDER BY 2 DESC LIMIT 15;
```

El corpus en español trajo el mercado local que las búsquedas en inglés no
mostraban: **BCP, Interbank, Yape, BBVA, Pacífico Seguros, Sodimac, Entel, cbc,
UNACEM, Industrias San Miguel, Auna, Grupo Vega**. Empresas peruanas tradicionales
creando puestos de datos e IA — incluidos cargos de dirección como *JEFE DE DATA E
IA* en cbc (bebidas, 137 años) y *LEAD COGNITIVE SYSTEM* en UNACEM (cemento).

## Consultas para el reporte

### IA generativa fuera del sector tecnología

El cruce más interesante para el post: qué empresas **no** tecnológicas piden IA.

```sql
SELECT p.rubro_inferido, p.nombre_empresa, p.nombre_puesto_estandarizado
FROM puestos p
WHERE p.rubro_inferido <> 'Tecnología'
  AND EXISTS (
    SELECT 1 FROM job_skills js
    JOIN skill_dictionary sd USING (skill_id)
    WHERE js.job_id = p.raw_id::text
      AND sd.ai_domain = 'Generative AI')
ORDER BY 1, 2;
```

### Habilidades de IA por nivel de puesto

¿La IA se pide en cargos junior o senior?

```sql
SELECT p.nivel_puesto,
       count(DISTINCT p.raw_id) FILTER (WHERE ia.job_id IS NOT NULL) AS con_ia,
       count(DISTINCT p.raw_id)                                      AS total
FROM puestos p
LEFT JOIN LATERAL (
    SELECT js.job_id FROM job_skills js
    JOIN skill_dictionary sd USING (skill_id)
    WHERE js.job_id = p.raw_id::text
      AND sd.ai_domain IN ('Generative AI','AI Agents','Machine Learning',
                           'Deep Learning','NLP','Computer Vision','MLOps')
    LIMIT 1
) ia ON TRUE
GROUP BY 1 ORDER BY 3 DESC;
```

### Trazabilidad: de la cifra al aviso original

Toda habilidad guarda la frase que la sustenta. Esto es lo que permite defender
cualquier número del reporte.

```sql
SELECT j.company, j.title, sd.canonical_skill,
       js.evidence, js.source_section
FROM job_skills js
JOIN skill_dictionary sd USING (skill_id)
JOIN jobs j USING (job_id)
WHERE sd.canonical_skill = 'RAG'
LIMIT 20;
```

### Estudios más solicitados

```sql
SELECT e.nivel_estudio, e.carrera_especialidad, count(*) AS veces
FROM estudios e
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20;
```

### Ciudades fuera de Lima

```sql
SELECT ciudad, count(*) AS ofertas
FROM puestos
WHERE ciudad NOT ILIKE '%lima%' AND ciudad <> ''
GROUP BY 1 ORDER BY 2 DESC;
```

Hay ofertas en Arequipa, Chiclayo, Trujillo, Piura, Ica, Cajamarca y Apurímac — el
estudio no es solo limeño.

## Verificación de integridad

Antes de publicar cualquier cifra, confirma que la limpieza corrió:

```sql
-- Las tres deben devolver 0
SELECT count(*) FROM job_skills js
  LEFT JOIN skill_dictionary sd USING (skill_id) WHERE sd.skill_id IS NULL;
SELECT count(*) FROM skill_dictionary sd
  LEFT JOIN job_skills js USING (skill_id) WHERE js.skill_id IS NULL;
SELECT count(*) FROM (
  SELECT canonical_skill FROM skill_dictionary
  GROUP BY 1 HAVING count(*) > 1) d;
```

## Limitaciones al citar

- **Foto, no tendencia.** Ofertas activas en agosto 2026. Sin serie histórica no se
  puede afirmar "creció X%".
- **Huecos por presupuesto.** Computer Vision (2.7%) y NLP (8.6%) están
  subrepresentados: las keywords `Computer Vision Engineer`, `NLP Engineer`,
  `Prompt Engineer`, `LLM Engineer` y `AI Product Manager` nunca se ejecutaron
  porque se agotó el crédito de Apify. **No concluyas que Perú no los demanda.**
- **Sueldos casi ausentes.** Los avisos peruanos rara vez publican rango salarial.
- **Sesgo de plataforma.** LinkedIn sobre-representa puestos formales de empresas
  medianas y grandes. Bodegas y pymes no publican ahí.
