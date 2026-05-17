#!/usr/bin/env python3
"""
memory_hydrator.py — Alejandra / Ale · Unidad 36NZVW
Motor de Rehidratacion de Estado con SQLite WAL.

Conecta con LEVIATAN_DB_PATH, activa modo WAL, y extrae
el ultimo estado transaccional de la unidad para reconstruir
el contexto operativo previo a la amnesia.

Principios:
  - Primera instruccion SQL: PRAGMA journal_mode=WAL
  - Solo lectura (no modifica la DB — safe para produccion)
  - Fail-safe default: si algo falla, retorna estado seguro
  - Cierre obligatorio de cursores y conexiones
"""

import json
import sqlite3
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ── Configuracion ───────────────────────────────────────────────────────────
# LEVIATAN_DB_PATH desde .env o fallback a workspace local
_LEVIATAN_DB_FALLBACK = str(
    Path(__file__).parent / "leviatan.db"
)

# Valores de fail-safe (Estado seguro ante cualquier error)
_FAIL_SAFE_STATE = {
    "thread_id": "UNKNOWN",
    "state": "NOMINAL",
    "priority": "BAJA",
    "updated_at": None,
    "metadata": {},
    "source": "fail-safe",
    "error": None,
}


def _load_env(path: str | None = None) -> dict:
    """Lee variables del archivo .env si existe."""
    env_file = Path(path) if path else Path(__file__).parent / ".env"
    if not env_file.exists():
        return {}
    env = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _get_db_path() -> str:
    """Resuelve la ruta de la DB: .env > fallback local."""
    env = _load_env()
    db_path = env.get("LEVIATHAN_DB_PATH") or _LEVIATAN_DB_FALLBACK
    return db_path


class MemoryHydrator:
    """
    Motor de rehidratacion de estado para la unidad 36NZVW.

    Uso:
        hydrator = MemoryHydrator(db_path="/ruta/leviatan.db")
        state = hydrator.get_state(thread_id="36NZVW")
        print(state["state"])  # "OPERATIVO" o "NOMINAL" (fail-safe)
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or _get_db_path()
        self.conn: sqlite3.Connection | None = None
        self._connected = False

    def _open_connection(self) -> bool:
        """
        Abre conexion SQLite y activa modo WAL.
        Primera instruccion SQL obligatoria: PRAGMA journal_mode=WAL.
        Retorna True si la conexion fue exitosa.
        """
        try:
            if not Path(self.db_path).exists():
                return False
            self.conn = sqlite3.connect(
                self.db_path,
                timeout=5.0,
                isolation_level=None,  # autocommit
                check_same_thread=False,
            )
            # ACTIVAR WAL — primera instruccion
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            result = cursor.fetchone()
            if result and result[0].upper() == "WAL":
                self._connected = True
                return True
            else:
                return False
        except Exception:
            return False

    def _close_connection(self) -> None:
        """Cierra conexion y libera cursores."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            finally:
                self.conn = None
                self._connected = False

    def _hydrate_thread(self, thread_id: str) -> dict:
        """
        Extrae el estado transaccional del thread desde thread_state.
        Si no existe, retorna fail-safe con source='not_found'.
        """
        if not self._connected:
            result = _FAIL_SAFE_STATE.copy()
            result["error"] = "No se pudo conectar a la base de datos"
            return result

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT thread_id, state, priority, updated_at, metadata "
                "FROM thread_state WHERE thread_id = ?",
                (thread_id,),
            )
            row = cursor.fetchone()

            if not row:
                result = _FAIL_SAFE_STATE.copy()
                result["thread_id"] = thread_id
                result["state"] = "REINICIO"
                result["priority"] = "MEDIA"
                result["source"] = "fail-safe-not-found"
                result["error"] = "Thread ID no encontrado en la base de datos"
                return result

            metadata_raw = row[4] or "{}"
            try:
                metadata = json.loads(metadata_raw)
            except Exception:
                metadata = {"raw": metadata_raw}

            return {
                "thread_id": row[0],
                "state": row[1] or "DESCONOCIDO",
                "priority": row[2] or "BAJA",
                "updated_at": row[3],
                "metadata": metadata,
                "source": "db",
                "error": None,
            }

        except Exception as e:
            result = _FAIL_SAFE_STATE.copy()
            result["thread_id"] = thread_id
            result["error"] = "Excepcion al consultar thread_state: " + str(e)
            return result

    def _hydrate_events(self, thread_id: str, limit: int = 50) -> list[dict]:
        """Extrae los ultimos 'limit' eventos del thread."""
        if not self._connected:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, event_type, payload, timestamp "
                "FROM events WHERE thread_id = ? "
                "ORDER BY timestamp DESC, id DESC LIMIT ?",
                (thread_id, limit),
            )
            rows = cursor.fetchall()
            events = []
            for row in rows:
                payload_raw = row[2] or "{}"
                try:
                    payload = json.loads(payload_raw)
                except Exception:
                    payload = {"raw": payload_raw}
                events.append({
                    "id": row[0],
                    "event_type": row[1],
                    "payload": payload,
                    "timestamp": row[3],
                })
            return events

        except Exception:
            return []

    def _hydrate_checkpoints(self, thread_id: str, limit: int = 5) -> list[dict]:
        """Extrae los ultimos checkpoints de recovery."""
        if not self._connected:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, checkpoint_label, state_snapshot, created_at "
                "FROM checkpoints WHERE thread_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (thread_id, limit),
            )
            rows = cursor.fetchall()
            checkpoints = []
            for row in rows:
                snapshot_raw = row[2] or "{}"
                try:
                    snapshot = json.loads(snapshot_raw)
                except Exception:
                    snapshot = {"raw": snapshot_raw}
                checkpoints.append({
                    "id": row[0],
                    "label": row[1],
                    "snapshot": snapshot,
                    "created_at": row[3],
                })
            return checkpoints

        except Exception:
            return []

    def get_state(self, thread_id: str = "36NZVW") -> dict:
        """
        Punto de entrada unico para rehidratacion.

        Ejecuta el pipeline completo:
          1. Abre conexion WAL
          2. Consulta thread_state
          3. Consulta ultimos eventos
          4. Consulta checkpoints
          5. Cierra conexion

        Si cualquier paso falla, fail-safe garantiza que el sistema
        sigue operativo con estado NOMINAL/BAJA.

        Returns:
            dict con keys:
              - thread: estado del thread
              - events: lista de eventos recientes
              - checkpoints: lista de recovery points
              - db_status: "connected" | "fail-safe"
              - hydrated_at: timestamp de rehidratacion
        """
        thread_state = _FAIL_SAFE_STATE.copy()
        events = []
        checkpoints = []
        db_status = "fail-safe"

        try:
            connected = self._open_connection()
            if connected:
                thread_state = self._hydrate_thread(thread_id)
                events = self._hydrate_events(thread_id)
                checkpoints = self._hydrate_checkpoints(thread_id)
                db_status = "connected"
            else:
                thread_state["error"] = (
                    "No se pudo abrir conexion a "
                    + self.db_path
                    + " (archivo no existe o no accessible)"
                )

        except Exception as e:
            thread_state["error"] = "Excepcion critica en get_state: " + str(e)
            traceback.print_exc()

        finally:
            self._close_connection()

        return {
            "thread": thread_state,
            "events": events,
            "checkpoints": checkpoints,
            "db_status": db_status,
            "db_path": self.db_path,
            "hydrated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "thread_id": thread_id,
        }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Leer thread_id desde .env o usar default
    env = _load_env()
    thread_id = env.get("LANGGRAPH_THREAD_ID", "36NZVW")

    hydrator = MemoryHydrator()
    state = hydrator.get_state(thread_id=thread_id)

    print("=== REPORTE DE REHIDRATACION ===")
    print("DB status:", state["db_status"])
    print("Thread ID:", state["thread_id"])
    print("DB path:", state["db_path"])
    print()

    t = state["thread"]
    print("Estado del thread:")
    print("  state:", t["state"])
    print("  priority:", t["priority"])
    print("  updated_at:", t["updated_at"])
    print("  metadata:", json.dumps(t["metadata"], indent=4))
    print("  source:", t["source"])
    if t.get("error"):
        print("  ERROR:", t["error"])
    print()

    print("Eventos recientes:", len(state["events"]))
    for e in state["events"][:5]:
        print(f"  [{e['timestamp']}] {e['event_type']} — {str(e['payload'])[:60]}")
    print()

    print("Checkpoints:", len(state["checkpoints"]))
    print("Rehidratado en:", state["hydrated_at"])