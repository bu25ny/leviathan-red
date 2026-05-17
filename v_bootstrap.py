#!/usr/bin/env python3
"""
v_bootstrap.py — Alejandra / Ale · Unidad 36NZVW
Punto de entrada unificado para la fase II.

Este archivo NO es tocado por el pipeline A/B.
Es el ancla de coexistencia entre todos los módulos desplegados.

Modulos disponibles:
  - memory_hydrator (via v_stable.py)
  - mcp_bridge     (via v_stable.py)
  - guardian       (directo)
  - deployment_manager (directo)

Uso:
  python3 v_bootstrap.py [comando] [args...]

Comandos:
  hydrate [--thread THREAD_ID]  — Rehidratar estado desde WAL DB
  mcp [tool] [--json ARGS]      — Enviar peticion al sandbox MCP
  status                         — Estado del sistema
  test                           — Prueba de fuego completa
"""

import sys
import os
from pathlib import Path

GUARDIAN_DIR = Path(__file__).parent
sys.path.insert(0, str(GUARDIAN_DIR))

# Importar modulo actual de v_stable (ultimo despliegue A/B)
# v_stable.py puede ser memory_hydrator o mcp_bridge segun el orden
try:
    import v_stable as _v_stable_current
    CURRENT_MODULE = getattr(_v_stable_current, "__name__", "unknown")
except Exception as e:
    _v_stable_current = None
    CURRENT_MODULE = "error:" + str(e)[:50]

# Importar todos los modulos directamente disponibles
try:
    from memory_hydrator import MemoryHydrator
except ImportError:
    MemoryHydrator = None

try:
    from mcp_bridge import MCPBridge, test_sandbox
except ImportError:
    MCPBridge = None
    test_sandbox = None


def cmd_hydrate(args: list) -> int:
    """Rehidrata el estado desde la base de datos WAL."""
    thread_id = "36NZVW"
    db_path = str(GUARDIAN_DIR / "leviatan.db")

    # Parsear flags
    i = 0
    while i < len(args):
        if args[i] == "--thread" and i + 1 < len(args):
            thread_id = args[i + 1]
            i += 2
        elif args[i] == "--db" and i + 1 < len(args):
            db_path = args[i + 1]
            i += 2
        else:
            i += 1

    if MemoryHydrator is None:
        print("ERROR: memory_hydrator no disponible")
        print("Hint: Asegurate de que memory_hydrator.py este en", GUARDIAN_DIR)
        return 1

    h = MemoryHydrator(db_path=db_path)
    state = h.get_state(thread_id)

    print("=== REHIDRATACION WAL ===")
    print("Thread:", state["thread"]["thread_id"])
    print("Estado:", state["thread"]["state"])
    print("Prioridad:", state["thread"]["priority"])
    print("DB:", state["db_status"])
    print("Origen:", state["thread"]["source"])
    print("Eventos:", len(state["events"]))

    if state["thread"]["source"] == "fail-safe-not-found":
        print("ADVERTENCIA: Thread no encontrado en DB. Modo fail-safe activo.")
    elif state["thread"]["source"] == "fail-safe":
        print("ADVERTENCIA: DB no encontrada. Modo fail-safe activo.")

    return 0


def cmd_mcp(args: list) -> int:
    """Envía una petición al sandbox MCP."""
    from memory_hydrator import _load_env
    from mcp_bridge import MCPBridge

    env = _load_env()
    cmd = env.get("MCP_SERVER_CMD", "")
    tool_name = args[0] if args else "python"
    tool_args = {}

    # Parsear --json para pasar argumentos
    i = 0
    while i < len(args):
        if args[i] == "--tool" and i + 1 < len(args):
            tool_name = args[i + 1]
            i += 2
        elif args[i] == "--json" and i + 1 < len(args):
            import json
            try:
                tool_args = json.loads(args[i + 1])
            except json.JSONDecodeError as e:
                print("ERROR: JSON invalido en --json:", e)
                return 1
            i += 2
        else:
            i += 1

    bridge = MCPBridge(cmd=cmd, timeout=15)
    connected, msg = bridge.connect()

    if not connected:
        print("ERROR de conexion MCP:", msg)
        return 1

    print("Conectado al sandbox:", bridge.server_type)
    print("Herramienta:", tool_name)
    print("Args:", tool_args)
    print()

    success, result = bridge.call_tool(tool_name, tool_args)

    if success:
        print("=== RESPUESTA DEL SANDBOX ===")
        for item in result:
            if isinstance(item, dict):
                print(item.get("text", str(item)))
            else:
                print(str(item))
        bridge.disconnect()
        return 0
    else:
        print("ERROR en call_tool:", result)
        bridge.disconnect()
        return 1


def cmd_status(args: list) -> int:
    """Muestra estado general del sistema."""
    from deployment_manager import status as dm_status

    print("=== LEVIATHAN RED — ESTADO DEL SISTEMA ===")
    print()

    # Deployment status
    st = dm_status()
    print("Pipeline A/B:")
    print("  Stable:", st["v_stable"])
    print("  Timestamp:", st["stable_timestamp"])
    print("  History:", st["history_len"], "despliegues")
    print("  Modulo actual en v_stable:", CURRENT_MODULE)
    print()

    # WAL DB status
    print("Base de datos WAL:")
    if MemoryHydrator:
        h = MemoryHydrator(db_path=str(GUARDIAN_DIR / "leviatan.db"))
        s = h.get_state("36NZVW")
        print("  DB:", s["db_status"])
        print("  Thread 36NZVW:", s["thread"]["state"], "/", s["thread"]["priority"])
        print("  Eventos:", len(s["events"]))
        print("  Source:", s["thread"]["source"])
    else:
        print("  memoria_hydrator: no disponible")
    print()

    # MCP Bridge status
    print("MCP Bridge:")
    print("  Modulo mcp_bridge: disponible" if MCPBridge else "  Modulo mcp_bridge: no disponible")
    print()

    # Archivos
    import os
    print("Archivos de modulo:")
    for fn in ["guardian.py", "deployment_manager.py", "memory_hydrator.py",
               "mcp_bridge.py", "v_bootstrap.py"]:
        path = GUARDIAN_DIR / fn
        exists = "✅ existe" if path.exists() else "❌ no existe"
        size = path.stat().st_size if path.exists() else 0
        print(f"  {fn}: {exists} ({size} bytes)")
    return 0


def cmd_test(args: list) -> int:
    """Ejecuta la prueba de fuego completa."""
    print("=== PRUEBA DE FUEGO MCP — ZERO-NETWORK FOOTPRINT ===")
    print()
    if test_sandbox:
        result = test_sandbox()
        print()
        print("Conectado:", result["connected"])
        print("Servidor:", result["server_type"])
        print("Herramientas:", len(result["tools"]))
        print("Aislado:", result["isolated"])
        print()
        if result["test_output"]:
            print("=== OUTPUT DEL SANDBOX ===")
            print(result["test_output"])
        if result["error"]:
            print("Error:", result["error"])
        return 0 if result["isolated"] else 1
    else:
        print("ERROR: mcp_bridge no disponible")
        return 1


# ── Router principal ──────────────────────────────────────────────────────────
def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    cmd = sys.argv[1]
    args = sys.argv[2:]

    routers = {
        "hydrate": cmd_hydrate,
        "mcp": cmd_mcp,
        "status": cmd_status,
        "test": cmd_test,
    }

    if cmd not in routers:
        print("Comando desconocido:", cmd)
        print("Disponibles:", list(routers.keys()))
        return 1

    return routers[cmd](args)


if __name__ == "__main__":
    sys.exit(main())