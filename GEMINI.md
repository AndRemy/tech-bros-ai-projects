# Agente IA Inmobiliario - Información del Proyecto

Este archivo contiene información sobre convenciones, arquitectura y configuración compartida del equipo.

## Repositorio de Colaboración
El proyecto se encuentra alojado en GitHub para la colaboración entre miembros del equipo:
https://github.com/AndRemy/tech-bros-ai-projects

## Historial de Cambios
- **14/07/2026**:
    - Ajuste de alcance: Solo **scraping** y **base de datos**.
    - Corrección scraper: Se arregló integración `playwright-stealth`.
    - Integración Apify: Implementación exitosa de `sian.agency/urbania-property-scraper` para sortear bloqueo de Cloudflare.
    - Automatización: Script `orchestrator_apify.py` recorre distritos automáticamente.
    - ETL: Script `load_to_db.py` mapea y carga 300 propiedades a SQLite según esquema del repo.
    - Demo: Repositorio preparado y documentado para entrega.
