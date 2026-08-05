# Configurar Gemma 2 9B localmente

Guía paso a paso para instalar y probar **Gemma 2 9B** (Google) en local usando Ollama.

## 1. Qué es Gemma 2 9B

- Modelo de lenguaje open-weight de Google, familia Gemma 2.
- 9 mil millones de parámetros — tamaño mediano, buena calidad para su peso.
- Licencia propia de Google (Gemma Terms of Use), permite uso comercial y de investigación con restricciones específicas — revisar la licencia antes de uso productivo.
- Publicado en Hugging Face: `google/gemma-2-9b-it` (versión instruct/chat) y disponible directamente en la librería de Ollama.

## 2. Requisitos de infraestructura

| Recurso | Mínimo | Recomendado |
|---|---|---|
| RAM / VRAM | 8GB | 16GB+ |
| Disco | 10GB libres | 15GB libres |
| CPU/GPU | CPU moderna (funciona sin GPU) | GPU o Apple Silicon para mejor velocidad |
| SO | macOS, Linux, Windows (WSL2) | — |

**Esta máquina (Mac M4 Pro, 24GB RAM):** ✅ compatible sin problema. El modelo cuantizado ocupa ~5.5–6GB en RAM, dejando margen amplio para el sistema.

## 3. Pasos de instalación con Ollama

1. **Instalar Ollama** (si no lo tienes ya)
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
   En macOS también puedes descargar el instalador desde https://ollama.com/download

2. **Verificar instalación**
   ```bash
   ollama --version
   ```

3. **Descargar el modelo**
   ```bash
   ollama pull gemma2:9b
   ```
   Esto descarga la versión cuantizada por defecto (Q4_0, ~5.5GB).

4. **Correr el modelo en modo chat interactivo**
   ```bash
   ollama run gemma2:9b
   ```

5. **Probar vía API HTTP local**
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "gemma2:9b",
     "prompt": "Explícame qué es un modelo de lenguaje en dos frases"
   }'
   ```

6. **Salir del chat interactivo**
   ```
   /bye
   ```

## 4. Variantes útiles

- `ollama pull gemma2:2b` — versión más chica (2B), útil si quieres algo aún más rápido para pruebas.
- `ollama pull gemma2:27b` — versión más grande (27B, ~15GB), viable en esta máquina pero con menos margen de RAM libre para otras apps.

## 5. Checklist

- [ ] Ollama instalado y verificado
- [ ] `ollama pull gemma2:9b` ejecutado sin errores
- [ ] Chat interactivo probado con `ollama run gemma2:9b`
- [ ] Llamada API vía `curl` respondiendo correctamente

## 6. Referencias

- Ollama library: https://ollama.com/library/gemma2
- Modelo en Hugging Face: https://huggingface.co/google/gemma-2-9b-it
- Licencia de uso: https://ai.google.dev/gemma/terms
