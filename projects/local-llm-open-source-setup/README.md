# Configurar modelos LLM open source localmente

Ejercicio práctico para aprender a instalar y probar modelos de lenguaje open source en local, usando esta máquina (Mac Apple M4 Pro, 24GB RAM unificada, ~494GB disco libre) como entorno de referencia.

## Manuales disponibles

| Manual | Modelo | Tamaño | RAM aprox. necesaria | Compatible con esta máquina |
|---|---|---|---|---|
| [kimi-k2.md](kimi-k2/README.md) | Kimi K2 (Moonshot AI) | ~1T parámetros (32B activos) | Cientos de GB | ❌ No — solo como referencia teórica |
| [gemma-2-9b.md](gemma-2-9b/README.md) | Gemma 2 9B (Google) | 9B | ~6GB | ✅ Sí |
| [deepseek-r1-14b.md](deepseek-r1-14b/README.md) | DeepSeek-R1 Distill 14B | 14B | ~9–10GB | ✅ Sí |

## Recomendación de orden

1. Empezar con **Gemma 2 9B** — el más liviano, ideal para aprender el flujo completo (instalación, pull, chat, API).
2. Continuar con **DeepSeek-R1 Distill 14B** — más capaz, especialmente bueno en razonamiento, todavía cómodo en 24GB de RAM.
3. Leer el manual de **Kimi K2** como referencia de qué implica escalar a un modelo de nivel datacenter (aunque no sea ejecutable en esta máquina).

Cada manual es independiente y contiene: qué es el modelo, requisitos de infraestructura, pasos de instalación con Ollama, cómo probarlo vía chat y API HTTP local, y una **alternativa en entorno virtual (venv) de Python** con `llama-cpp-python` para quienes prefieran un setup aislado dentro del proyecto en vez del servicio de sistema de Ollama (ver sección correspondiente en `gemma-2-9b.md` y `deepseek-r1-14b.md`; en `kimi-k2.md` se explica por qué el venv no resuelve el problema de tamaño en ese caso).
