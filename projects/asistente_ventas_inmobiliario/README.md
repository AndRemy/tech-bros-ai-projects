# Asistente de Ventas Inmobiliario

Bot conversacional que responde preguntas en lenguaje natural sobre disponibilidad de
departamentos, usando GenAI para entender la solicitud, construir la consulta contra la
base de datos y redactar la respuesta. Es agnóstico al canal: hoy soporta Telegram y
Discord, y se pueden agregar nuevos canales sin tocar el núcleo del bot.

Este proyecto es parte del portafolio `tech-bros-ai-projects` pero se instala y corre de
forma independiente — todo lo que necesitas está en esta carpeta.

## Arquitectura

Arquitectura hexagonal (puertos y adaptadores). El núcleo (`bot/core`) no sabe nada de
Telegram, Discord ni SQLite; solo conoce interfaces (`bot/adapters/base.py`,
`bot/core/session.py`, `bot/repository/apartments_repository.py`) que las piezas
concretas implementan.

Flujo de una consulta:

```
Canal (Telegram/Discord)
  -> ChannelAdapter        recibe y normaliza a IncomingMessage
  -> Orchestrator          coordina el pipeline y el estado de la conversación
  -> NLU (LLM #1)          texto -> intención + filtros estructurados
  -> QueryBuilder + Repository   filtros -> SQL parametrizado -> SQLite
  -> Ranking                relevancia a la descripción, luego fecha de publicación descendente
  -> Responder (LLM #2)     resultados -> 2-3 oraciones por opción
  -> ChannelAdapter          envía la respuesta al canal de origen
```

Decisiones de diseño relevantes:

- **El LLM nunca genera SQL directo.** El NLU produce un JSON de filtros validado contra
  un schema; el `QueryBuilder` es código determinista que arma la consulta parametrizada.
  Esto evita inyección/alucinación de columnas y hace la etapa testeable sin mockear un LLM.
- **Estado de conversación** vive detrás de la interfaz `SessionStore` (filtros activos,
  orden, página actual). La implementación en memoria alcanza para una sola instancia;
  cambiar a Redis u otro store no debería tocar el `Orchestrator`.
- **Errores con lenguaje amigable.** Cada etapa lanza excepciones de dominio
  (`bot/core/exceptions.py`); el `Orchestrator` las traduce a mensajes de plantilla fija
  (no generados por LLM, para seguir respondiendo aunque el proveedor de LLM esté caído) y
  loguea el error real para diagnóstico. Cero resultados no es un error, es una rama normal
  del flujo.
- **Paginación top-3.** Por defecto se ordena por relevancia a la descripción (cuántos
  filtros extraídos coincide cada fila) y luego por fecha de publicación descendente. El
  usuario puede pedir otro orden o pedir la siguiente página; ambas cosas reutilizan la
  sesión activa en vez de iniciar una búsqueda nueva.
- **Factory para elegir implementación según configuración.** `bot/repository/factory.py`
  decide qué `ApartmentsRepository` instanciar según el esquema de `DATABASE_URL`;
  `bot/adapters/factory.py` arma la lista de `ChannelAdapter` a partir de `ENABLED_CHANNELS`
  en `.env`; `bot/llm/factory.py` decide qué proveedor de LLM (`IntentExtractor` +
  `ResponseGenerator`) usar según `LLM_PROVIDER`. En los tres casos `main.py` solo conoce la
  interfaz — agregar un backend de base de datos, un canal o un proveedor de LLM nuevo es
  agregar una entrada al diccionario del factory correspondiente, sin tocar el resto del bot.

## Estructura

```
asistente_ventas_inmobiliario/
├── bot/                             # asistente conversacional
│   ├── main.py                      # entrypoint: arma las dependencias y arranca los adapters
│   ├── adapters/                    # un adapter por canal, todos implementan ChannelAdapter
│   │   ├── base.py
│   │   ├── factory.py               # ENABLED_CHANNELS -> lista de ChannelAdapter
│   │   ├── telegram_adapter.py      # expone create_from_env()
│   │   └── discord_adapter.py       # expone create_from_env()
│   ├── core/                        # lógica de negocio, sin dependencias de infraestructura
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── nlu.py                   # puerto IntentExtractor (sin SDK de ningún proveedor)
│   │   ├── ranking.py
│   │   ├── responder.py             # puerto ResponseGenerator + build_prompt compartido
│   │   ├── orchestrator.py
│   │   ├── exceptions.py
│   │   └── errors.py
│   ├── llm/                         # un archivo por proveedor de LLM
│   │   ├── factory.py               # LLM_PROVIDER -> (IntentExtractor, ResponseGenerator)
│   │   ├── anthropic_provider.py    # expone create_intent_extractor_from_env() / create_response_generator_from_env()
│   │   ├── openai_provider.py
│   │   └── gemini_provider.py
│   └── repository/
│       ├── factory.py               # DATABASE_URL -> ApartmentsRepository concreto
│       └── apartments_repository.py
├── scrapper/                        # extracción de listados desde Urbania.pe (Apify + Playwright)
│   ├── orchestrator_apify.py        # recorre distritos/operaciones vía Apify -> resultados_finales.json
│   ├── orchestrator.py              # variante propia con Playwright: crawler.py + urbania_scraper.py
│   ├── load_to_db.py                # carga resultados_finales.json a la tabla `apartments`
│   ├── load_*.py                    # cargas puntuales por lote (alquiler/venta, depto/casa)
│   └── DESIGN.md, GEMINI.md         # notas de diseño y bitácora del equipo de scraping
├── database/                        # esquema SQLModel (Property, DistrictStats) + engine
│   ├── db.py
│   └── models.py
├── ingestion/                       # ingesta on-demand: un link de Urbania -> fila en la base
│   └── ingestor.py
├── utils/                           # helpers compartidos por scrapper/database/ingestion
│   └── helpers.py
├── tests/
│   └── test_core.py
├── data/
│   └── real_estate.db               # SQLite local
├── requirements.txt
└── .env.example
```

## Estado actual / pendientes

El bot (`bot/`) ya está conectado y probado contra datos reales:
`bot/repository/apartments_repository.py` (`PostgresApartmentsRepository`) lee la tabla
`apartments` de un Postgres administrado en Neon — 654 filas confirmadas, con columnas
`id, zona, precio, habitaciones, banos, area_m2, amenities, fecha_publicacion, descripcion,
url, operacion, tipo`. Filtros, ranking y paginación fueron verificados end-to-end contra esa
base (sin mockear el schema).

Pendientes conocidos:

- **`url` es NULL en ~98% de las filas** (644/654) — son las cargadas por los loaders
  manuales (`scrapper/load_*.py`), que pegan listados sin URL real; solo las filas cargadas
  vía Apify (`load_to_db.py`) tienen `url`. Ya está modelado como opcional en
  `bot/core/models.py`; el bot simplemente omite el link cuando no existe.
- **El pipeline de ingesta on-demand (`ingestion/ingestor.py` + `database/db.py`) no escribe
  a la misma base que usa el bot.** Usa SQLModel contra `data/real_estate.db` (SQLite local)
  con tablas `Property`/`DistrictStats`, un esquema distinto al `apartments` de Postgres. Si
  se quiere que la ingesta on-demand alimente al bot, hay que decidir si conviene apuntarla a
  Postgres y al esquema `apartments`, o mantenerla como un pipeline aparte.
- **Credenciales de Telegram/Discord**: los adapters están escritos contra las interfaces
  de `python-telegram-bot` y `discord.py`, pero necesitan un bot token para correr.
- **Proveedor de LLM**: `bot/llm/` soporta Anthropic, OpenAI y Gemini (`LLM_PROVIDER` en
  `.env`) — falta la API key del que vayan a usar. **Ninguno de los tres se probó todavía
  contra una API real** (no había ninguna key disponible en esta sesión); las tres
  implementaciones están escritas y validadas contra la documentación/SDK de cada proveedor
  (construcción de clientes, forma de las respuestas), pero conviene probar cada una con una
  pregunta simple antes de confiar en ellas en producción. Nota: el SDK `google-generativeai`
  está deprecado (el propio paquete lo advierte al importarlo) — `gemini_provider.py` ya usa
  el reemplazo oficial, `google-genai`.

## Instalación

```bash
cd projects/asistente_ventas_inmobiliario
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium  # solo si vas a correr scrapper/crawler.py o urbania_scraper.py
cp .env.example .env  # completar con credenciales reales
```

## Correr el bot

Los canales activos se listan en `ENABLED_CHANNELS` dentro de `.env` (ej.
`ENABLED_CHANNELS=telegram,discord`); el bot corre todos los que estén en esa lista al
mismo tiempo, cada uno con su propio token (`TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, ...).
El proveedor de LLM se elige con `LLM_PROVIDER=anthropic|openai|gemini`; solo hace falta la
API key de ese proveedor (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` o `GEMINI_API_KEY`).

```bash
python -m bot.main
```

## Correr el pipeline de scraping / ETL

Los scripts de `scrapper/`, `database/`, `ingestion/` y `tests/` asumen que se ejecutan
con el directorio de trabajo en la raíz del proyecto (`projects/asistente_ventas_inmobiliario/`),
igual que el bot, para que los imports (`from database.db import ...`, `from scrapper...`,
`from utils.helpers import ...`) resuelvan correctamente:

```bash
cd projects/asistente_ventas_inmobiliario

# Extracción vía Apify (requiere APIFY_API_TOKEN en .env) + carga a `apartments`
cd scrapper && python orchestrator_apify.py && python load_to_db.py && cd ..

# Ingesta on-demand de un link individual (usa database/ + tablas Property/DistrictStats)
python -c "from ingestion.ingestor import ingest_property_link; ingest_property_link('https://urbania.pe/...')"

# Tests
pytest tests/
```
