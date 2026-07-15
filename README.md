# Agente IA Inmobiliario

Este proyecto es un scraper automatizado diseñado para extraer listados de propiedades (departamentos y casas) del portal Urbania.pe, filtrando automáticamente proyectos en construcción para obtener solo ofertas de reventa directas.

## Estructura del Proyecto

- `scrapper/`: Contiene la lógica para invocar al scraper de Apify (`orchestrator_apify.py`).
- `database/`: Define el esquema de la base de datos y modelos (`db.py`).
- `ingestion/`: Módulo encargado de procesar y cargar la data (`load_to_db.py`).
- `data/`: Contiene la base de datos SQLite (`real_estate.db`) con la data consolidada.

## Cómo ejecutar la demo

1. **Configuración:**
   - Asegúrate de tener configurado tu token de Apify en el archivo `.env`:
     ```
     APIFY_API_TOKEN=tu_token_aqui
     ```

2. **Ejecutar el pipeline completo:**
   - Para extraer la data y cargarla en la base de datos:
     ```bash
     .\.venv\Scripts\python.exe orchestrator_apify.py
     .\.venv\Scripts\python.exe load_to_db.py
     ```

3. **Resultados:**
   - Los resultados brutos de la extracción se guardan en `resultados_finales.json`.
   - La data procesada reside en `data/real_estate.db`.
