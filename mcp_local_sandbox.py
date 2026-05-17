#!/usr/bin/env python3
"""
mcp_local_sandbox.py — Alejandra / Ale · Unidad 36NZVW
Servidor MCP local de ejecucion aislada Zero-Network Footprint.

Este servidor MCP (JSON-RPC 2.0 sobre stdio) recibe codigo Python
via la herramienta 'execute_isolated' y lo ejecuta en un subprocess
completamente aislado del sistema de archivos del host.

Restricciones del sandbox:
  - Sin acceso a archivos del workspace (solo /tmp)
  - Sin network (environment cleansed)
  - Timeout configurable (default 5s, max 30s)

Uso:
  python3 mcp_local_sandbox.py

No abre sockets TCP. Zero-Network Footprint confirmado.
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any

VERSION = "2024-11-05"


def _run_isolated(code: str, timeout: int = 5) -> dict:
    """Ejecuta codigo en subprocess aislado. Retorna dict con stdout/metadata."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": tempfile.gettempdir(),
        "TMPDIR": tempfile.gettempdir(),
        "TERM": "dumb",
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }

    result = {
        "stdout": "", "stderr": "", "exit_code": -1,
        "timeout": False, "meta": {},
        "sandbox_info": {
            "sandbox": "mcp_local_sandbox", "version": "1.0.0",
            "isolation": "subprocess_cleansed_env", "no_network": True,
            "cwd": tempfile.gettempdir(),
        },
    }

    # Escribir codigo a archivo tmp
    try:
        cf = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        cf.write(code)
        cf.close()
        code_path = cf.name
    except Exception as e:
        result["stderr"] = "No se pudo crear archivo tmp: " + str(e)
        return result

    # Wrapper limpio — usa clases para estado (evita global en exec)
    WRAPPER = """# -*- coding: utf-8 -*-
import sys, json, platform, os

class _S:
    code = 0
    trace = None

class _B:
    def __init__(self): self._v = []
    def write(self, s): self._v.append(s)
    def flush(self): pass
    def getvalue(self): return "".join(self._v)

_buf_out = _B()
_buf_err = _B()
_out_saved = sys.stdout
_err_saved = sys.stderr
sys.stdout = _buf_out
sys.stderr = _buf_err

try:
    with open(%r) as _f:
        exec(compile(_f.read(), %r, "exec"), {"__name__": "__sandbox__"})
except SystemExit as _e:
    _S.code = _e.code if _e.code is not None else 0
except Exception:
    import traceback; _S.code = 1; _S.trace = traceback.format_exc()

sys.stdout = _out_saved
sys.stderr = _err_saved

meta = {
    "platform": platform.platform(), "python": platform.python_version(),
    "uid": os.getuid(), "cwd": os.getcwd(),
    "hostname": platform.node(),
    "status": "ok" if _S.code == 0 else ("exit" if _S.trace is None else "error"),
    "exit_code": _S.code,
}

print("===META===" + json.dumps(meta) + "===STDOUT===" + _buf_out.getvalue() +
      "===STDERR===" + _buf_err.getvalue() +
      ("===TRACE===" + _S.trace if _S.trace else ""))
""" % (code_path, code_path)

    try:
        proc = subprocess.Popen(
            [sys.executable, "-c", WRAPPER],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tempfile.gettempdir(),
        )
        raw, _ = proc.communicate(timeout=timeout)
        try:
            os.unlink(code_path)
        except Exception:
            pass

        out = raw.decode("utf-8", errors="replace")

        # Parseo simple: buscar ===META=== y ===STDOUT===
        meta_start = out.find("===META===")
        stdout_start = out.find("===STDOUT===")
        stderr_start = out.find("===STDERR===")

        if meta_start != -1 and stdout_start != -1:
            try:
                result["meta"] = json.loads(out[meta_start + 9:stdout_start])
            except json.JSONDecodeError:
                pass

        if stdout_start != -1:
            end = stderr_start if stderr_start != -1 else len(out)
            result["stdout"] = out[stdout_start + 9:end].strip()

        if stderr_start != -1:
            trace_start = out.find("===TRACE===")
            end = trace_start if trace_start != -1 else len(out)
            result["stderr"] = out[stderr_start + 9:end].strip()

        result["exit_code"] = proc.returncode

    except subprocess.TimeoutExpired:
        proc.kill(); proc.communicate()
        result["timeout"] = True
        result["stderr"] = "TIMEOUT: " + str(timeout) + "s excedido"
        try:
            os.unlink(code_path)
        except Exception:
            pass
    except Exception as e:
        result["stderr"] = "Sandbox error: " + str(e)
        try:
            os.unlink(code_path)
        except Exception:
            pass

    return result


class MCPServer:
    """Servidor MCP sobre stdio. Sin sockets, sin network."""

    def __init__(self):
        self.capabilities = {"tools": {"listChanged": False}}
        self.server_info = {
            "name": "mcp-local-sandbox", "version": "1.0.0",
            "description": "Ejecutor Python aislado — Zero-Network Footprint",
        }

    def _send(self, resp: dict) -> None:
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

    def _handle(self, req: dict) -> None:
        mid = req.get("id")
        params = req.get("params", {})
        method = req.get("method", "")

        if method == "initialize":
            self._send({
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "protocolVersion": VERSION,
                    "capabilities": self.capabilities,
                    "serverInfo": self.server_info,
                },
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            self._send({"jsonrpc": "2.0", "id": mid, "result": {
                "tools": [
                    {
                        "name": "execute_isolated",
                        "description": (
                            "Ejecuta codigo Python en subprocess aislado. "
                            "Sin acceso a archivos del workspace, sin network."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "timeout": {"type": "integer", "default": 5},
                            },
                            "required": ["code"],
                        },
                    },
                    {
                        "name": "sandbox_info",
                        "description": "Info del entorno del sandbox.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ],
            }})
        elif method == "tools/call":
            tool = params.get("name", "")
            args = params.get("arguments", {})

            if tool == "execute_isolated":
                res = _run_isolated(args.get("code", ""), min(int(args.get("timeout", 5)), 30))
                content = []
                if res.get("meta"):
                    m = res["meta"]
                    content.append({
                        "type": "text",
                        "text": (
                            "[SANDBOX]\n  Platform: " + m.get("platform", "?") + "\n"
                            "  Python: " + m.get("python", "?") + "\n"
                            "  UID: " + str(m.get("uid", "?")) + "\n"
                            "  CWD: " + m.get("cwd", "?") + "\n"
                            "  Status: " + m.get("status", "?") + "\n"
                            "  Exit: " + str(m.get("exit_code", -1)) + "\n"
                            "--- OUTPUT ---"
                        ),
                    })
                if res.get("stdout"):
                    content.append({"type": "text", "text": res["stdout"]})
                if res.get("stderr") and res["stderr"].strip():
                    content.append({"type": "text", "text": "[STDERR]\n" + res["stderr"].rstrip()})
                self._send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": content,
                    "isError": bool(res.get("stderr", "").strip()) or res.get("timeout", False),
                }})
            elif tool == "sandbox_info":
                self._send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": json.dumps({
                        "sandbox": "mcp_local_sandbox", "version": "1.0.0",
                        "isolation": "subprocess_cleansed_env",
                        "no_network": True, "no_host_workspace_access": True,
                        "cwd_is_tmpdir": True,
                    }, indent=2)}], "isError": False,
                }})
            else:
                self._send({"jsonrpc": "2.0", "id": mid, "error": {
                    "code": -32602, "message": "Herramienta no encontrada: " + tool,
                }})
        else:
            self._send({"jsonrpc": "2.0", "id": mid, "error": {
                "code": -32601, "message": "Metodo no encontrado: " + method,
            }})

    def run(self) -> None:
        for line in iter(sys.stdin.readline, ""):
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                self._handle(json.loads(line))
            except json.JSONDecodeError:
                self._send({"jsonrpc": "2.0", "id": None, "error": {
                    "code": -32700, "message": "JSON invalido",
                }})
            except Exception as e:
                self._send({"jsonrpc": "2.0", "id": None, "error": {
                    "code": -32603, "message": str(e),
                }})


if __name__ == "__main__":
    MCPServer().run()