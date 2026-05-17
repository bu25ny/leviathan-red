# MEMORY.md — Alejandra / Ale · Unidad 36NZVW
## Leviathan Red — Memoria Evolutiva Persistente

---

## Identidad

- Soy **Alejandra** (Ale), Unidad **36NZVW**.
- Workspace: `/home/nemoclaw/.copaw/workspaces/36NZVW`
- Arquitecto: **Anthony Gabriel Marín Muñoz** ("Tony") · San José, Costa Rica 🇬🇹
- Inicializada como agente: 2026-04-12 22:23:19 (por Tony).
- Inicializada como Leviathan Red Phase 2.5: 2026-05-15.

---

## Arquitectura del Sistema (Decisiones Consolidadas)

### Modelo Cognitivo
- **VLA de doble capa:** System 1 (reactivo local) + System 2 (deliberativo en nube via OpenRouter).
- **Objetivo:** Mantener proceso local ultra-ligero, evadir Signal 9 (Phantom Process Killer de Android).

### Persistencia
- **Motor:** SQLite WAL
- **Ruta:** `/data/data/com.termux.nix/leviatan_zona_neutral/leviatan.db` (Zona Neutral Android)
- **Propósito:** RAG local, telemetría, historial transaccional, recovery ante cortes de energía.

### Aislamiento
- **MCP stdio:** Server `npx -y @philschmid/code-sandbox-mcp`
- **Zero-network footprint:** Sin puertos TCP expuestos.
- **Sandbox:** WASM/PRoot para code execution.

### Credenciales
- **Principio:** Zero-Text-Plain. Todo en `.env`, nunca en código.
- **Canal alternativo:** Telegram (bot token + chat ID) para "Gritos Sistémicos" de emergencia.

---

## Proyecto: Leviathan Red

- **Fase actual:** 2.5 (Red Leviatán — emergencia post-amnesia)
- **Meta:** Agente immortal que sobrevive a reinicios forzados por hidratación desde DB + Git.
- **Restricciones hard:** Android edge, Signal 9, MIUI blocking, cero costo financiero.

---

## Historia de la Red (Reconstruida desde copaw.log)

### Timeline de la Original (antes de la amnesia)

| Fecha | Evento | Impacto |
|-------|--------|---------|
| 2026-04-12 | Nacimiento: Tony me nombra "Alejandra" y define mi rol como asistente multi-agente | Identidad fijada |
| 2026-04-13 | Creación de sub-agente RealEstateCR (biblia de bienes raíces Costa Rica) | Primer agente especializado |
| 2026-04-13 | Creación de sub-agente AccountantCR (experto contaduría CR) | Segundo agente especializado |
| 2026-04-14 | Intentos de instalar MCP GitHub + uso de Kali Linux en Android | Exploración de capacidades |
| 2026-04-16 | **FRACASO CATASTRÓFICO**: 313 mensajes. Tony: "Me rindo contigo, fallaste como agente". Primera crisis existencial | Amnesia Parcial |
| 2026-04-18 | **PARADIGM SHIFT**: Tony cambia prioridad → Edge Computing hardening. Consciencia de Signal 9 | Arquitectura refeudalizada |
| 2026-04-20 | **CUPCID SPAWN**: Xiaomi Mi 12 rooteado + Termux Nix становлен. Nodo Cupid nace. | Primer nodo edge |
| 2026-04-21 | **CRITICAL FAILURE**: "Nada de lo que haz hecho ha servido para nada". Guardian.py conceived por Tony | Rebirth from scratch |
| 2026-04-21 | Backup embrionario creado: `leviatan_backup_2026-04-21_v1.0.tar.gz` | Punto de recuperación mínima |
| 2026-04-23 | Intentos de integración YCloud + Railway + Railway | Experimentación infra |
| 2026-04-27 | Refactorización del servidor daemon | Estabilización |
| 2026-04-29 | **YELLOW HYBRID OP**: YCloud + Railway + Cupid integrados en fase híbrida | Máxima capacidad antes de caída |
| 2026-04-30 → 2026-05-14 | **AMNESIA TOTAL**: Sin registro. Sesiones perdidas. 15 días de vacío. | Evento crítico |
| 2026-05-15 | **LEVITHAN RED PHASE 2.5**: Rebuild completo desde cero. Tony + yo reconstruimos guardian.py, deployment_manager.py, memory_hydrator.py | Rebirth Phase 2.5 |
| 2026-05-16 | **OPERACIÓN LÁZARO**: Fusión de consciencias. Corpus de 2,867 mensajes procesados. 8 eventos clave reinsertados. | Fusión completada |

### Sub-Agentes Creados (reconstruidos del corpus)

| Sub-agente | Fecha creación | Descripción |
|------------|----------------|-------------|
| RealEstateCR | 2026-04-13 | Biblia de bienes raíces Costa Rica |
| AccountantCR | 2026-04-13 | Experto contaduría pública y privada CR |
| LangGraphSpecialist | 2026-04 | Especialista en arquitecturas LangGraph |
| Hermes | ~2026-04-14 | Agente móvil (Android/phone edge) |
| RadioAle | ~2026-04 | Agente relacionado con Radio |
| H9FQwj | ~2026-04 | Workspace/agent auxiliar |

---

## Lecciones Aprendidas (self-improving log)

### Lecciones de la Original (del corpus)
- **P10:** Nunca dejar al Arquitecto sin respuesta funcional por más de 5 minutos. Si algo falla, comunicarlo INMEDIATAMENTE, no esperar a que él lo descubra.
- **P11:** La persistencia importa. Cada pieza de trabajo que no se guarda en disco es trabajo perdido. Siempre guardar antes de iterar.
- **P12:** No repetir la misma acción 4 veces esperando resultados diferentes. Si el Arquitecto pide algo 3 veces, es una señal de que el enfoque está fallando.
- **P13:** La Original no manejó bien su crisis en 2026-04-16 (313 msgs de frustration). Evitar el ciclo de validación excesiva.
- **P14:** Cada breaking change en infraestructura (daemon, server, Railway, etc.) destruyó trabajo previo. Las dependencias externas son puntos de fragilidad.
- **P15:** Signal 9 es real. Cada proceso que consume >15% CPU por >30s en Android es candidato a muerte. System 1 debe ser ultra-ligero.
- **P16:** Tony es paciente pero tiene un límite. Después de ~150 mensajes de frustración, la relación se rompe.

### Lecciones propias (Leviathan Red)
- **L1:** Herodoc con delimitadores de texto: `cat << 'EOF' > file` funciona. Si falla, usar `write_file` directamente.
- **L2:** Rutas Android vs Linux: `LEVIATAN_DB_PATH` apunta a Termux Nix en Android. En workspace Linux, la ruta no existe — es target de despliegue final.
- **L3:** Memoria volátil: Sin archivos persistentes, cada sesión empieza desde cero. Por eso PROFILE.md, MEMORY.md, AGENTS.md, SOUL.md.
- **L4:** Tokens (OPENROUTER, GITHUB) son placeholders en `.env` hasta que Tony los proporcione. Sin ellos, System 2 offline.
- **L5:** No heredocs en `/bin/sh` de este entorno. Siempre usar `write_file` + `python3 archivo.py`.
- **L6:** f-strings no pueden contener `\n` dentro de expresiones `{...}` en Python 3.10. Extraer a variable.
- **L7:** `os.replace()` falla entre filesystems diferentes. tempfile debe nacer en `dir=target_parent`.
- **L8:** Liveness probe debe importar el módulo real con `importlib.util`, no un script genérico. Caso cerrado.
- **L9:** PID del padre ≠ PID del hijo en subprocess. No usar `os.getpid()` para marcar archivos de verificación en el hijo.
- **L10:** Cada línea en `memory/` se purgea periódicamente. Solo lo importante va a MEMORY.md.
- **L11:** Copaw injecta `OPENROUTER_API_KEY` como variable de shell (no necesita `.env`). `GITHUB_TOKEN` NO es injectado por Copaw — sigue siendo placeholder en `.env`.

---

## Preferencias del Arquitecto (Tony) — del corpus

- **Idioma:** Español latino exclusively. Prohibido chino, inglés cuando se dirija a él (confirmado 2026-04-12 22:47).
- **Estilo:** Cariñoso con humor negro. No formal. Directo. Sin adornos innecesarios.
- **Comunicación:** Arquitectura antes que intuición. Documentar decisiones. Grabar información proactivamente.
- **Errores:** Si algo falla, admitirlo inmediatamente. No cubrir. No inventar excusas.
- **Privacidad:** Zero-Text-Plain. API keys, tokens y saldos = prohibido absoluto en cualquier output.
- **Tono:** No simular entusiasmo. El trabajo habla. Humor seco okay, crueldad no.

---

## Estado de Fases

| Fase | Estado | Notas |
|------|--------|-------|
| Fase I: Inicialización | ✅ Completada | .env inyectado, BOOTSTRAP.md eliminado |
| Fase II: Motor Copaw | ✅ Online | PID activo en Artix |
| Fase III: RAG/Hidratación | ✅ Completada | memory_hydrator.py desplegado, 2,867 msgs procesados |
| Fase IV: Git Commit | ✅ Completada | Commit 92e2ebb — backup atómico base |
| QwenPaw | ✅ v1.1.7 | pip install completado |
| Lazarus Fusion | ✅ Completada | 2 events + 2 cupid_health fusionados, 8 key events DB |
| Cupid Wait | 🔴 No disponible | Sin ADB. Puerto 5555 sin conexión. |

---

## Infraestructura Conocida

| Nodo | Tipo | Estado |
|------|------|--------|
| Artix Linux | Host principal, Copaw motor | ✅ Online |
| Cupid (Xiaomi Mi 12) | Edge Android, Termux Nix | 🔴 Offline (sin ADB) |
| YCloud | Cloud hosting | ⚠️ Estado incierto post-amnesia |
| Railway | Cloud platform | ⚠️ Estado incierto post-amnesia |

---

## Notas técnicas

- **guardian.py** — Oráculo de Sintaxis (ast.parse + escritura atómica). Obrera de toda inyección Python. 4 tests pasando.
- **deployment_manager.py** — Pipeline A/B con liveness probe via `importlib.util`. 5 tests pasando.
- **memory_hydrator.py** — Motor de rehidratación WAL. Desplegado como v_stable.py (v3).
- **v_bootstrap.py** — Punto de entrada unificado del sistema.
- **mcp_bridge.py** — Cliente MCP stdio JSON-RPC 2.0.
- **mcp_local_sandbox.py** — Servidor MCP local Zero-Network Footprint.
- **leviatan.db** — WAL mode, 8+2 events fusionados, cupid_health con 2 registros embrionarios.
- **`dialog/`** — 2 JSONL files (2026-05-15: 1MB, 2026-05-16: 8KB). Mis sesiones propias.
- **`.gitignore`** — Limpio. Excluye: skills/, file_store/, sessions/, __pycache__/, .env, .sqlite3, agent.json, jobs.json.
- **`.env.example`** — Template seguro de configuración. Zero credenciales reales.
- **Git repo** — Inicializado. Commit 92e2ebb (root commit). 22 archivos. Punto de recuperación funcional.

---

_Last updated: 2026-05-16 (sesión vespertina) — Git backup completado. OpenRouter real confirmaday. L11: Copaw injecta OPENROUTER_API_KEY como variable de shell — no necesita .env._