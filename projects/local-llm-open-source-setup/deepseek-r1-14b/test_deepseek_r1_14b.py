"""Prueba rápida de DeepSeek-R1 Distill Qwen 14B vía llama-cpp-python.

Uso:
    source .venv/bin/activate
    python projects/local-llm-open-source-setup/deepseek-r1-14b/test_deepseek_r1_14b.py
"""

from pathlib import Path

from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"

PROMPTS = [
    "Resuelve: 17 * 24, muestra tu razonamiento",
    "Si un tren sale a las 14:00 a 80km/h y otro sale 30 minutos después a 100km/h "
    "en la misma dirección, ¿a qué hora lo alcanza? Explica el razonamiento paso a paso.",
]


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(f"No se encontró el modelo en {MODEL_PATH}")

    llm = Llama(model_path=str(MODEL_PATH), n_ctx=4096, n_gpu_layers=-1, verbose=False)

    for prompt in PROMPTS:
        print(f"\n{'=' * 80}\nPrompt: {prompt}\n{'-' * 80}")
        respuesta = llm.create_chat_completion(messages=[{"role": "user", "content": prompt}])
        print(respuesta["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
