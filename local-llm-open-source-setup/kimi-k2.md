# Configurar Kimi K2 localmente

Guía paso a paso para correr **Kimi K2** (Moonshot AI) en local. No existe públicamente un modelo llamado "Kimi K3" al momento de escribir esto — esta guía asume que te refieres a **Kimi K2**. Si en el futuro Moonshot lanza una versión más nueva, los pasos aplican igual, solo hay que ajustar el nombre del modelo en los comandos.

## 1. Qué es Kimi K2

- Modelo de lenguaje open-weight de Moonshot AI (arquitectura Mixture-of-Experts).
- ~1 billón de parámetros totales, ~32B activos por token.
- Publicado en Hugging Face: `moonshotai/Kimi-K2-Instruct` (y variantes `-Base`, cuantizadas, etc.)
- Por su tamaño, correrlo "completo" en local requiere hardware de nivel servidor. Para un equipo personal, la opción realista es usar una **versión cuantizada** (GGUF) vía `llama.cpp` / `Ollama` / `LM Studio`.

## 2. Elegir la ruta según tu hardware

| Ruta | Hardware necesario | Dificultad |
|---|---|---|
| A. Cuantizada (GGUF) con Ollama / llama.cpp | GPU con 24–48GB VRAM (o CPU+RAM con paciencia), 200GB+ disco | Media |
| B. Full precision / multi-GPU | Varios GPUs datacenter (A100/H100), 800GB+ VRAM agregada | Alta (infra tipo servidor) |
| C. Nube/alquiler de GPU (RunPod, Lambda, Vast.ai) | Ninguno propio, solo presupuesto por hora | Baja |

Para "aprender a configurar un LLM local", la ruta recomendada es **A** con Ollama, porque es la más accesible y sigue siendo "local" en el sentido de correr en tu propia máquina.

## 3. Requisitos de infraestructura

### Ruta A — Cuantizada (recomendada para aprendizaje)
- **GPU:** NVIDIA con 24GB+ VRAM idealmente (RTX 4090, RTX 6000 Ada, etc.). Con menos VRAM se puede, pero con cuantizaciones más agresivas (Q2/Q3) y mucho más lento, o corriendo parcialmente en CPU.
- **RAM del sistema:** 64GB+ recomendado (para cargar capas que no caben en VRAM).
- **Disco:** 200–400GB libres, SSD recomendado (los pesos cuantizados de un modelo de 1T parámetros pesan cientos de GB incluso en 4-bit).
- **SO:** Linux o macOS (Apple Silicon con suficiente RAM unificada también sirve vía llama.cpp) o Windows con WSL2.
- **CUDA/drivers** actualizados si usas GPU NVIDIA.

### Ruta B — Full precision
- Múltiples GPUs de datacenter (ej. 8x H100 80GB) — no viable en un equipo personal típico.
- Se menciona solo como referencia; normalmente no aplica para "setup local" doméstico.

### Ruta C — Nube
- Solo necesitas conexión a internet y una cuenta en un proveedor (RunPod, Vast.ai, Lambda Labs, etc.).
- Costo por hora de GPU (ej. 1x A100 80GB ronda unos pocos dólares/hora).

## 4. Pasos — Instalación con Ollama (Ruta A, la más simple)

1. **Instalar Ollama**
   - macOS: descargar desde https://ollama.com/download
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows: instalador desde el sitio oficial.

2. **Verificar instalación**
   ```bash
   ollama --version
   ```

3. **Buscar si Kimi K2 está disponible en la librería de Ollama**
   ```bash
   ollama pull kimi-k2
   ```
   Si el nombre exacto no existe en la librería oficial, buscar en https://ollama.com/library o usar una versión cuantizada GGUF subida a Hugging Face (ver paso 6).

4. **Correr el modelo**
   ```bash
   ollama run kimi-k2
   ```
   Esto abre un chat interactivo en la terminal.

5. **Probar vía API local** (Ollama expone un servidor HTTP en `localhost:11434`)
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "kimi-k2",
     "prompt": "Hola, preséntate"
   }'
   ```

## 5. ¿Alternativa en venv (Python)?

Para Gemma 2 9B y DeepSeek-R1 Distill 14B (ver [gemma-2-9b.md](gemma-2-9b.md) y [deepseek-r1-distill-14b.md](deepseek-r1-distill-14b.md)) sí es recomendable usar un venv con `llama-cpp-python` como alternativa a Ollama. **Para Kimi K2 no cambia nada relevante**: el problema no es el método de instalación (Ollama vs. Python vs. binario), sino que los pesos cuantizados siguen pesando cientos de GB — eso no lo resuelve un entorno virtual. Un venv seguiría necesitando descargar y cargar en RAM/VRAM los mismos archivos gigantes, así que en la práctica solo tendría sentido en un servidor con la infraestructura de la sección 3 (ruta A o B), no en esta máquina.

## 6. Alternativa — llama.cpp directo (más control, más manual)

1. Clonar y compilar llama.cpp:
   ```bash
   git clone https://github.com/ggml-org/llama.cpp
   cd llama.cpp
   cmake -B build -DGGML_CUDA=ON   # quitar -DGGML_CUDA=ON si no hay GPU NVIDIA
   cmake --build build --config Release -j
   ```

2. Descargar los pesos GGUF cuantizados de Kimi K2 desde Hugging Face (buscar `Kimi-K2-Instruct-GGUF` de comunidades como `unsloth` o `bartowski`, que suelen publicar cuantizaciones de modelos grandes poco después del release oficial).

3. Correr el servidor:
   ```bash
   ./build/bin/llama-server -m ./models/Kimi-K2-Instruct-Q4_K_M.gguf --ctx-size 4096 -ngl 999
   ```
   - `-ngl` controla cuántas capas se descargan a GPU (ajustar según VRAM disponible).

## 7. Notas importantes sobre el tamaño del modelo

- Kimi K2 es uno de los modelos open-weight más grandes disponibles. Incluso en cuantización 4-bit, los pesos ocupan **cientos de GB**.
- Si tu hardware no alcanza, considera:
  - Usar una versión "lite" o destilada si Moonshot/la comunidad publica una.
  - Usar la Ruta C (GPU en la nube) solo para el aprendizaje inicial, sin comprar hardware.
  - Practicar el mismo flujo (Ollama, llama.cpp) primero con un modelo más chico (ej. Llama 3.1 8B, Mistral 7B) para entender el proceso, y luego escalar a Kimi K2 cuando tengas claro el setup y el hardware adecuado.

## 8. Checklist de infraestructura mínima realista

- [ ] GPU NVIDIA 24GB+ VRAM (o Mac con 64GB+ RAM unificada)
- [ ] 400GB de disco libre en SSD
- [ ] 64GB+ RAM del sistema
- [ ] Drivers CUDA actualizados (si aplica)
- [ ] Ollama o llama.cpp instalado
- [ ] Conexión a internet estable para la descarga inicial (puede ser de cientos de GB)

## 9. Referencias

- Ollama: https://ollama.com
- llama.cpp: https://github.com/ggml-org/llama.cpp
- Kimi K2 en Hugging Face: https://huggingface.co/moonshotai

## 10. Alternativa realista para esta máquina (Mac M4 Pro, 24GB RAM)

Con este hardware (chip Apple Silicon M4 Pro, 24GB de RAM unificada, ~494GB de disco libre), **Kimi K2 no es viable ni cuantizado** — requiere cientos de GB solo para los pesos. La RAM unificada de un Mac es compartida entre CPU y GPU, así que el límite real de "modelo que carga" ronda los 12–16GB de pesos (dejando margen para el sistema).

Modelos open source que sí corren bien acá vía Ollama:

| Modelo | Tamaño (parámetros) | RAM aprox. necesaria (cuantizado) | Notas |
|---|---|---|---|
| **Llama 3.1 8B** (Meta) | 8B | ~5–6GB | Buen balance calidad/velocidad, ideal para aprender el flujo |
| **Mistral 7B** | 7B | ~4–5GB | Rápido, liviano |
| **Qwen2.5 14B** (Alibaba) | 14B | ~9–10GB | Más capaz, sigue cabiendo cómodo en 24GB |
| **Gemma 2 9B** (Google) | 9B | ~6GB | Buena calidad para su tamaño |
| **Phi-3.5 mini** (Microsoft) | 3.8B | ~2–3GB | Muy liviano, útil para pruebas rápidas |
| **DeepSeek-R1 (distill 14B/32B)** | 14B–32B | ~9–20GB | El de 32B queda muy justo en 24GB; el de 14B es más seguro |

**Recomendación:** empezar con `llama3.1:8b` o `qwen2.5:14b` — ambos corren bien en esta Mac con Apple Silicon (que además tiene aceleración nativa para Metal en Ollama/llama.cpp).

Pasos (idénticos a la sección 4, solo cambia el nombre del modelo):

```bash
ollama pull llama3.1:8b
ollama run llama3.1:8b
```

o para algo más capaz pero todavía cómodo en 24GB:

```bash
ollama pull qwen2.5:14b
ollama run qwen2.5:14b
```

Esto te permite practicar exactamente el mismo ejercicio de configuración local (instalación, pull del modelo, chat, API HTTP) sin pelear con las limitaciones de infraestructura que tendría Kimi K2 en este equipo.
