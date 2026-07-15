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

## Estructura

```
asistente_ventas_inmobiliario/
├── bot/
│   ├── main.py                     # entrypoint: arma las dependencias y arranca los adapters
│   ├── adapters/                   # un adapter por canal, todos implementan ChannelAdapter
│   │   ├── base.py
│   │   ├── telegram_adapter.py
│   │   └── discord_adapter.py
│   ├── core/                       # lógica de negocio, sin dependencias de infraestructura
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── nlu.py
│   │   ├── ranking.py
│   │   ├── responder.py
│   │   ├── orchestrator.py
│   │   ├── exceptions.py
│   │   └── errors.py
│   └── repository/
│       └── apartments_repository.py
├── database/                       # a cargo del equipo de scraping/datos
├── scrapper/                       # a cargo del equipo de scraping/datos
├── requirements.txt
└── .env.example
```

## Estado actual / pendientes

Este es el scaffolding de la arquitectura: interfaces y modelos están completos y
tipados; las piezas que dependen de infraestructura externa están marcadas con `TODO`
porque faltan detalles que no dependen de este equipo:

- **Schema de la base de datos**: `ApartmentsRepository` asume una tabla `apartments` con
  columnas razonables (`zona`, `precio`, `habitaciones`, `fecha_publicacion`, ...). Hay que
  ajustar `bot/repository/apartments_repository.py` cuando el equipo de datos confirme el
  schema real y la cadena de conexión a la base SQLite en la nube.
- **Credenciales de Telegram/Discord**: los adapters están escritos contra las interfaces
  de `python-telegram-bot` y `discord.py`, pero necesitan un bot token para correr.
- **Proveedor de LLM**: `nlu.py` y `responder.py` dependen de una interfaz `LLMClient`
  (`bot/core/nlu.py`); falta decidir y cablear el proveedor (Anthropic, OpenAI, etc.) y su
  API key.

## Instalación

```bash
cd projects/asistente_ventas_inmobiliario
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar con credenciales reales
```

## Correr el bot

```bash
python -m bot.main
```
