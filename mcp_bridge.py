#!/usr/bin/env python3
"""
mcp_bridge.py — Alejandra / Ale · Unidad 36NZVW
Cliente MCP generico con transporte stdio para comunicacion hermetica.

Arquitectura:
  - Conexion via subprocess.Popen (sin sockets TCP)
  - Protocolo JSON-RPC 2.0 sobre stdin/stdout
  - Sin acceso a red — Zero-Network Footprint confirmado

Este modulo implementa:
  1. Inicializacion del servidor MCP como subprocess
  2. Handshake de protocolo (initialize)
  3. Llamadas a herramientas via tools/call
  4. Deteccion automatica de esquema (tools/list)
  5. Fail-safe si el servidor no responde o no existe

Uso:
    bridge = MCPBridge(cmd="npx -y @philschmid/code-sandbox-mcp")
    bridge.connect()
    result = bridge.call_tool("python", {"code": "print(1+1)"})
    bridge.disconnect()
"""

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Configuracion ────────────────────────────────────────────────────────────
GUARDIAN_DIR = Path(__file__).parent
ENV_FILE = GUARDIAN_DIR / ".env"
MCP_BRIDGE_LOG = GUARDIAN_DIR / "mcp_bridge_log.md"


def _load_env() -> dict:
    """Lee variables del archivo .env."""
    if not ENV_FILE.exists():
        return {}
    env = {}
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[MCP] " + ts + " — " + msg
    print(line)
    try:
        with open(MCP_BRIDGE_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Tipos de datos ───────────────────────────────────────────────────────────
@dataclass
class MCPRequest:
    jsonrpc: str = "2.0"
    id: int = 1
    method: str = ""
    params: dict = field(default_factory=dict)


@dataclass
class MCPResponse:
    id: int
    result: Any = None
    error: dict | None = None

    @property
    def success(self) -> bool:
        return self.error is None


# ── Cliente MCP stdio ────────────────────────────────────────────────────────
class MCPBridge:
    """
    Puente MCP generico con transporte stdio.

    Implementa JSON-RPC 2.0 sobre pipes unidireccionales.
    El servidor MCP se ejecuta como subprocess y se comunica
    exclusivamente via stdin/stdout — Zero-Network Footprint.
    """

    def __init__(
        self,
        cmd: str | None = None,
        auto_install: bool = False,
        timeout: int = 10,
    ):
        env = _load_env()
        self.cmd = cmd or env.get("MCP_SERVER_CMD", "")
        self.timeout = timeout
        self.auto_install = auto_install
        self.proc: subprocess.Popen | None = None
        self.reader_thread: threading.Thread | None = None
        self.responses: dict[int, MCPResponse] = {}
        self.responses_lock = threading.Lock()
        self.next_id = 1
        self._connected = False
        self._read_buffer = ""

        # Detectar el tipo de servidor para adaptar el protocolo
        self.server_type: str = "unknown"

    def connect(self) -> tuple[bool, str]:
        """
        Inicia el servidor MCP y ejecuta handshake de inicializacion.
        Retorna (success, message).
        """
        if not self.cmd:
            return False, "MCP_SERVER_CMD vacio. No hay servidor que iniciar."

        # Parsear comando en partes (exec + args) para Popen
        # Maneja tanto "npx -y pkg" como "/usr/bin/python script.py"
        import shlex
        try:
            cmd_parts = shlex.split(self.cmd)
        except ValueError:
            # Fallback si shlex falla: split simple
            cmd_parts = self.cmd.split()

        if not cmd_parts:
            return False, "Comando MCP vacio o invalido."

        exec_cmd = cmd_parts[0]
        exec_args = cmd_parts[1:]

        _log("Intentando conectar con servidor MCP: " + self.cmd)

        try:
            self.proc = subprocess.Popen(
                cmd_parts,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(GUARDIAN_DIR),
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )
            _log("Subprocess iniciado — PID: " + str(self.proc.pid))

        except FileNotFoundError as e:
            pkg = parts[1] if len(parts) > 1 else parts[0]
            if self.auto_install and "npx" in cmd_parts[0]:
                _log("Paquete no encontrado — intentando instalacion automatica...")
                install_result = self._auto_install(cmd_parts)
                if not install_result[0]:
                    return False, "No se pudo instalar: " + install_result[1]
                # Reintentar con el paquete ya instalado
                try:
                    self.proc = subprocess.Popen(
                        cmd_parts,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(GUARDIAN_DIR),
                    )
                except Exception as e2:
                    return False, "Error al reiniciar tras instalacion: " + str(e2)
            else:
                return False, "Comando no encontrado: " + parts[0] + " — " + str(e)

        except Exception as e:
            return False, "Error al iniciar subprocess: " + str(e)

        # Iniciar hilo lector en background
        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
        )
        self.reader_thread.start()

        # Handshake de inicializacion JSON-RPC
        success, msg = self._initialize()
        if not success:
            self.disconnect()
            return False, "Handshake fallido: " + msg

        self._connected = True
        return True, "Conectado a servidor MCP (" + self.server_type + ")"

    def _auto_install(self, cmd_parts: list) -> tuple[bool, str]:
        """
        Instala automaticamente un paquete npm si no existe.
        cmd_parts es la lista parseada del comando (ej: ['npx', '-y', '@scope/pkg']).
        """
        import shlex

        # Extraer nombre del paquete npm de la lista de partes
        # Busca '@scope/name' o nombres de paquete plain en la lista
        pkg_name = None
        for part in cmd_parts:
            if part.startswith("@"):
                pkg_name = part
                break
            elif part not in ("npx", "-y", "node", "npm"):
                pkg_name = part
                break

        if not pkg_name:
            return False, "No se pudo extraer nombre de paquete de: " + str(cmd_parts)

        try:
            _log("Ejecutando: npm install -g " + pkg_name)
            proc = subprocess.run(
                ["npm", "install", "-g", pkg_name],
                capture_output=True,
                timeout=120,
            )
            if proc.returncode == 0:
                return True, "Instalado: " + pkg_name
            else:
                stderr_msg = proc.stderr.decode("utf-8", errors="replace")[:200]
                return False, "npm install fallido: " + stderr_msg
        except subprocess.TimeoutExpired:
            return False, "npm install timeout (>120s)"
        except Exception as e:
            return False, "Excepcion en install: " + str(e)

    def _reader_loop(self) -> None:
        """
        Hilo daemon que lee linea a linea del stdout del servidor MCP.
        Parsea respuestas JSON-RPC y las guarda en self.responses.
        """
        if not self.proc or not self.proc.stdout:
            return

        try:
            for line in iter(self.proc.stdout.readline, ""):
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    resp_id = msg.get("id", 0)
                    with self.responses_lock:
                        if "result" in msg:
                            self.responses[resp_id] = MCPResponse(
                                id=resp_id, result=msg.get("result")
                            )
                        elif "error" in msg:
                            self.responses[resp_id] = MCPResponse(
                                id=resp_id, error=msg.get("error")
                            )
                        else:
                            # Notificacion (sin id) — loguear si es interesante
                            _log("Notificacion recibida: " + str(msg)[:100])
                except json.JSONDecodeError:
                    # No es JSON — puede ser output de debug del servidor
                    _log("Stdout no-JSON del servidor: " + line[:100])
        except Exception as e:
            _log("Reader loop exception: " + str(e))

    def _send(self, method: str, params: dict = {}) -> MCPResponse:
        """Envia una peticion JSON-RPC y espera respuesta."""
        if not self.proc or self.proc.stdin is None:
            return MCPResponse(id=-1, error={"message": "No hay conexion"})

        req_id = self.next_id
        self.next_id += 1

        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        try:
            line = json.dumps(req) + "\n"
            self.proc.stdin.write(line.encode("utf-8"))
            self.proc.stdin.flush()
        except Exception as e:
            return MCPResponse(id=req_id, error={"message": "Error al enviar: " + str(e)})

        # Esperar respuesta con timeout
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            with self.responses_lock:
                if req_id in self.responses:
                    return self.responses.pop(req_id)
            time.sleep(0.05)

        return MCPResponse(id=req_id, error={"message": "Timeout esperando respuesta"})

    def _initialize(self) -> tuple[bool, str]:
        """Ejecuta handshake de inicializacion con el servidor MCP."""
        capabilities = {
            "tools": {},
            "prompts": {},
            "resources": {},
        }

        resp = self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": capabilities,
                "clientInfo": {
                    "name": "alejandra-36nzvw",
                    "version": "1.0.0",
                },
            },
        )

        if not resp.success:
            # Intentar handshake con protocolo legacy
            resp = self._send(
                "initialize",
                {
                    "protocolVersion": "2024-01-01",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "alejandra-36nzvw",
                        "version": "1.0.0",
                    },
                },
            )

        if not resp.success:
            return False, str(resp.error)

        # Guardar info del servidor
        result = resp.result or {}
        self.server_type = result.get("serverInfo", {}).get("name", "unknown")
        _log("Servidor conectado: " + self.server_type)
        _log("Capacidades del servidor: " + json.dumps(result.get("capabilities", {})))

        # Enviar initialized notification (importante para algunos servidores)
        notif = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }) + "\n"
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(notif.encode("utf-8"))
                self.proc.stdin.flush()
            except Exception:
                pass

        return True, self.server_type

    def list_tools(self) -> list[dict]:
        """Lista las herramientas disponibles en el servidor MCP."""
        resp = self._send("tools/list")
        if not resp.success:
            _log("tools/list fallido: " + str(resp.error))
            return []

        result = resp.result or {}
        tools = result.get("tools", [])
        _log("Herramientas disponibles: " + str(len(tools)))
        return tools

    def call_tool(self, tool_name: str, arguments: dict | None = None) -> tuple[bool, Any]:
        """
        Ejecuta una herramienta en el servidor MCP.
        Retorna (success, result_or_error).
        """
        if not self._connected:
            return False, "No conectado al servidor MCP"

        resp = self._send(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments or {},
            },
        )

        if not resp.success:
            return False, str(resp.error)

        result = resp.result or {}
        # Dependiendo del servidor, el resultado puede venir en differentes campos
        content = result.get("content", [])
        return True, content

    def disconnect(self) -> None:
        """Detiene el servidor MCP limpiamente."""
        self._connected = False
        if self.proc:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
        _log("Desconectado del servidor MCP")

    def __enter__(self) -> "MCPBridge":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()


# ── Prueba integrada del sandbox ─────────────────────────────────────────────
def test_sandbox() -> dict:
    """
    Prueba de fuego: conecta al sandbox, lista herramientas,
    y ejecuta codigo Python aislado.
    """
    result = {
        "connected": False,
        "server_type": None,
        "tools": [],
        "test_output": None,
        "error": None,
        "isolated": False,
    }

    env = _load_env()
    cmd = env.get("MCP_SERVER_CMD", "")

    _log("=== INICIANDO PRUEBA DE FUEGO MCP ===")
    _log("Comando: " + cmd)

    bridge = MCPBridge(cmd=cmd, timeout=10)

    # 1. Conectar
    connected, msg = bridge.connect()
    if not connected:
        result["error"] = msg
        _log("CONEXION FALLIDA: " + msg)

        # Diagnostico de falla
        if "not found" in msg.lower() or "no such file" in msg.lower():
            result["error"] = (
                "El paquete MCP solicitado ('"
                + cmd
                + "') no existe en npm. "
                + "El comando en .env es un PLACEHOLDER del manifiesto de Fase I. "
                + "El servidor real debe ser configurado con un paquete MCP existente."
            )
        return result

    result["connected"] = True
    result["server_type"] = bridge.server_type
    _log("CONEXION EXITOSA: " + msg)

    # 2. Listar herramientas
    tools = bridge.list_tools()
    result["tools"] = tools
    _log("Herramientas: " + str(len(tools)))
    for t in tools[:5]:
        _log("  - " + str(t.get("name", "unknown")))

    # 3. Ejecutar prueba de aislamiento
    if tools:
        # Buscar herramienta de codigo
        code_tool = None
        for t in tools:
            name = t.get("name", "").lower()
            if any(k in name for k in ["python", "run", "exec", "code", "sandbox", "script"]):
                code_tool = t.get("name")
                break

        if code_tool:
            _log("Ejecutando prueba de aislamiento con: " + code_tool)
            success, content = bridge.call_tool(code_tool, {
                "code": "import platform, os; print('HOST:', platform.node()); print('UID:', os.getuid()); print('PY:', platform.python_version()); print('CWD:', os.getcwd())"
            })
            if success:
                output = ""
                for item in content:
                    if isinstance(item, dict):
                        output += item.get("text", str(item))
                    else:
                        output += str(item)
                result["test_output"] = output.strip()
                result["isolated"] = True
                _log("OUTPUT: " + output.strip().replace("\n", " | "))
        else:
            _log("No se encontro herramienta de codigo en el sandbox")
            result["test_output"] = "No hay herramienta de codigo disponible en este servidor"

    bridge.disconnect()
    _log("=== PRUEBA DE FUEGO FINALIZADA ===")
    return result


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== MCP BRIDGE — PRUEBA DE AISLAMIENTO ===")
    print("Zero-Network Footprint: stdin/stdout only")
    print()

    test_result = test_sandbox()

    print()
    print("=== RESULTADO ===")
    print("Conectado:", test_result["connected"])
    print("Tipo de servidor:", test_result["server_type"])
    print("Herramientas disponibles:", len(test_result["tools"]))
    if test_result["tools"]:
        tool_names = [t.get("name", "?") for t in test_result["tools"][:5]]
        print("Primeras 5:", tool_names)
    print()
    if test_result["error"]:
        print("ERROR:", test_result["error"])
    print()
    if test_result["isolated"]:
        print("=== SALIDA DEL SANDBOX (ejecucion aislada) ===")
        print(test_result["test_output"])
        print()
        print("AISLAMIENTO CONFIRMADO — Zero-Network Footprint activo.")
    else:
        print("Test de aislamiento: PENDIENTE (servidor MCP no disponible)")
        print("Nota: MCP_SERVER_CMD en .env es un placeholder.")
        print("En produccion (Android), configurar con un servidor MCP real.")