"""Corrige `puestos.nivel_puesto` derivándolo del título, sin usar la API.

El LLM resultó poco fiable en esta dimensión: manda `JEFE DE DATA E IA` a Gerencia
pese a una regla explícita en el prompt, y `Especialista` absorbe el 53% de los
puestos. Cuando el título nombra el nivel, una regla determinista acierta el 100%.

Filosofía: el regex **solo pisa** al LLM cuando hay señal clara en el título
(palabra de jerarquía, o marca de seniority sin palabra de jerarquía). Si el título
no dice nada —"Data Engineer", "AI Specialist"— se respeta lo que infirió el modelo,
que es justo donde sí aporta.

    python nivel_desde_titulo.py            # previsualiza y mide el acierto
    python nivel_desde_titulo.py --apply    # corrige
"""

import argparse
import collections
import os
import re
import unicodedata

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# Orden = precedencia. La jerarquía gana sobre la marca de seniority: en
# "Senior AI-Native Engineering Lead" manda "Lead" (Jefatura), no "Senior".
JERARQUIA = [
    ("Direccion", r"\bdirector(a|es)?\b|\bchief\b|\bC[TIDEO]O\b|\bVP\b|vicepresident"),
    ("Gerencia",  r"\bgerente\b|\bgerencia\b|\bmanager\b|\bhead of\b|\bhead\b(?!\s*count)"),
    ("Jefatura",  r"\bjefe\b|\bjefa\b|\bjefatura\b|\bl[ií]der\b|\blead\b|\bleader\b|"
                  r"\bsupervisor(a)?\b|\bcoordinador(a)?\b|\bencargad[oa]\b"),
    ("Practicante", r"\bpracticante\b|\bpr[áa]cticas\b|\bintern\b|\binternship\b|"
                    r"\btrainee\b|\bbecari[oa]\b|\baprendiz\b"),
    ("Asistente", r"\basistente\b|\bauxiliar\b|\bassistant\b|\bapoyo\b"),
    ("Analista",  r"\banalista\b|\banalyst\b"),
    ("Especialista", r"\bespecialista\b|\bspecialist\b|\bexperto\b"),
]

# Solo se consultan si el título NO trae palabra de jerarquía.
SENIORITY = [
    ("Analista", r"\bjr\b|\bjunior\b|\bjuniors\b|\bi\b(?=\s*$)"),
    ("Especialista", r"\bsr\b|\bsenior\b|\bstaff\b|\bprincipal\b|\bexpert\b|"
                     r"\bespecializad[oa]\b|\biii\b"),
]

JERARQUIA_RX = [(n, re.compile(p, re.I)) for n, p in JERARQUIA]
SENIORITY_RX = [(n, re.compile(p, re.I)) for n, p in SENIORITY]


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def nivel_de(titulo: str) -> tuple[str | None, str]:
    """Devuelve (nivel, motivo). nivel es None si el título no da señal."""
    if not titulo:
        return None, ""
    # Se evalúa con y sin tildes: los avisos escriben "lider" tanto como "líder".
    variantes = (titulo, sin_tildes(titulo))
    for nombre, rx in JERARQUIA_RX:
        for v in variantes:
            m = rx.search(v)
            if m:
                return nombre, f"jerarquía: '{m.group(0)}'"
    for nombre, rx in SENIORITY_RX:
        for v in variantes:
            m = rx.search(v)
            if m:
                return nombre, f"seniority: '{m.group(0)}'"
    return None, ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el .env")

    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nombre_puesto_original, nivel_puesto FROM puestos")
        filas = cur.fetchall()

        cambios, sin_senal, ya_ok = [], 0, 0
        for pid, titulo, actual in filas:
            nivel, motivo = nivel_de(titulo or "")
            if nivel is None:
                sin_senal += 1
            elif nivel == actual:
                ya_ok += 1
            else:
                cambios.append((pid, titulo, actual, nivel, motivo))

        print(f"puestos                    : {len(filas)}")
        print(f"  el LLM ya acertaba       : {ya_ok}")
        print(f"  se corrigen              : {len(cambios)}")
        print(f"  sin señal (se respeta LLM): {sin_senal}")

        matriz = collections.Counter((c[2], c[3]) for c in cambios)
        print("\n=== correcciones por tipo ===")
        for (antes, despues), n in matriz.most_common(12):
            print(f"  {n:>4}  {antes:<16} → {despues}")

        print("\n=== ejemplos ===")
        for _, t, antes, despues, motivo in cambios[:14]:
            print(f"  {antes:<14} → {despues:<13} {t[:44]:<44} [{motivo}]")

        print("\n=== distribución resultante ===")
        final = collections.Counter()
        for pid, titulo, actual in filas:
            nivel, _ = nivel_de(titulo or "")
            final[nivel or actual] += 1
        for niv, n in final.most_common():
            print(f"  {n:>4} ({100*n/len(filas):4.1f}%)  {niv}")

        if not args.apply:
            print("\n[previsualización] Nada se modificó. Usa --apply para corregir.")
            return

        for pid, _, _, nivel, _ in cambios:
            cur.execute("UPDATE puestos SET nivel_puesto = %s WHERE id = %s", (nivel, pid))
        conn.commit()
        print(f"\nActualizados: {len(cambios)} puestos")


if __name__ == "__main__":
    main()
