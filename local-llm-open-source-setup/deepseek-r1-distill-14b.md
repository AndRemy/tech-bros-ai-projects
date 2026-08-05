# Configurar DeepSeek-R1 Distill 14B localmente

Guía paso a paso para instalar y probar **DeepSeek-R1 Distill Qwen 14B** en local usando Ollama.

## 1. Qué es DeepSeek-R1 Distill 14B

- No es el modelo DeepSeek-R1 completo (ese es un MoE de cientos de miles de millones de parámetros, no viable en local doméstico).
- Es una versión **destilada**: el conocimiento y las capacidades de razonamiento de R1 se transfirieron a un modelo base más chico (Qwen2.5 14B), entrenándolo para imitar las cadenas de razonamiento de R1.
- Buen desempeño en tareas de razonamiento, matemáticas y lógica en relación a su tamaño.
- Licencia open source (Apache 2.0 / MIT según el modelo base).
- Publicado en Hugging Face: `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` y disponible en la librería de Ollama.

## 2. Requisitos de infraestructura

| Recurso | Mínimo | Recomendado |
|---|---|---|
| RAM / VRAM | 10GB | 16GB+ |
| Disco | 12GB libres | 20GB libres |
| CPU/GPU | CPU moderna (funciona sin GPU, más lento) | GPU o Apple Silicon para mejor velocidad |
| SO | macOS, Linux, Windows (WSL2) | — |

**Esta máquina (Mac M4 Pro, 24GB RAM):** ✅ compatible. El modelo cuantizado ocupa ~9GB en RAM, dejando margen razonable para el sistema operativo y otras apps abiertas.

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
   ollama pull deepseek-r1:14b
   ```
   Esto descarga la versión distill 14B cuantizada (Q4_K_M, ~9GB).

4. **Correr el modelo en modo chat interactivo**
   ```bash
   ollama run deepseek-r1:14b
   ```

5. **Probar con un prompt de razonamiento** (donde este modelo destaca)
   ```bash
   ollama run deepseek-r1:14b "Si un tren sale a las 14:00 a 80km/h y otro sale 30 minutos después a 100km/h en la misma dirección, ¿a qué hora lo alcanza? Explica el razonamiento paso a paso."
   ```
   Vas a notar que el modelo muestra su cadena de razonamiento (thinking) antes de dar la respuesta final — esa es la característica heredada de R1.

6. **Probar vía API HTTP local**
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "deepseek-r1:14b",
     "prompt": "Resuelve: 17 * 24, muestra tu razonamiento"
   }'
   ```

## 4. Variantes útiles según hardware

- `ollama pull deepseek-r1:7b` — versión más chica (Qwen 7B destilado), más rápida, ~4.5GB.
- `ollama pull deepseek-r1:32b` — versión más grande (32B, ~20GB), técnicamente cabe en 24GB de RAM pero deja muy poco margen para el resto del sistema; no recomendado correr junto con otras apps pesadas.
- `ollama pull deepseek-r1:1.5b` — versión mínima, útil solo para pruebas rápidas de flujo, calidad limitada.

## 5. Alternativa: instalar y correr en un entorno virtual (venv) de Python

Ollama no se instala "dentro" de un venv — es un binario/servicio del sistema. Si preferís un enfoque 100% Python, aislado en un venv y fácil de versionar en `requirements.txt`, podés usar `llama-cpp-python` para cargar directamente el mismo archivo GGUF cuantizado.

**Recomendable cuando** vas a integrar el modelo en un script/notebook de Python, o querés mantener el setup dentro del repo del proyecto. **No es necesario** si solo querés probarlo por chat — ahí Ollama (sección 3) es más simple.

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
   En Linux con GPU NVIDIA, usar `CMAKE_ARGS="-DGGML_CUDA=on"`. Sin GPU, se puede correr en CPU (más lento, pero funcional).

3. **Descargar el archivo GGUF cuantizado** desde Hugging Face (ej. desde `bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF`)
   ```bash
   pip install huggingface_hub
   huggingface-cli download bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf --local-dir ./models
   ```

4. **Probar el modelo con un script simple** (mostrando la cadena de razonamiento)
   ```python
   from llama_cpp import Llama

   llm = Llama(model_path="./models/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf", n_ctx=4096, n_gpu_layers=-1)
   respuesta = llm.create_chat_completion(
       messages=[{"role": "user", "content": "Resuelve: 17 * 24, muestra tu razonamiento"}]
   )
   print(respuesta["choices"][0]["message"]["content"])
   ```

5. **(Opcional) Levantar un servidor HTTP compatible con la API de OpenAI**, sin depender de Ollama
   ```bash
   pip install 'llama-cpp-python[server]'
   python3 -m llama_cpp.server --model ./models/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf --n_gpu_layers -1
   ```
   Servidor disponible en `http://localhost:8000` con endpoints tipo `/v1/chat/completions`.

6. **Desactivar el venv al terminar**
   ```bash
   deactivate
   ```

## 6. Checklist

- [ ] Ollama instalado y verificado
- [ ] `ollama pull deepseek-r1:14b` ejecutado sin errores
- [ ] Chat interactivo probado con `ollama run deepseek-r1:14b`
- [ ] Prompt de razonamiento probado y cadena de pensamiento visible
- [ ] Llamada API vía `curl` respondiendo correctamente

## 7. Referencias

- Ollama library: https://ollama.com/library/deepseek-r1
- Modelo en Hugging Face: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
- Paper de DeepSeek-R1: https://arxiv.org/abs/2501.12948
