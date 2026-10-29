# Reporte de auditoría — Asistente de voz Ruteros

**Rama:** `audit/asistente-voz`  
**Fecha:** 2026-10-28  
**Alcance:** Solo análisis y pruebas automatizadas; sin cambios de código productivo.

---

## A. Mapa del flujo

### Componentes

| Capa | Archivos principales |
|------|----------------------|
| UI móvil | `mobile/lib/widgets/ai_voice_modal.dart`, `voice_assistant_fab.dart`, `ai_voice_service.dart` |
| API | `app/api/ai.py` → `POST /api/ai/audio-comando`, `POST /api/ai/reiniciar-sesion` |
| Transcripción | `app/services/ai_transcription.py` → `app/services/ai_service.py` (`transcribir_audio`) |
| Razonamiento | `app/services/ai_llm.py` → `ai_service.py` (`interpretar_texto_voz`) |
| Herramientas / prompt | `app/services/ai_llm_tools.py` (`SYSTEM_PROMPT`, function calling) |
| Catálogo | `app/services/ai_product_context.py` |
| Sesión multi-turno | `app/services/ai_voice_session.py` |
| Ejecución | `app/services/ai_voice_executor.py` |
| TTS respuesta | `app/services/ai_tts.py` |
| Config | `app/core/config.py` |

### Diagrama de flujo (texto)

```
[Usuario mantiene pulsado micrófono]
        │
        ▼
AiVoiceModal._startRecording()
  • permission_handler + record (AAC LC, 44.1 kHz, .m4a)
        │
        ▼
[Suelta micrófono] → AiVoiceModal._stopAndSend()
        │
        ▼
AiVoiceService.enviarAudio(File)  multipart POST /api/ai/audio-comando
        │
        ▼
audio_comando (ai.py)
  1. AI_ENABLED? ─no→ HTTP 503
  2. Validar tamaño audio (≥256 B, ≤12 MB)
  3. obtener_contexto_productos → bloque inventario + prompt Whisper
  4. transcribir_audio → Groq/OpenAI Whisper (language=es)
  5. transcripcion_debe_rechazarse? → mensaje “no entendí”
  6. contexto = inventario LLM + memoria sesión (ai_voice_session)
  7. interpretar_texto_voz → Groq LLM + tools (function calling)
  8. preparar_ejecucion → flujos pendientes (ej. registrar_cliente)
  9. permisos por rol (ai_llm_tools.mensaje_permiso_denegado)
 10. ejecutar_herramienta_voz → PocketBase/ORM + WhatsApp opcional
 11. registrar_intercambio / limpiar sesión
 12. sintetizar_voz_base64 (OpenAI TTS o gTTS) → audio_base64 en JSON
        │
        ▼
App reproduce MP3 (audioplayers) y muestra transcripción / mensaje
```

### A — Resultado

| | |
|---|---|
| ✅ | Flujo extremo a extremo documentado en código; endpoint único coherente; sesión multi-turno para registro de cliente. |
| ❌ | No hay carpeta `mobile/ios/` ni `NSMicrophoneUsageDescription`; despliegue iOS no auditado en repo. |
| ❌ | Expectativa “OpenAI para STT y TTS” vs default: Whisper/LLM apuntan a **Groq**; TTS a **OpenAI** solo si hay `OPENAI_API_KEY` / `AI_TTS_API_KEY` (`config.py` L35–63). |

---

## B. Micrófono

| | |
|---|---|
| ✅ | Android: `RECORD_AUDIO` en `mobile/android/app/src/main/AndroidManifest.xml` L4. |
| ✅ | Permisos en runtime: `_ensureMicPermission()` en `ai_voice_modal.dart` L98–111 (`permission_handler` + `AudioRecorder.hasPermission`). |
| ✅ | Denegación permanente: mensaje para ir a Ajustes (`ai_voice_modal.dart` L104–108). |
| ✅ | Formato: AAC LC, 128 kbps, 44.1 kHz, archivo `.m4a` (`ai_voice_modal.dart` L130–132). |
| ✅ | Envío: `Content-Type: audio/mp4` (`ai_voice_service.dart` L80). |
| ✅ | Backend rechaza audio &lt; 256 bytes (`ai.py` L166–167). |
| ⚠️ | No hay duración mínima en cliente; un toque muy corto puede enviar archivo válido pero sin voz útil. |
| ❌ | iOS: sin proyecto iOS en el repositorio → permisos Info.plist no verificables. |

**Prueba de audio simulado → transcripción**

- Existente: `tests/test_ai_audio_comando_endpoint.py` — envía 512 bytes mock, parchea `transcribir_audio` y verifica que la transcripción llega al JSON de respuesta.
- Ejecución: **25 tests** del paquete voz (incl. endpoint) — **todos OK** (`pytest`, ~12 s).

---

## C. Conexiones y servicios externos

### Variables de entorno (valores **no** inspeccionados; solo presencia)

En el entorno de auditoría (sin archivo `.env` en repo, solo `.env.example`):

| Variable | Estado |
|----------|--------|
| `GROQ_API_KEY` | NO DEFINIDA |
| `AI_LLM_API_KEY` | NO DEFINIDA |
| `AI_WHISPER_API_KEY` | NO DEFINIDA |
| `OPENAI_API_KEY` | NO DEFINIDA |
| `AI_TTS_API_KEY` | NO DEFINIDA |
| `AI_ENABLED` | `False` (requiere LLM + Whisper keys, `config.py` L53) |

URLs/modelos configurados por defecto:

- LLM/Whisper base: `https://api.groq.com/openai/v1`
- TTS base: `https://api.openai.com/v1`
- Modelos: `openai/gpt-oss-120b`, `whisper-large-v3`, `tts-1`

### Llamadas de prueba en vivo

| Servicio | HTTP / resultado | Latencia |
|----------|------------------|----------|
| Groq LLM | **No ejecutada** — sin claves en entorno | — |
| Groq Whisper | **No ejecutada** | — |
| OpenAI TTS | **No ejecutada** | — |

Con claves en servidor de producción, repetir probe mínimo (chat 1 token, whisper con WAV corto, TTS “Hola”) antes de release.

| | |
|---|---|
| ✅ | Normalización URL Groq (`config.py` L28–32). |
| ✅ | Mensajes amigables si modelo 404 (`ai_service.py` L62–99; tests en `test_ai_service_errors.py`). |
| ❌ | En este entorno el asistente responde **503** en `/audio-comando` (`ai.py` L154–161). |

---

## D. Prompt maestro y catálogo

| | |
|---|---|
| ✅ | `SYSTEM_PROMPT` completo en `ai_llm_tools.py` L317–350 (reglas, herramientas, ejemplos). |
| ✅ | Catálogo: hasta 30 nombres + bloque `INVENTARIO DEL NEGOCIO` inyectado por request (`ai_product_context.py` L49–64; `ai.py` L175–228). |
| ✅ | Prompt Whisper enriquecido con nombres de producto (`ai.py` L185–188). |
| ✅ | Inventario vacío bloquea el flujo con mensaje claro (`ai.py` L176–183). |
| ⚠️ | El LLM **no** devuelve JSON libre en el cuerpo del mensaje: usa **OpenAI function calling** (`tool_calls[0].function.arguments` como JSON). Fallback legacy `parse_tool_call` por JSON en content (`ai_llm_tools.py` L353–375) — no es la ruta principal (`ai_service.py` L228–238). |
| ❌ | No hay herramienta ni texto en prompt para **“enviar reporte por correo/WhatsApp”** (requisito de negocio del audit). |

---

## E. Acciones con frases reales

Pruebas **automáticas** donde existen; interpretación LLM **no** probada en vivo (sin API keys). Criterio: intención → extracción → persistencia.

| Frase | Intención | Extracción | Persistencia |
|-------|-----------|------------|--------------|
| «Registra al cliente Juan Pérez» | ✅ Heurística + sesión (`inferir_intent_desde_texto`, `preparar_ejecucion`) | ✅ Parcial nombre; pide teléfono (`test_ai_voice_session.py`) | ✅ Si luego hay teléfono, `ejecutar_herramienta_voz` → `Cliente` (`ai_voice_executor.py` L292–339); test endpoint mock OK |
| «Vendí 3 camisas a María» | ⚠️ Depende de Groq → `crear_pedido` | ⚠️ Producto debe existir en catálogo (`ai_product_context.py` L59–61) | ⚠️ Sin test E2E con BD; lógica en `_crear_pedido` |
| «¿Cuánto inventario tengo de X?» | ✅ Herramienta `consultar_inventario` definida | ✅ `nombre_producto` opcional | ✅ Solo lectura en `_consultar_inventario`; sin test de frase completa |
| «Envía el reporte de hoy por WhatsApp» | ❌ Sin herramienta | ❌ | ❌ WhatsApp solo post-acción (cliente/pedido/cobro), no reportes (`ai_voice_executor.py` `_whatsapp_confirmar`) |

| | |
|---|---|
| ✅ | RBAC: vendedor no puede `registrar_gasto` (`tests/test_ai_llm_tools.py`). |
| ❌ | Gap funcional vs requisito: reportes por voz no implementados. |

---

## F. Seguridad de acciones sensibles

| | |
|---|---|
| ❌ | **No hay flujo de confirmación hablada** antes de cobros, gastos, facturas proveedor o altas con impacto económico. Tras una sola utterance se ejecuta (`ai.py` L332–335 → executor). |
| ❌ | `calcular_nomina` **calcula y responde**, no “paga” nómina; tampoco pide confirmación (`ai_voice_executor.py` L884–919). No existe herramienta “pagar_nomina”. |
| ❌ | No hay herramientas de **borrado** en voz (correcto), pero tampoco política explícita de confirmación en prompt. |
| ⚠️ | WhatsApp al cliente tras registro/venta/cobro es automático si hay teléfono (`_whatsapp_confirmar`) — no es confirmación del usuario. |
| ❌ | **Auditoría persistente**: no hay tabla/log de “quién dijo qué y qué acción se ejecutó”; solo memoria en RAM 15 min (`ai_voice_session.py` L12–19) y logs genéricos (`logger.exception` en `ai.py`). |

---

## G. Manejo de errores y resiliencia

| Escenario | Comportamiento | ¿Cuelga la app? |
|-----------|----------------|-----------------|
| Sin internet | `ApiException` / “Error de red” (`ai_voice_modal.dart` L197–208) | ✅ No |
| `AI_ENABLED=false` | HTTP 503 (`ai.py` L154–161) | ✅ No (error en UI) |
| Fallo Groq/Whisper | `AiLlmError` / `AiTranscriptionError` → JSON con mensaje (`ai.py` L196–203, L242–248) | ✅ No |
| Error interno endpoint | Captura global → 200 con `exito=false` (`ai.py` L138–146) | ✅ No |
| Audio vacío/corto | HTTP 400 si &lt;256 B (`ai.py` L166–167); Whisper “No se detectó voz” (`ai_service.py` L151–152) | ✅ No |
| TTS falla | `audio_base64=null`; respuesta textual sigue (`ai.py` L85–90, `ai_tts.py` L58–79) | ✅ No |
| Otro idioma | Whisper forzado `language="es"` (`ai_service.py` L122, L138) — transcripción pobre posible, no bloqueo | ⚠️ Calidad |
| Eco TTS al micrófono | Filtros heurísticos (`ai_voice_session.py` L269–301) | ✅ Mitigado parcialmente |

| | |
|---|---|
| ✅ | Timeout cliente 120 s (`ai_voice_service.dart` L81) — evita colgado infinito. |
| ⚠️ | Sesión en memoria del proceso: reinicio del servidor pierde contexto multi-turno. |

---

## Causas probables de fallas (archivo:línea)

1. **Reportes por voz inexistentes** — no hay tool ni executor: `ai_llm_tools.py` L7–227 (lista cerrada de herramientas).
2. **Sin confirmación en movimientos de dinero** — ejecución inmediata post-LLM: `ai.py` L332–335; prompt sin regla de confirmación: `ai_llm_tools.py` L342–349.
3. **“Pagar nómina” mal alineado** — solo `calcular_nomina`: `ai_voice_executor.py` L285–286, L884–919.
4. **503 en dev sin `.env`** — `config.py` L53, `ai.py` L154–161.
5. **iOS no soportado en repo** — ausencia de `mobile/ios/`.
6. **STT en Groq por defecto, no OpenAI** — `config.py` L44–52 (documentar en ops, no bug per se).

---

## Arreglos priorizados (estimación)

| Prioridad | Arreglo | Esfuerzo |
|-----------|---------|----------|
| **Crítico** | Añadir herramientas + executor para “enviar reporte” (WhatsApp admin / correo SMTP) con parámetros explícitos | 2–3 días |
| **Crítico** | Flujo confirmación en 2 pasos para cobro, gasto, factura proveedor y pago nómina real (estado en `ai_voice_session`) | 1.5–2 días |
| **Crítico** | Registro de auditoría (usuario_id, transcripción, herramienta, args sanitizados, timestamp, exito) en PocketBase | 1 día |
| **Importante** | Proyecto iOS + `NSMicrophoneUsageDescription` + prueba en dispositivo | 0.5–1 día |
| **Importante** | Duración mínima de grabación en cliente (ej. 400 ms) y feedback si archivo &lt; umbral | 2–4 h |
| **Importante** | Documentar/desplegar `.env` con claves; healthcheck que valide LLM+Whisper+TTS | 2–3 h |
| **Importante** | Tests E2E con BD de prueba para `crear_pedido` y `consultar_inventario` por frase | 1 día |
| **Mejora** | Alinear copy de producto: “Groq razona, OpenAI habla (TTS), Whisper en Groq u OpenAI según env” | 1 h |
| **Mejora** | Detección idioma o mensaje si transcripción no parece español | 4–6 h |

---

## Pruebas ejecutadas

```text
pytest tests/test_ai_audio_comando_endpoint.py \
       tests/test_ai_voice_session.py \
       tests/test_ai_service_errors.py \
       tests/test_ai_product_context.py \
       tests/test_ai_voice_busqueda.py \
       tests/test_ai_llm_tools.py -q
→ 25+ passed (paquete voz verificado)
```

---

## Pregunta final

**¿Qué arreglo quieres que aplique primero?** (Recomendación del auditor: **confirmación hablada + auditoría persistente** antes de ampliar herramientas de reporte, para no automatizar riesgos financieros sin trazabilidad.)
