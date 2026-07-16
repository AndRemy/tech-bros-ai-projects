# Diseño y Arquitectura: Agente IA Inmobiliario

Este documento detalla la visión del producto, la arquitectura técnica y el plan de implementación para el **Agente IA Inmobiliario**, concebido como un copiloto de mercado para el sector inmobiliario en el Perú.

## 🎯 Visión del Producto

**"El primer agente inmobiliario para Perú que razona sobre el mercado."**

A diferencia de los buscadores tradicionales (Urbania, Adondevivir) que solo filtran listas de propiedades, este agente actúa como un **copiloto consultor** para el comprador. No se limita a responder "¿Qué departamentos hay?", sino que ayuda a responder:

* ¿Qué departamentos están subvalorados u ofrecen una verdadera oportunidad de inversión?
* ¿Cuáles están sobrevalorados en comparación con el promedio real de la zona (m²)?
* ¿La descripción del anuncio coincide con la realidad de las fotos o tiene inconsistencias?
* ¿Qué distrito o zona ofrece un mejor retorno o precio promedio por m² según el presupuesto?

---

## 🏗️ Arquitectura de Software

La arquitectura propuesta aprovecha la agilidad de un canal conversacional ligero (Telegram) conectado a un backend robusto de análisis y extracción de datos.

```
                  Usuario
                     │ (Mensaje en Lenguaje Natural / Link)
                     ▼
               Telegram Bot
                     │ (Webhooks)
                     ▼
                  FastAPI
                     │
                 Agente IA ◄──► LLM (Gemini / Claude con Tool Calling)
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Base de Datos  MCP Browser    Embeddings (Vector DB)
(SQLite / PG)  + Playwright    (Búsqueda semántica)
```

### Componentes Clave

1. **Frontend / Canal:** **Telegram Bot**. Ideal para demostraciones interactivas (vídeos de 30-60 segundos para LinkedIn) por su nulo costo de API oficial, rapidez de configuración y alta capacidad multimedia (tablas, negritas, links).
2. **Backend:** **FastAPI**. API asíncrona de alto rendimiento en Python, ideal para interactuar con webhooks de Telegram y orquestar las llamadas a LLMs.
3. **Agente IA:** Motor de razonamiento basado en LLM con capacidades de **Tool Calling** (llamada a funciones) para interactuar con la base de datos y herramientas de navegación.
4. **Scraping / Extracción:** Integración de **Playwright** y **MCP Browser** para extraer información en tiempo real de anuncios provistos por el usuario o actualizar listados.
5. **Base de Datos (Data Store):**
   - **Relacional:** SQLite (para MVP) o PostgreSQL (producción) que guarde propiedades recopiladas, estadísticas por distrito y promedios por m².
   - **Vectorial:** Para almacenamiento y búsqueda semántica de anuncios y descripciones complejas.

---

## 📈 Casos de Uso del MVP (Para Demo de LinkedIn)

1. **Análisis de Oportunidad por Link:** El usuario pega un enlace de Urbania/Adondevivir y el bot extrae la info usando Playwright, calcula el precio por m² y le dice: *"Este departamento está 10.5% por debajo del promedio en Miraflores. Es una buena oportunidad."*
2. **Búsqueda Semántica & Razonamiento:** *"Busco algo en Surco por $180k con 3 dorms."* El bot no solo lista opciones, sino que analiza y justifica: *"Te recomiendo este en la zona X porque su m² está mejor valorado que el promedio y tiene excelente conectividad."*
3. **Estadísticas Comparativas:** *"¿Qué distrito tiene el m² más barato entre Miraflores, San Isidro y Barranco?"* El bot muestra una tabla comparativa con datos consolidados de la base de datos.
4. **Detector de Descripciones Engañosas o Anomalías:** El agente analiza el texto y datos de una propiedad para alertar si el precio no corresponde a la realidad del mercado o si la descripción promete cosas incoherentes con los metrajes.
