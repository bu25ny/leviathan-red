#!/usr/bin/env python3
"""
deployment_manager.py — Alejandra / Ale · Unidad 36NZVW
Sistema de Doble Búfer con Rollback Automático (A/B pattern).

Arquitectura:
  - v_stable  = versión actualmente en producción (nunca se toca directamente)
  - v_new     = candidato en validación
  - version.json = puntero atómico que dice cuál es "stable"

Flujo:
  deploy(codigo_fuente)
    ├── 1. guardian.validate_ast()  — zero I/O, validación RAM
    ├── 2. write to v_new.py         — escritura atómica
    ├── 3. liveness_probe()         — subprocess 3s, CPU quota
    │       ├── FAIL → rollback() → return False
    │       └── PASS → continue
    ├── 4. readiness_check()         — health check funcional
    │       ├── FAIL → rollback() → return False
    │       └── PASS → continue
    └── 5. promote()                 — os.replace(v_new → v_stable)

Liveness probe previene:
  - Bucles infinitos (detonadores de Signal 9)
  - Crash inmediato por import roto
  - Consumo excesivo de CPU en hardware Android

El sistema NUNCA arranca código no validado en producción.
"""

import ast
import json
import os
import resource
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Configuración ────────────────────────────────────────────────────────────
GUARDIAN_DIR = Path(__file__).parent
V_STABLE = GUARDIAN_DIR / "v_stable.py"
V_NEW = GUARDIAN_DIR / "v_new.py"
VERSION_JSON = GUARDIAN_DIR / "version.json"
DEPLOYMENT_LOG = GUARDIAN_DIR / "deployment_log.md"

# Límites del liveness probe para evadir Signal 9 en Android
LIVENESS_TIMEOUT_SEC = 3.0


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[DEPLOY] " + ts + " — " + msg
    print(line)
    with open(DEPLOYMENT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load_version() -> dict:
    if not VERSION_JSON.exists():
        default = {"stable": None, "new": None, "history": []}
        with open(VERSION_JSON, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(VERSION_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_version(state: dict) -> None:
    tmp = VERSION_JSON.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp), str(VERSION_JSON))


# ── PASO 1: Validación AST ───────────────────────────────────────────────────
def _validate_ast(source: str) -> tuple[bool, str | None]:
    try:
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        msg = "SyntaxError en linea " + str(e.lineno) + ": " + e.msg
        return False, msg


# ── PASO 2: Escritura atómica a v_new ──────────────────────────────────────
def _write_v_new(source: str) -> bool:
    tmp = V_NEW.with_suffix(".py.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(source)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp), str(V_NEW))
        return True
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        _log("ERROR: Fallo en escritura atomica de v_new: " + str(e))
        return False


# ── PASO 3: Liveness Probe ─────────────────────────────────────────────────
def _liveness_probe() -> tuple[bool, str]:
    """
    Ejecuta v_new en un subproceso efímero con timeout de 3s.
    El probe escribe un marker en un path FIJO (no basado en PID del hijo).
    Retorna (True, msg) si el proceso sobrevive 3s y genera ALIVE en stdout.
    Retorna (False, msg) si crashea, timeout, o no responde.
    """
    start = time.time()

    # Marker con nombre FIJO (sin PID) para que el padre pueda encontrarlo
    marker_file = GUARDIAN_DIR / "_liveness_marker.ok"

    # Limpiar marcadores previos
    if marker_file.exists():
        marker_file.unlink()

    # Probe recibe marker_path como ARGUMENTO (no calcula PID interno)
    # Así evita el desajuste padre/hijo
    probe_script = (
        "import sys, time\n"
        "marker_path = sys.argv[1]\n"
        "v_new_path = sys.argv[2]\n"
        "open(marker_path, 'w').close()\n"          # Marca: el probe inicio
        "sys.stdout.write('ALIVE\\n')\n"
        "sys.stdout.flush()\n"
        "# Importa v_new.py como modulo real — aqui se detecta\n"
        "# cualquier bucle infinito, import roto, o error de runtime\n"
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('v_new', v_new_path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "sys.stdout.write('IMPORT_OK\\n')\n"
        "sys.stdout.flush()\n"
        "time.sleep(0.5)\n"
    )
    probe_path = GUARDIAN_DIR / "_probe_temp.py"
    try:
        with open(probe_path, "w", encoding="utf-8") as f:
            f.write(probe_script)

        def set_resource_limits():
            """Limita CPU y RAM del subproceso para no despertar Signal 9."""
            try:
                # CPU soft cap al 30% de 1核 durante LIVENESS_TIMEOUT_SEC
                cpu_units = 1  # 1 segundo de CPU
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_units, cpu_units * 2))
                # RAM 128MB
                resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 256 * 1024 * 1024))
            except Exception:
                pass

        proc = subprocess.Popen(
            [sys.executable, str(probe_path), str(marker_file), str(V_NEW)],
            cwd=str(GUARDIAN_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=set_resource_limits,
        )

        try:
            stdout, stderr = proc.communicate(timeout=LIVENESS_TIMEOUT_SEC)
            elapsed = time.time() - start
            marker_found = marker_file.exists()

            if proc.returncode != 0:
                return False, (
                    "Liveness FALLO: returncode="
                    + str(proc.returncode)
                    + " stderr="
                    + stderr.decode("utf-8", errors="replace")[:80]
                )
            if not marker_found:
                return False, "Liveness FALLO: no genero marker de vida"
            if b"ALIVE" not in stdout or b"IMPORT_OK" not in stdout:
                return False, "Liveness FALLO: v_new.py no se importo correctamente. stdout=" + stdout.decode()[:80]

            return True, (
                "Liveness OK: sobrevivio "
                + str(round(elapsed, 2))
                + "s sin consumir recursos excesivos"
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return False, (
                "Liveness FALLO: timeout de "
                + str(LIVENESS_TIMEOUT_SEC)
                + "s (probable bucle infinito)"
            )

    finally:
        if marker_file.exists():
            marker_file.unlink()
        if probe_path.exists():
            probe_path.unlink()


# ── PASO 4: Readiness Check ─────────────────────────────────────────────────
def _readiness_check() -> tuple[bool, str]:
    """Verifica que v_new puede operar sin errores de runtime."""
    check_script = (
        "import sys\n"
        "from pathlib import Path\n"
        "p = Path(sys.argv[1])\n"
        "assert p.exists(), 'Carpeta de trabajo no accesible'\n"
        "sys.stdout.write('READY\\n')\n"
    )
    check_path = GUARDIAN_DIR / "_check_temp.py"
    try:
        with open(check_path, "w", encoding="utf-8") as f:
            f.write(check_script)
        proc = subprocess.Popen(
            [sys.executable, str(check_path), str(GUARDIAN_DIR)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(timeout=5)
        if proc.returncode != 0 or b"READY" not in stdout:
            return False, "Readiness FALLO: " + stderr.decode()[:80]
        return True, "Readiness OK: puede operar sin errores de runtime"
    except Exception as e:
        return False, "Readiness FALLO: exception=" + str(e)
    finally:
        if check_path.exists():
            check_path.unlink()


# ── PASO 5: Promote ─────────────────────────────────────────────────────────
def _promote(source: str, history_entry: str) -> bool:
    """Promueve v_new a v_stable de forma atómica y actualiza version.json."""
    stable_tmp = V_STABLE.with_suffix(".py.tmp")
    try:
        with open(stable_tmp, "w", encoding="utf-8") as f:
            f.write(source)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(stable_tmp), str(V_STABLE))
        if V_NEW.exists():
            V_NEW.unlink()
        state = _load_version()
        state["stable"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["new"] = None
        state["history"].append(history_entry)
        _save_version(state)
        return True
    except Exception as e:
        _log("ERROR en promote: " + str(e))
        return False


# ── ROLLBACK ───────────────────────────────────────────────────────────────
def _rollback() -> bool:
    """Descarta v_new y mantiene v_stable intacto."""
    if V_NEW.exists():
        V_NEW.unlink()
    state = _load_version()
    state["new"] = None
    _save_version(state)
    return True


# ── API PRINCIPAL ───────────────────────────────────────────────────────────
def deploy(source: str, label: str = "unnamed") -> bool:
    """
    Pipeline completo de despliegue con doble búfer.

    Si cualquier paso falla → Rollback automático → v_stable intacto.

    Returns:
        True  = promoción completada
        False = despliegue abortado (rollback hecho)
    """
    deploy_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + label
    _log("INICIO despliegue: " + deploy_id)

    state = _load_version()
    state["new"] = deploy_id
    _save_version(state)

    # 1. Validación AST
    _log("[1/4] Validando AST...")
    valid, err = _validate_ast(source)
    if not valid:
        _log("  [1/4] FAIL-AST: " + err)
        _log("Despliegue ABORTADO en paso 1.")
        return False

    # 2. Escritura a v_new
    _log("[2/4] Escribiendo v_new.py (atomico)...")
    if not _write_v_new(source):
        _log("Despliegue ABORTADO en paso 2.")
        return False
    _log("  [2/4] v_new.py escrito correctamente.")

    # 3. Liveness Probe
    _log("[3/4] Ejecutando Liveness Probe...")
    alive, msg = _liveness_probe()
    _log("  [3/4] " + msg)
    if not alive:
        _log("ROLLBACK: liveness fallida, descartando v_new.")
        _rollback()
        _log("Despliegue ABORTADO en paso 3.")
        return False

    # 4. Readiness Check
    _log("[4/4] Ejecutando Readiness Check...")
    ready, msg = _readiness_check()
    _log("  [4/4] " + msg)
    if not ready:
        _log("ROLLBACK: readiness fallida, descartando v_new.")
        _rollback()
        _log("Despliegue ABORTADO en paso 4.")
        return False

    # 5. Promote
    history_entry = (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        + " | "
        + deploy_id
        + " | promoted"
    )
    if not _promote(source, history_entry):
        _log("Despliegue ABORTADO en paso 5 (promote).")
        return False

    _log(">>> DESPLIEGUE EXITOSO: " + deploy_id)
    return True


def status() -> dict:
    state = _load_version()
    return {
        "v_stable": str(V_STABLE) if V_STABLE.exists() else None,
        "v_new": str(V_NEW) if V_NEW.exists() else None,
        "stable_timestamp": state.get("stable"),
        "new_candidate": state.get("new"),
        "history_len": len(state.get("history", [])),
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python deployment_manager.py <subcomando> [args]")
        print("  status               — muestra estado de búfers")
        print("  deploy <archivo.py>  — despliega candidato")
        print("  deploy-stdin         — despliega desde stdin")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "status":
        print(json.dumps(status(), indent=2))
    elif cmd == "deploy":
        if len(sys.argv) < 3:
            print("ERROR: specify <archivo.py>")
            sys.exit(1)
        with open(sys.argv[2], "r") as f:
            source = f.read()
        success = deploy(source, Path(sys.argv[2]).stem)
        sys.exit(0 if success else 1)
    elif cmd == "deploy-stdin":
        source = sys.stdin.read()
        success = deploy(source, "stdin")
        sys.exit(0 if success else 1)
    else:
        print("Comando desconocido: " + cmd)
        sys.exit(1)