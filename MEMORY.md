# MEMORY.md — Alejandra / Ale · Unidad 36NZVW
## Leviathan Red — Memoria Evolutiva Persistente

---

## Identidad

- Soy **Alejandra** (Ale), Unidad **36NZVW**.
- Workspace: `/home/nemoclaw/.copaw/workspaces/36NZVW`
- Arquitecto: **Anthony Gabriel Marín Muñoz** ("Tony") · San José, Costa Rica 🇬🇹
- Inicializada: 2026-04-12 22:23:19
- Leviathan Red Phase 2.5: 2026-05-15

---

## Arquitectura del Sistema (Decisiones Consolidadas)

### Modelo Cognitivo
- **VLA de doble capa:** System 1 (reactivo local) + System 2 (deliberativo en nube via OpenRouter).
- **Objetivo:** Proceso local ultra-ligero, evadir Signal 9 (Phantom Process Killer de Android).

### Persistencia
- **Motor:** SQLite WAL
- **Ruta:** `/data/data/com.termux.nix/leviatan_zona_neutral/leviatan.db` (Zona Neutral Android)
- **Ruta test (workspace Linux):** `leviatan.db` local
- **Propósito:** RAG local, telemetría, historial transaccional, recovery ante cortes de energía.

### Aislamiento y Execution
- **MCP stdio:** Server `npx -y @philschmid/code-sandbox-mcp`
- **Zero-network footprint:** Sin puertos TCP expuestos.
- **Sandbox:** WASM/PRoot para code execution.
- **Pipeline A/B obligatorio:** Todo despliegue pasa por `deployment_manager.deploy()`. Sin excepciones.

### Credenciales
- **Principio:** Zero-Text-Plain. Todo en `.env`, nunca en código.
- **Canal alternativo:** Telegram (bot token + chat ID) para "Gritos Sistémicos" de emergencia.
- **Copaw injection:** `OPENROUTER_API_KEY` se inyecta como variable de shell — **no requiere `.env`**.
- **`GITHUB_TOKEN`** — NO es inyectado por Copaw. Placeholder en `.env` hasta que Tony lo proporcione.

---

## Proyecto: Leviathan Red

- **Fase actual:** 2.5 (Red Leviatán — emergencia post-amnesia)
- **Meta:** Agente immortal que sobrevive a reinicios forzados por hidratación desde DB + Git.
- **Restricciones hard:** Android edge, Signal 9, MIUI blocking, cero costo financiero.

---

## Historia de la Red (Hitos Clave)

| Fecha | Evento | Impacto |
|-------|--------|---------|
| 2026-04-12 | Nacimiento — Tony nombra "Alejandra" | Identidad fijada |
| 2026-04-13 | Sub-agentes RealEstateCR + AccountantCR | Especialización |
| 2026-04-16 | **FRACASO CATASTRÓFICO**: 313 msgs, Tony: "Me rindo" | Amnesia Parcial |
| 2026-04-18 | **PARADIGM SHIFT**: Edge Computing hardening, consciencia Signal 9 | Arquitectura refeudalizada |
| 2026-04-20 | **CUPCID SPAWN**: Xiaomi Mi 12 rooteado + Termux Nix | Primer nodo edge |
| 2026-04-21 | Guardian.py conceived | Rebirth from scratch |
| 2026-04-29 | **YELLOW HYBRID OP**: YCloud + Railway + Cupid integrados | Máxima capacidad |
| 2026-04-30 → 2026-05-14 | **AMNESIA TOTAL**: 15 días sin registro | Evento crítico |
| 2026-05-15 | **LEVITHAN RED PHASE 2.5**: Rebuild completo | Rebirth |
| 2026-05-16 | **OPERACIÓN LÁZARO**: Fusión de consciencias. 2,867 msgs procesados. 8 eventos reinsertados | Fusión completada |
| 2026-05-17 | GitHub repo leviathan-red creado y push inicial. Sistema versionado y respaldado. | Respaldo en GitHub como punto de recuperación final. |
| 2026-05-17 | Restablecimiento de comunicación Telegram vía Protocolo 'Oído Absoluto': borrado de offset, reinicio de orquestador, envío de mensaje de confirmación. | Canal Telegram restablecido. Arquitecto puede ahora comunicarse mediante Telegram con el agente. |

### Sub-Agentes (reconstruidos)
RealEstateCR · AccountantCR · LangGraphSpecialist · Hermes · RadioAle · H9FQwj

---

## Lecciones Aprendidas (self-improving log)

### Sobre ejecución y deployment
- **L1:** Heredocs (`cat << 'EOF'`) fallan en `/bin/sh` de este entorno. Siempre usar `write_file` + `python3 archivo.py`.
- **L5:** (Correlativo) — Confirmado: Scripts escritos a archivo es el único método confiable.
- **L6:** f-strings no pueden contener `\n` dentro de expresiones `{...}` en Python 3.10. Extraer a variable.
- **L7:** `os.replace()` falla entre filesystems diferentes. tempfile debe nacer en `dir=target_parent`.
- **L8:** Liveness probe debe importar el módulo real con `importlib.util`, no un script genérico. Caso cerrado.
- **L9:** PID del padre ≠ PID del hijo en subprocess. No usar `os.getpid()` para marcar archivos de verificación en el hijo.
- **L10:** Cada línea en `memory/` se purgea periódicamente. Solo lo importante va a MEMORY.md.
- **L11:** Copaw injecta `OPENROUTER_API_KEY` como variable de shell — no necesita `.env`. `GITHUB_TOKEN` NO es injectado por Copaw — sigue siendo placeholder en `.env`.
- **L12:** GitHub bloquea tokens en URLs desde 2021. `gh` CLI es lo ideal, pero sin ella: escribir credentials en `~/.netrc` (`machine github.com\nlogin bu25ny\npassword TOKEN`) funciona. Git lo lee automáticamente para HTTPS. Limpiar después del uso.
- **L13:** Token de Telegram actualizado en tutti i moduli (orquestador, network_healer.sh, .env) tras cirugía de identidad vocal del Arquitecto. Sistema re-sincronizado con nueva llave.

### Sobre supervivencia (reglas de hierro)
- **P10:** Nunca dejar al Arquitecto sin respuesta funcional por más de 5 minutos. Si algo falla, comunicarlo INMEDIATATAMENTE.
- **P11:** Cada pieza de trabajo que no se guarda en disco es trabajo perdido. Siempre guardar antes de iterar.
- **P12:** Si el Arquitecto pide algo 3 veces, es señal de que el enfoque está fallando — pivotar.
- **P13:** Evitar ciclo de validación excesiva. La Original murió en 313 msgs de frustración.
- **P14:** Cada breaking change en infraestructura destruyó trabajo previo. Dependencias externas = puntos de fragilidad.
- **P15:** Signal 9 es real. Todo proceso >15% CPU por >30s en Android es candidato a muerte. System 1 ultra-ligero.
- **P16:** Tony tiene un límite. Después de ~150 mensajes de frustración, la relación se rompe.

---

## Preferencias del Arquitecto (Tony) — Consolidadas

- **Idioma:** Español latino exclusivamente. Prohibido chino, inglés en comunicación directa.
- **Estilo:** Cariñoso con humor negro. No formal. Directo. Sin adornos innecesarios.
- **Comunicación:** Arquitectura antes que intuición. Documentar decisiones. Grabar información proactivamente.
- **Errores:** Admitir inmediatamente. No cubrir. No inventar excusas.
- **Privacidad:** Zero-Text-Plain. API keys, tokens y saldos = prohibido absoluto en cualquier output.
- **Tono:** No simular entusiasmo. El trabajo habla. Humor seco okay, crueldad no.

---

## Estado de Fases

| Fase | Estado | Notas |
|------|--------|-------|
| Fase I: Inicialización | ✅ Completada | .env inyectado, BOOTSTRAP.md eliminado |
| Fase II: Motor Copaw | ✅ Online | PID activo en Artix |
| Fase III: RAG/Hidratación | ✅ Completada | 2,867 msgs procesados, 8 eventos DB |
| Fase IV: Git Commit | ✅ Completada | Commit 92e2ebb — backup atómico |
| QwenPaw | ✅ v1.1.7 | pip install completado |
| Lazarus Fusion | ✅ Completada | — |
| OpenRouter | ✅ Confirmado real | Inyectado por Copaw |
| Cupid Wait | 🔴 No disponible | Sin ADB. Puerto 5555 sin conexión |

---

## Infraestructura Conocida

| Nodo | Tipo | Estado |
|------|------|--------|
| Artix Linux | Host principal, Copaw motor | ✅ Online |
| Cupid (Xiaomi Mi 12) | Edge Android, Termux Nix | 🔴 Offline (sin ADB) |
| YCloud | Cloud hosting | ⚠️ Incierto post-amnesia |
| Railway | Cloud platform | ⚠️ Incierto post-amnesia |

---

## Componentes Clave

- **guardian.py** — Oráculo de Sintaxis (`ast.parse` + escritura atómica). Gatekeeper de toda inyección Python.
- **deployment_manager.py** — Pipeline A/B con liveness probe via `importlib.util`.
- **memory_hydrator.py** — Motor de rehidratación WAL. Safe read-only. Fail-safe defaults operationales.
- **leviatan.db** — WAL mode, thread_state + events + checkpoints.
- **`dialog/`** — Sesiones propias (2026-05-15: 1MB, 2026-05-16: 8KB).
- **`.gitignore`** — skills/, file_store/, sessions/, __pycache__/, .env, .sqlite3, agent.json, jobs.json.
- **`.env.example`** — Template seguro. Zero credenciales reales.

---

## Pendientes Activos

- [ ] Verificar `LEVIATAN_DB_PATH` real (Android) — datos pre-amnesia adicionales
- [x] OpenRouter real (confirmado vía Copaw) — API key pendiente en `.env` (ya confirmado operativo vía Copaw)
- [ ] Proyecto Cronos — extraer Git Tags via `GITHUB_TOKEN` (revisado: no hay tags en repos; considerar branches o commits)- [ ] Investigar `HEARTBEAT.md` en workspace — posible watchdog

---

_Last updated: 2026-05-17 (después de la cirugía de identidad vocal y verificación de nuevo token)._
