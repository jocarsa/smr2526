#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Explica el contenido de cada carpeta (recursivamente) usando Ollama.

Nueva lógica solicitada:
1) Jerarquía: curso → asignatura (módulo profesional) → unidad didáctica → subunidad didáctica.
2) Sólo cuando la carpeta actual corresponda a una "subunidad didáctica":
     - Crear subcarpeta "001-Contenidos básicos"
     - Dentro, "Contenidos básicos.md"
     - No sobrescribir si ya existe con contenido (sí si está vacío).
     - ADICIONAL: Si el archivo existe pero tiene el marcador por defecto
       "# Contenidos básicos\n\nEscribe aquí los contenidos esenciales."
       o menos de MIN_CHARS_BASICO caracteres, se considera "vacío" y se genera texto.
3) En cualquier otro caso (curso, asignatura, unidad didáctica, u otros apartados):
     - Crear en la carpeta actual un archivo "000-Resumen.md" (sin subcarpeta)
     - No sobrescribir si ya existe con contenido (sí si está vacío).
     - ADICIONAL: Nunca crear "000-Resumen.md" en carpetas
       "002-Ejercicios", "003-Criterios de evaluación" o "003-Criterios de evaluacion".

Estilo:
- EXACTAMENTE 10 párrafos, prosa, tono literario y didáctico.
- Sin títulos, sin listas, sin código.
- Agnóstico de tecnología (no nombrar lenguajes/herramientas).
- Sin referencias explícitas a otras carpetas/archivos.

Requisitos:
  - Python 3.8+
  - requests  (pip install requests)
  - Ollama en ejecución (http://localhost:11434) con modelo descargado
    (p. ej. `ollama pull qwen2.5-coder:7b`)

Uso:
  python3 explica_carpetas_con_ollama.py
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Iterable, Tuple
import requests

# ---------------------- CONFIGURACIÓN ----------------------

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.2"))
NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "65536"))

# Excluir directorios en cualquier nivel
EXCLUDE_DIRS = {
    ".git",
    # Invisibles para el cómputo
    "101-Ejercicios",
    "201-Criterios de evaluación",
    "201-Criterios de evaluacion",  # sin tilde
    # añade aquí p.ej. "node_modules", ".venv", "dist", "build", "moodledata", etc.
}

# Bloqueos específicos para NO crear 000-Resumen.md
BLOCK_RESUMEN_DIRNAMES = {
    "002-Ejercicios",
    "003-Criterios de evaluación",
    "003-Criterios de evaluacion",  # sin tilde
}

# Pausa entre peticiones
SLEEP_BETWEEN_REQUESTS = float(os.environ.get("OLLAMA_SLEEP", "0.5"))

# Nombres de salida
OUTPUT_SUBFOLDER = "001-Contenidos básicos"
OUTPUT_BASICO = "Contenidos básicos.md"
OUTPUT_RESUMEN = "000-Resumen.md"

# Heurística de "contenido suficiente" para Contenidos básicos
MIN_CHARS_BASICO = int(os.environ.get("MIN_CHARS_BASICO", "120"))
BASICO_PLACEHOLDER = "# Contenidos básicos\n\nEscribe aquí los contenidos esenciales.".strip()

# ---------------------- UTILIDADES ----------------------


def is_excluded_dir(path: Path) -> bool:
    return path.name in EXCLUDE_DIRS


def build_tree(root: Path) -> str:
    """Construye un árbol de texto del directorio `root`, excluyendo carpetas en EXCLUDE_DIRS."""
    lines: List[str] = [root.name + "/"]

    def _walk(dir_path: Path, prefix: str = ""):
        try:
            entries = sorted(
                (e for e in dir_path.iterdir() if not (e.is_dir() and is_excluded_dir(e))),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            return

        total = len(entries)
        for i, entry in enumerate(entries):
            connector = "└── " if i == total - 1 else "├── "
            lines.append(prefix + connector + entry.name + ("/" if entry.is_dir() else ""))
            if entry.is_dir():
                if is_excluded_dir(entry):
                    continue
                extension = "    " if i == total - 1 else "│   "
                _walk(entry, prefix + extension)

    _walk(root)
    return "\n".join(lines)


def iter_all_subdirs(root: Path) -> Iterable[Path]:
    """Itera todas las subcarpetas bajo `root` (recursivo), aplicando exclusiones."""
    for dirpath, dirnames, _filenames in os.walk(root):
        # Filtra in-place para que os.walk no entre en las excluidas
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for d in dirnames:
            yield Path(dirpath) / d


def chat_ollama(model: str, system: str, user: str) -> str:
    """Llama a /api/chat de Ollama con mensajes system+user y devuelve el contenido."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "message" in data and "content" in data["message"]:
        return data["message"]["content"].strip()
    return json.dumps(data, ensure_ascii=False, indent=2)


def label_for_depth(depth: int) -> str:
    """Etiqueta semántica según profundidad relativa al directorio base."""
    if depth == 1:
        return "curso"
    if depth == 2:
        return "asignatura"  # alias de "módulo profesional"
    if depth == 3:
        return "unidad didáctica"
    if depth == 4:
        return "subunidad didáctica"
    return "apartado"


def depth_relative(base: Path, path: Path) -> int:
    """Profundidad de `path` relativa a `base`."""
    return len(path.relative_to(base).parts)


def has_child_dirs(folder: Path) -> bool:
    """Devuelve True si `folder` tiene subdirectorios (no excluidos)."""
    try:
        for e in folder.iterdir():
            if e.is_dir() and not is_excluded_dir(e):
                return True
    except PermissionError:
        pass
    return False


def file_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def is_placeholder_or_short(text: str, min_chars: int) -> bool:
    """Devuelve True si el texto coincide con el placeholder o es muy corto."""
    t = text.strip()
    if not t:
        return True
    if t == BASICO_PLACEHOLDER:
        return True
    return len(t) < min_chars


def should_write_generic(path: Path) -> Tuple[bool, str]:
    """
    Decide si se debe escribir en `path` para archivos genéricos (regla por tamaño).
    - True/"crear"              si no existe
    - True/"sobrescribir_vacio" si existe y está vacío
    - False/"omitir_contenido"  si existe con contenido
    """
    if not path.exists():
        return True, "crear"
    try:
        if path.is_file() and path.stat().st_size == 0:
            return True, "sobrescribir_vacio"
    except OSError:
        return False, "omitir_contenido"
    return False, "omitir_contenido"


def should_write_basicos(path: Path) -> Tuple[bool, str]:
    """
    Decide si escribir en 'Contenidos básicos.md', considerando placeholder y longitud mínima.
    - True/"crear"                     si no existe
    - True/"sobrescribir_vacio"        si tamaño 0
    - True/"placeholder_o_corto"       si tiene placeholder o es corto (< MIN_CHARS_BASICO)
    - False/"omitir_contenido"         si tiene contenido suficiente
    """
    if not path.exists():
        return True, "crear"
    try:
        if path.is_file():
            if path.stat().st_size == 0:
                return True, "sobrescribir_vacio"
            text = file_text_or_empty(path)
            if is_placeholder_or_short(text, MIN_CHARS_BASICO):
                return True, "placeholder_o_corto"
    except OSError:
        return False, "omitir_contenido"
    return False, "omitir_contenido"


# ---------------------- LÓGICA PRINCIPAL ----------------------


def main():
    base = Path(__file__).resolve().parent

    # 1) Árbol global (contexto) — ya excluye las carpetas invisibles
    tree_text = build_tree(base)

    # 2) Subcarpetas objetivo — ya excluye las carpetas invisibles
    target_dirs = list(iter_all_subdirs(base))
    if not target_dirs:
        print("No se han encontrado subcarpetas objetivo (excluyendo directorios ignorados).")
        print("Directorio base:", base)
        sys.exit(0)

    # 3) Mensaje del sistema (común)
    system_msg = (
        "Eres un asistente experto en redacción didáctica para libros de programación.\n"
        "INSTRUCCIONES OBLIGATORIAS:\n"
        "1) Responde en español.\n"
        "2) Escribe EXACTAMENTE 10 párrafos en prosa continua, tono literario y didáctico.\n"
        "3) No incluyas fragmentos de código, ni títulos, ni viñetas, ni listas numeradas.\n"
        "4) Mantén la explicación agnóstica de tecnología: no menciones lenguajes, frameworks ni herramientas concretas.\n"
        "5) No hagas referencias explícitas a otras carpetas o archivos. Considera el contexto general, pero sin nombrarlo.\n"
        "6) Evita repetir ideas; cada párrafo debe aportar un avance claro del discurso.\n"
    )

    context_header = (
        "A continuación tienes el árbol GLOBAL de directorios. "
        "Úsalo solo como referencia contextual implícita (no lo cites literalmente):\n\n"
        "```\n" + tree_text + "\n```\n"
    )

    # 4) Procesar cada carpeta
    for d in target_dirs:
        # Omitir la propia carpeta contenedora de básicos
        if d.name == OUTPUT_SUBFOLDER:
            print(f"[→] Carpeta contenedora detectada, se omite: {d}")
            continue

        if is_excluded_dir(d):
            print(f"[→] Directorio excluido (invisible): {d}")
            continue

        rel = d.relative_to(base)
        depth = depth_relative(base, d)
        etiqueta = label_for_depth(depth)

        is_subunidad = (etiqueta == "subunidad didáctica")

        if is_subunidad:
            # Caso 2: crear subcarpeta + "Contenidos básicos.md"
            out_dir = d / OUTPUT_SUBFOLDER
            out_path = out_dir / OUTPUT_BASICO

            # Crear carpeta contenedora si no existe
            if not out_dir.exists():
                try:
                    out_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    print(f"[!] No se pudo crear {out_dir}: {e}")
                    continue

            write_ok, reason = should_write_basicos(out_path)
            if not write_ok:
                print(f"[→] Ya existe con contenido suficiente, se omite: {out_path}")
                continue
            else:
                if reason == "sobrescribir_vacio":
                    print(f"[!] Archivo vacío encontrado, se sobrescribirá: {out_path}")
                elif reason == "placeholder_o_corto":
                    print(f"[!] Archivo con placeholder o corto, se sobrescribirá: {out_path}")
                else:
                    print(f"[+] Se creará nuevo archivo: {out_path}")

            user_prompt = (
                f"{context_header}\n"
                f"Carpeta actual: `{rel}` (esto corresponde a una {etiqueta}).\n\n"
                "Redacta los contenidos básicos de esta subunidad con un hilo expositivo continuo, "
                "como si fuera una sección de un libro de programación. Evita enumeraciones explícitas: "
                "todo debe aparecer integrado en la narración. Mantén el foco en el alcance propio de esta carpeta, "
                "sin mencionar otras carpetas. Exactamente 10 párrafos, en prosa, sin títulos, sin listas y sin código.\n"
            )

            print("\n" + "=" * 100)
            print(f"[PROMPT (BÁSICOS) para] {rel}  (nivel {depth} → {etiqueta})")
            print("-" * 100)
            print(user_prompt)

            try:
                answer = chat_ollama(MODEL, system_msg, user_prompt)
            except requests.RequestException as e:
                print(f"[!] Error al llamar a Ollama para {rel}: {e}")
                continue

            print("-" * 100)
            print(f"[RESPUESTA de] {rel}")
            print("-" * 100)
            print(answer)
            print("=" * 100)

            try:
                out_path.write_text(answer + "\n", encoding="utf-8")
                print(f"[✓] Guardado: {out_path}")
            except Exception as e:
                print(f"[!] No se pudo escribir {out_path}: {e}")

        else:
            # Caso 3: crear "000-Resumen.md" en la carpeta actual (sin subcarpeta),
            # salvo que la carpeta esté bloqueada para resúmenes.
            if d.name in BLOCK_RESUMEN_DIRNAMES:
                print(f"[→] Carpeta marcada para NO crear resumen, se omite: {d}")
                continue

            out_path = d / OUTPUT_RESUMEN

            write_ok, reason = should_write_generic(out_path)
            if not write_ok:
                print(f"[→] Ya existe con contenido, se omite: {out_path}")
                continue
            else:
                if reason == "sobrescribir_vacio":
                    print(f"[!] Archivo vacío encontrado, se sobrescribirá: {out_path}")
                else:
                    print(f"[+] Se creará nuevo archivo: {out_path}")

            user_prompt = (
                f"{context_header}\n"
                f"Carpeta actual: `{rel}` (esto corresponde a un {etiqueta}).\n\n"
                "Redacta un RESUMEN de alto nivel, coherente y continuo, que sirva de introducción y orientación para esta carpeta. "
                "Debe presentar el propósito, el enfoque y el recorrido conceptual típico en este nivel de la jerarquía, evitando "
                "mencionar explícitamente otras carpetas. Exactamente 10 párrafos, en prosa, sin títulos, sin listas y sin código.\n"
            )

            print("\n" + "=" * 100)
            print(f"[PROMPT (RESUMEN) para] {rel}  (nivel {depth} → {etiqueta})")
            print("-" * 100)
            print(user_prompt)

            try:
                answer = chat_ollama(MODEL, system_msg, user_prompt)
            except requests.RequestException as e:
                print(f"[!] Error al llamar a Ollama para {rel}: {e}")
                continue

            print("-" * 100)
            print(f"[RESPUESTA de] {rel}")
            print("-" * 100)
            print(answer)
            print("=" * 100)

            try:
                out_path.write_text(answer + "\n", encoding="utf-8")
                print(f"[✓] Guardado: {out_path}")
            except Exception as e:
                print(f"[!] No se pudo escribir {out_path}: {e}")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print("\nTerminado.")


if __name__ == "__main__":
    main()

