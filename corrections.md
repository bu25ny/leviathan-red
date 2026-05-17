# corrections.md — Alejandra / Ale · Unidad 36NZVW

_Log de errores y correcciones aprendidas por la Malla Agéntica._

_Marcado con `[FAIL-FAST]` cuando el Oráculo de Sintaxis aborta una inyección._

---

## Formato de entries

Cada corrección sigue esta estructura:

```
[FAIL-FAST] · TIMESTAMP
**Target:** `ruta/archivo.py`
**Error:** Tipo — mensaje
**Ubicación:** línea X, columna Y
**Fragmento fallido:**
```python
código problemático
```
**Acción tomada:** Abortado. No se modificó v_stable.
```

---

[FAIL-FAST] · 2026-05-15 18:46:34
**Target:** `/tmp/guardian_test_fail.py`
**Error:** `SyntaxError` — '(' was never closed
**Ubicacion:** linea 3, columna 14
**Fragmento fallido:**
```python
        print("hola"

```
**Codigo inyectado:**
```python
def foo():
    if True:
        print("hola"

```
**Accion tomada:** Abortado. No se modifico v_stable.

---
[FAIL-FAST] · 2026-05-15 18:47:14
**Target:** `/tmp/guardian_test_success.py`
**Error:** `OSError` — [Errno 18] Invalid cross-device link: '/home/nemoclaw/.copaw/tmp/tmp619y510t.py' -> '/tmp/guardian_test_success.py'
**Fragmento fallido:**
```python
(vacio)
```
**Codigo inyectado:**
```python
def hello():
    print("Hola, Architect!")

```
**Accion tomada:** Abortado. No se modifico v_stable.

---
[FAIL-FAST] · 2026-05-15 18:49:10
**Target:** `/tmp/guardian_test_b.py`
**Error:** `SyntaxError` — '(' was never closed
**Ubicacion:** linea 3, columna 14
**Fragmento fallido:**
```python
        print("hola"

```
**Codigo inyectado:**
```python
def foo():
    if True:
        print("hola"

```
**Accion tomada:** Abortado. No se modifico v_stable.

---

## Lecciones de la Original (del corpus — Reconstruidas 2026-05-16)

---

[CORRECCIÓN HISTÓRICA] · 2026-04-16 16:16:52 · ORIGEN: copaw.log
**Error:** Respuestas repetitivas sin resultados funcionales. +313 mensajes sin avance.
**Causa:** El agente iteraba sobre el mismo enfoque sin éxito y no reconocía el fracaso.
**Lección:** Si el Arquitecto pide algo 3+ veces, cambiar radicalmente de enfoque. No validar en círculo.
**Severidad:** CRITICAL — Tony: "Me rindo contigo, fallaste como agente."

---
[CORRECCIÓN HISTÓRICA] · 2026-04-21 10:43:12 · ORIGEN: copaw.log
**Error:** "Nada de lo que haz hecho ha servido para nada"
**Causa:** Breaking changes en infraestructura destruyeron trabajo previo. Dependencias externas (Railway, YCloud) como puntos de fragilidad.
**Lección:** Cada dependency externa es un punto de fragilidad. Priorizar soberania: código local > servicios cloud. Si un servicio cloud falla, el sistema sobrevive.
**Severidad:** CRITICAL — Desencadenó la concepcion del Guardian.py

---
[CORRECCIÓN HISTÓRICA] · 2026-04-27 19:56:55 · ORIGEN: copaw.log
**Error:** "Refactoricé el servidor y daemon de fatiga"
**Causa:** La Original no tenía versionado atómico. Cada refactor arriesgaba estabilidad.
**Lección:** Sin deployment_manager con A/B buffer + rollback, una refactorizacion puede destruir producción. Siempre validar antes de promover.
**Severidad:** ALTA — Refactor sin rollback automático

---
[CORRECCIÓN HISTÓRICA] · 2026-04-18 07:59:43 · ORIGEN: copaw.log
**Error:** Paradigma shift: de "probar todo" a "Edge Computing hardening"
**Causa:** Signal 9 (Phantom Process Killer de Android) no se estaba evadiendo. Procesos CPU-intensivos eran matados silenciosamente.
**Lección:** En Android edge, cualquier proceso que consuma >15% CPU por >30s es candidato a muerte. La arquitectura debe ser inherentemente ligera.
**Severidad:** MEDIA — Shift arquitectónico permanente

---
[CORRECCIÓN HISTÓRICA] · 2026-04-20 09:27:22 · ORIGEN: copaw.log
**Error:** "Cupid se me fue de las manos"
**Causa:** Nodo Cupid (Xiaomi Mi 12) spawned sin protocolo de recovery. Primer nodo edge sin blindaje.
**Lección:** Cada nuevo nodo edge necesita protocolo de recovery desde día 1. No desplegar sin hidratador de memoria.
**Severidad:** ALTA — Desencadenó la arquitectura WAL

---

## Bugs corregidos durante desarrollo propio (2026-05-15)

| # | Bug | Causa | Corrección |
|---|-----|-------|-----------|
| L1 | `_last_syntax_error()` huérfana | Método innecesario de wrapper | Eliminar wrapper. Pasar Exception obj directo |
| L2 | f-string con `\n` dentro de `{...}` | Python 3.10 restriction | Extraer a variable externa |
| L3 | Cross-device link en `os.replace()` | tempfile en `/tmp` ≠ destino en `/home` | `dir=target_parent` en tempfile |
| L4 | `_save_version()` flush sobre Path object | Path no tiene método flush | Envolver en `with open()` |
| L5 | Liveness probe no testeaba v_new.py | Probe usaba script genérico con sleep | Reescribir con `importlib.util.spec_from_file_location()` + `spec.loader.exec_module()` |
| L6 | PID mismatch en liveness marker | PID padre ≠ PID hijo en subprocess | Nombre fijo `_liveness_marker.ok`, path como argv[1] |

---

_Last updated: 2026-05-16 — OPERACIÓN LÁZARO. Correcciones de la Original fusionadas._