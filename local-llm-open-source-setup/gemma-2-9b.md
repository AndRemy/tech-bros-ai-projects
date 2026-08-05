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

## 5. Alternativa: instalar y correr en un entorno virtual (venv) de Python

Ollama en sí **no** es un paquete de Python — es un binario/servicio del sistema, así que no se instala "dentro" de un venv. Pero si preferís un enfoque 100% Python (aislado, reproducible, sin instalar un servicio a nivel de sistema), podés usar `llama-cpp-python`, que sí es instalable vía pip y carga directamente los mismos archivos GGUF cuantizados.

**Es recomendable cuando:**
- Querés que todo el setup viva dentro del proyecto/repo (útil para reproducibilidad o para versionar dependencias en `requirements.txt`).
- Vas a integrar el modelo en un script o notebook de Python en vez de usarlo solo por chat/CLI.

**No es necesario si** solo querés probar el modelo por chat — ahí Ollama (sección 3) es más simple.

### Pasos

1. **Crear y activar el venv**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar `llama-cpp-python`** (con aceleración Metal en Apple Silicon)
   ```bash
   CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
   ```
   En Linux con GPU NVIDIA, usar `CMAKE_ARGS="-DGGML_CUDA=on"` en su lugar. Sin GPU, se puede omitir `CMAKE_ARGS` y correr en CPU (más lento).

3. **Descargar el archivo GGUF cuantizado** directamente desde Hugging Face (ej. desde `bartowski/gemma-2-9b-it-GGUF`)
   ```bash
   pip install huggingface_hub
   huggingface-cli download bartowski/gemma-2-9b-it-GGUF gemma-2-9b-it-Q4_K_M.gguf --local-dir ./models
   ```

4. **Probar el modelo con un script simple**
   ```python
   from llama_cpp import Llama

   llm = Llama(model_path="./models/gemma-2-9b-it-Q4_K_M.gguf", n_ctx=4096, n_gpu_layers=-1)
   respuesta = llm.create_chat_completion(
       messages=[{"role": "user", "content": "Explícame qué es un modelo de lenguaje en dos frases"}]
   )
   print(respuesta["choices"][0]["message"]["content"])
   ```

5. **(Opcional) Levantar un servidor HTTP compatible con la API de OpenAI**, sin depender de Ollama
   ```bash
   pip install 'llama-cpp-python[server]'
   python3 -m llama_cpp.server --model ./models/gemma-2-9b-it-Q4_K_M.gguf --n_gpu_layers -1
   ```
   Esto expone un servidor en `http://localhost:8000` con endpoints compatibles con la API de OpenAI (`/v1/chat/completions`, etc.).

6. **Desactivar el venv al terminar**
   ```bash
   deactivate
   ```

## 6. Checklist

- [ ] Ollama instalado y verificado
- [ ] `ollama pull gemma2:9b` ejecutado sin errores
- [ ] Chat interactivo probado con `ollama run gemma2:9b`
- [ ] Llamada API vía `curl` respondiendo correctamente

## 7. Referencias

- Ollama library: https://ollama.com/library/gemma2
- Modelo en Hugging Face: https://huggingface.co/google/gemma-2-9b-it
- Licencia de uso: https://ai.google.dev/gemma/terms
