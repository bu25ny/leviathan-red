#!/usr/bin/env python3
"""
guardian.py — Alejandra / Ale · Unidad 36NZVW
Oraculo de Sintaxis para escritura atomica de Python.

Uso:
    from guardian import validate_and_write

    success = validate_and_write(
        source_code="# tu codigo aqui\n",
        target_path="/ruta/archivo.py"
    )

Si ast.parse() detecta SyntaxError -> Fail-Fast -> log en corrections.md
Si pasa validacion -> escritura atomica (tempfile + fsync + os.replace)
"""

import ast
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

GUARDIAN_DIR = Path(__file__).parent
CORRECTIONS_FILE = GUARDIAN_DIR / "corrections.md"


def _build_log_entry(
    timestamp: str,
    target_path: str,
    err_type: str,
    err_msg: str,
    err_loc: str,
    err_text: str,
    source: str,
) -> str:
    """Construye el bloque de log para corrections.md sin f-strings con backslashes."""
    lines = [
        "",
        "---",
        "[FAIL-FAST] · " + timestamp,
        "**Target:** `" + target_path + "`",
        "**Error:** `" + err_type + "` — " + err_msg,
    ]
    if err_loc:
        lines.append("**Ubicacion:** " + err_loc)
    lines.append("**Fragmento fallido:**")
    lines.append("```python")
    lines.append(err_text)
    lines.append("```")
    lines.append("**Codigo inyectado:**")
    lines.append("```python")
    truncated = source[:500] + ("..." if len(source) > 500 else "")
    lines.append(truncated)
    lines.append("```")
    lines.append("**Accion tomada:** Abortado. No se modifico v_stable.")
    return "\n".join(lines) + "\n"


def _log_failure(source: str, error: Exception, target_path: str) -> None:
    """Registra fallo en corrections.md con etiqueta [FAIL-FAST]."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    err_type = type(error).__name__
    err_msg = getattr(error, "msg", str(error))
    err_loc_parts = []
    if hasattr(error, "lineno"):
        err_loc_parts.append("linea " + str(error.lineno))
        col = getattr(error, "offset", None)
        if col:
            err_loc_parts.append("columna " + str(col))
    err_loc = ", ".join(err_loc_parts)
    err_text = getattr(error, "text", None) or "(vacio)"

    entry = _build_log_entry(
        timestamp, target_path, err_type, err_msg, err_loc, err_text, source
    )
    with open(CORRECTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def validate_ast(source: str) -> tuple[bool, str | None, Exception | None]:
    """
    Valida source con ast.parse().
    Retorna (True, None, None) si es valido.
    Retorna (False, mensaje, exception_obj) si hay SyntaxError.
    """
    try:
        ast.parse(source)
        return True, None, None
    except SyntaxError as e:
        return False, "SyntaxError en linea " + str(e.lineno) + ": " + e.msg, e


def validate_and_write(source: str, target_path: str) -> bool:
    """
    Pipeline completo de validacion + escritura atomica.

    1. ast.parse() — validacion semantica en RAM (no I/O todavia)
    2. Si pasa -> escritura atomica via tempfile + fsync + os.replace()
    3. Si falla -> Fail-Fast, log en corrections.md, abortar

    Returns:
        True  = escritura completada con exito
        False = validacion fallida (ya registrado en corrections.md)
    """
    # Paso 1: Validacion AST (zero I/O)
    valid, error_msg, error_obj = validate_ast(source)
    if not valid:
        print("[GUARDIAN] X Fail-Fast activado: " + error_msg)
        _log_failure(source, error_obj, target_path)
        return False

    # Paso 2: Escritura atomica
    target_abs = str(Path(target_path).resolve())

    try:
        tmp_path = None
        # Dirige el tempfile al MISMO filesystem que el destino
        target_parent = str(Path(target_abs).parent)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".py",
            dir=target_parent,
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(source)
            tmp.flush()
            os.fsync(tmp.fileno())

        # Paso 3: Intercambio atomico
        os.replace(tmp_path, target_abs)
        print("[GUARDIAN] + Escritura atomica completada: " + target_abs)
        return True

    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print("[GUARDIAN] X Error en escritura atomica: " + str(e))
        _log_failure(source, e, target_path)
        return False


# Interfaz CLI: python guardian.py <archivo.py>  (lee stdin como source)
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python guardian.py <path_destino>  (lee stdin como source)")
        sys.exit(1)
    target = sys.argv[1]
    source = sys.stdin.read()
    success = validate_and_write(source, target)
    sys.exit(0 if success else 1)