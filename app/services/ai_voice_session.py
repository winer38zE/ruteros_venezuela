"""Memoria de conversación del asistente de voz (por usuario, en proceso)."""
from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any

_TTL_SEGUNDOS = 900
_MAX_TURNOS = 8
_MAX_MENSAJES_HISTORIAL = 8  # ~4 intercambios user/assistant

_LOCK = threading.Lock()
_SESIONES: dict[str, "_SesionVoz"] = {}
# Alias legible para depuración (misma referencia que _SESIONES).
conversation_history: dict[str, "_SesionVoz"] = _SESIONES


@dataclass
class _SesionVoz:
    intent: str
    partial: dict[str, Any] = field(default_factory=dict)
    turnos: list[str] = field(default_factory=list)
    messages: list[dict[str, str]] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)


def _ahora() -> float:
    return time.time()


def _limpiar_vencidas() -> None:
    ahora = _ahora()
    vencidas = [k for k, s in _SESIONES.items() if ahora - s.updated_at > _TTL_SEGUNDOS]
    for k in vencidas:
        _SESIONES.pop(k, None)


def limpiar(usuario_id: str) -> None:
    with _LOCK:
        _SESIONES.pop(str(usuario_id), None)


def obtener(usuario_id: str) -> _SesionVoz | None:
    with _LOCK:
        _limpiar_vencidas()
        ses = _SESIONES.get(str(usuario_id))
        if ses is None:
            return None
        if _ahora() - ses.updated_at > _TTL_SEGUNDOS:
            _SESIONES.pop(str(usuario_id), None)
            return None
        return ses


def _append_mensaje(messages: list[dict[str, str]], role: str, content: str) -> list[dict[str, str]]:
    texto = (content or "").strip()
    if not texto:
        return messages
    out = list(messages)
    if out and out[-1].get("role") == role and out[-1].get("content") == texto:
        return out
    out.append({"role": role, "content": texto})
    return out[-_MAX_MENSAJES_HISTORIAL:]


def historial_mensajes_para_llm(usuario_id: str) -> list[dict[str, str]]:
    ses = obtener(usuario_id)
    if ses is None:
        return []
    return list(ses.messages[-_MAX_MENSAJES_HISTORIAL:])


def registrar_intercambio(
    usuario_id: str,
    *,
    intent: str,
    partial: dict[str, Any],
    transcripcion_usuario: str,
    respuesta_asistente: str | None = None,
) -> None:
    """Persiste turno user (+ assistant opcional) para el próximo request HTTP."""
    uid = str(usuario_id)
    with _LOCK:
        _limpiar_vencidas()
        prev = _SESIONES.get(uid)
        turnos = list(prev.turnos) if prev else []
        messages = list(prev.messages) if prev else []
        t = (transcripcion_usuario or "").strip()
        if t and (not turnos or turnos[-1] != t):
            turnos.append(t)
        turnos = turnos[-_MAX_TURNOS:]
        messages = _append_mensaje(messages, "user", t)
        if respuesta_asistente:
            messages = _append_mensaje(messages, "assistant", respuesta_asistente)
        _SESIONES[uid] = _SesionVoz(
            intent=intent,
            partial=dict(partial),
            turnos=turnos,
            messages=messages,
            updated_at=_ahora(),
        )


def actualizar_parcial_sesion(
    usuario_id: str,
    intent: str,
    partial: dict[str, Any],
    transcripcion: str | None = None,
) -> None:
    """Actualiza intent/datos parciales sin duplicar mensajes del chat (eso va en ai.py)."""
    uid = str(usuario_id)
    with _LOCK:
        _limpiar_vencidas()
        prev = _SESIONES.get(uid)
        turnos = list(prev.turnos) if prev else []
        messages = list(prev.messages) if prev else []
        if transcripcion:
            t = transcripcion.strip()
            if t and (not turnos or turnos[-1] != t):
                turnos.append(t)
            turnos = turnos[-_MAX_TURNOS:]
        _SESIONES[uid] = _SesionVoz(
            intent=intent,
            partial=dict(partial),
            turnos=turnos,
            messages=messages,
            updated_at=_ahora(),
        )


def guardar(
    usuario_id: str,
    intent: str,
    partial: dict[str, Any],
    transcripcion: str,
    respuesta_asistente: str | None = None,
) -> None:
    registrar_intercambio(
        usuario_id,
        intent=intent,
        partial=partial,
        transcripcion_usuario=transcripcion,
        respuesta_asistente=respuesta_asistente,
    )


def fusionar_args(base: dict[str, Any], nuevos: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for clave, valor in nuevos.items():
        if valor is None:
            continue
        if isinstance(valor, str) and not valor.strip():
            continue
        if isinstance(valor, list) and not valor:
            continue
        out[clave] = valor
    return out


def inferir_intent_desde_texto(texto: str) -> str | None:
    t = (texto or "").lower()
    if "registrar" in t and "cliente" in t:
        return "registrar_cliente"
    if "nuevo cliente" in t or "cliente nuevo" in t:
        return "registrar_cliente"
    if any(x in t for x in ("pedido", "vender", "venta", "compró", "compro")):
        return "crear_pedido"
    if any(x in t for x in ("cobro", "cobrar", "abono", "pago de")):
        return "registrar_cobro"
    return None


def _parece_telefono(texto: str) -> bool:
    digitos = re.sub(r"\D", "", texto or "")
    return len(digitos) >= 8


# Alucinaciones frecuentes de Whisper con silencio, ruido o manos cerca del micrófono.
_PALABRAS_NO_NOMBRE = frozenset(
    {
        "aplauso",
        "aplausos",
        "aplause",
        "gracias",
        "hola",
        "adios",
        "adiós",
        "chao",
        "sí",
        "si",
        "no",
        "ok",
        "okay",
        "vale",
        "listo",
        "bueno",
        "eh",
        "ah",
        "um",
        "mmm",
        "music",
        "música",
        "musica",
        "risa",
        "risas",
        "subtitulos",
        "subtítulos",
        "subtitles",
        "thanks",
        "thank",
        "you",
    }
)


def _normalizar_token_nombre(texto: str) -> str:
    s = (texto or "").strip().casefold()
    descompuesto = unicodedata.normalize("NFKD", s)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _es_nombre_cliente_valido(nombre: str) -> bool:
    t = (nombre or "").strip()
    if not t or _parece_telefono(t) or len(t) > 80:
        return False
    palabras = t.split()
    if not palabras or len(palabras) > 6:
        return False
    baja = t.lower()
    if any(
        x in baja
        for x in (
            "registrar",
            "cliente",
            "teléfono",
            "telefono",
            "dirección",
            "direccion",
            "pedido",
            "cobro",
        )
    ):
        return False
    tokens = [_normalizar_token_nombre(p) for p in palabras if p.strip()]
    return all(len(tok) >= 2 and tok not in _PALABRAS_NO_NOMBRE for tok in tokens)


def _parece_nombre_propio(texto: str) -> bool:
    return _es_nombre_cliente_valido(texto)


def _es_ruido_transcripcion(texto: str) -> bool:
    t = (texto or "").strip()
    if not t:
        return True
    if _parece_telefono(t):
        return False
    palabras = t.split()
    if len(palabras) == 1:
        tok = _normalizar_token_nombre(palabras[0])
        return tok in _PALABRAS_NO_NOMBRE
    return False


def _transcripcion_parece_eco_asistente(texto: str) -> bool:
    """Micrófono capturando la propia respuesta TTS del asistente."""
    baja = (texto or "").lower()
    if not baja:
        return False
    marcadores = (
        "anotado",
        "cuál es el teléfono",
        "cual es el telefono",
        "teléfono del cliente",
        "telefono del cliente",
        "nombre del cliente",
        "mantén pulsado",
        "manten pulsado",
    )
    return sum(1 for m in marcadores if m in baja) >= 2 or (
        "anotado" in baja and ("teléfono" in baja or "telefono" in baja)
    )


def transcripcion_debe_rechazarse(texto: str) -> bool:
    """Ruido/eco sin intención clara de negocio."""
    if _transcripcion_parece_eco_asistente(texto):
        return True
    if not _es_ruido_transcripcion(texto):
        return False
    baja = (texto or "").lower()
    if "registrar" in baja and "cliente" in baja:
        return False
    if inferir_intent_desde_texto(texto) in ("crear_pedido", "registrar_cobro"):
        return False
    return True


def _sanitizar_args_llm(args: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(args or {})
    nombre = str(out.get("nombre") or "").strip()
    if nombre and not _es_nombre_cliente_valido(nombre):
        out.pop("nombre", None)
    return out


def intent_memoria_pendiente(herramienta: str | None, transcripcion: str) -> str:
    h = (herramienta or "").strip()
    if h in ("crear_pedido", "registrar_cliente", "registrar_cobro"):
        return h
    inf = inferir_intent_desde_texto(transcripcion)
    return inf or "general"


def parcial_memoria(intent: str, args: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(args or {})
    if intent == "registrar_cliente":
        return _depurar_nombre_registrar_cliente(_sanitizar_args_llm(base))
    if intent == "crear_pedido":
        return _sanitizar_args_pedido(base)
    if intent == "registrar_cobro":
        return _sanitizar_args_cobro(base)
    return base


def _debe_abandonar_registro_cliente(transcripcion: str, herramienta: str | None) -> bool:
    if herramienta in ("crear_pedido", "registrar_cobro"):
        return True
    otro = inferir_intent_desde_texto(transcripcion)
    if otro in ("crear_pedido", "registrar_cobro"):
        return True
    baja = (transcripcion or "").lower()
    if any(
        x in baja
        for x in (
            "cancelar",
            "cancela",
            "olvida",
            "olvidar",
            "no quiero",
            "dejalo",
            "déjalo",
            "otra cosa",
            "nuevo pedido",
        )
    ):
        return True
    return False


def _depurar_nombre_registrar_cliente(merged: dict[str, Any]) -> dict[str, Any]:
    out = dict(merged)
    nombre = str(out.get("nombre") or "").strip()
    if nombre and not _es_nombre_cliente_valido(nombre):
        out.pop("nombre", None)
    return out


def enriquecer_args_desde_turno(
    intent: str,
    transcripcion: str,
    args: dict[str, Any],
    partial_previo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Completa campos obvios cuando el usuario responde en un solo dato por audio."""
    out = fusionar_args(partial_previo or {}, args)
    texto = (transcripcion or "").strip()
    if intent == "registrar_cliente":
        m_tel = re.search(
            r"(?:tel[eé]fono|celular|móvil|movil)\s*[:\s]*([+\d\s\-()]{8,})",
            texto,
            re.I,
        )
        if m_tel and not out.get("telefono"):
            out["telefono"] = re.sub(r"\D", "", m_tel.group(1))
        if not out.get("telefono") and _parece_telefono(texto):
            digitos = re.sub(r"\D", "", texto)
            out["telefono"] = digitos[-11:] if len(digitos) > 11 else digitos
        esperando_solo_telefono = bool(str(out.get("nombre") or "").strip()) and not str(
            out.get("telefono") or ""
        ).strip()
        if not out.get("nombre") and _es_nombre_cliente_valido(texto):
            out["nombre"] = texto.strip()
        elif esperando_solo_telefono and _es_ruido_transcripcion(texto):
            pass
        m_nom = re.search(
            r"(?:registrar\s+)?cliente\s+(?:llamado\s+)?"
            r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})"
            r"(?=\s+(?:tel[eé]fono|celular|m[oó]vil|direcci[oó]n)\b|\s*$)",
            texto,
            re.I,
        )
        if m_nom and not out.get("nombre"):
            candidato = m_nom.group(1).strip().strip(",")
            if _es_nombre_cliente_valido(candidato):
                out["nombre"] = candidato
        if not out.get("nombre") and not _transcripcion_parece_eco_asistente(texto):
            m_nom2 = re.search(
                r"(?:nombre|cliente)\s+(?:es\s+)?"
                r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})"
                r"(?=\s+(?:tel[eé]fono|celular|direcci[oó]n)\b|\s*$)",
                texto,
                re.I,
            )
            if m_nom2:
                candidato = m_nom2.group(1).strip().strip(",")
                if _es_nombre_cliente_valido(candidato):
                    out["nombre"] = candidato
        m_dir = re.search(
            r"(?:direcci[oó]n|vive en|ubicado en)\s+(?:es\s+)?(.{5,120})",
            texto,
            re.I,
        )
        if m_dir and not out.get("direccion"):
            out["direccion"] = m_dir.group(1).strip().strip(",")
    return out


def campos_faltantes_registrar_cliente(args: dict[str, Any]) -> list[str]:
    faltan: list[str] = []
    if not str(args.get("nombre") or "").strip():
        faltan.append("nombre")
    if not str(args.get("telefono") or "").strip():
        faltan.append("telefono")
    return faltan


def mensaje_pendiente_registrar_cliente(
    args: dict[str, Any],
    *,
    telefono_no_entendido: bool = False,
) -> str:
    nombre = str(args.get("nombre") or "").strip()
    if not nombre:
        return "¿Cuál es el nombre del cliente?"
    if not str(args.get("telefono") or "").strip():
        if telefono_no_entendido:
            return (
                f"Tengo el nombre «{nombre}». "
                "No escuché bien el teléfono: di solo los números, por ejemplo 04141234567."
            )
        return f"Nombre «{nombre}» anotado. ¿Cuál es el teléfono del cliente?"
    return "Listo para registrar. Procesando…"


def texto_contexto_para_llm(usuario_id: str) -> str:
    ses = obtener(usuario_id)
    if ses is None:
        return ""
    bloques = [
        "CONTEXTO DE CONVERSACIÓN (memoria del turno anterior — respétala):",
        f"- Flujo activo: {ses.intent}.",
    ]
    if ses.partial:
        bloques.append(
            f"- Datos ya confirmados por el usuario: {json.dumps(ses.partial, ensure_ascii=False)}."
        )
    if ses.turnos:
        bloques.append(f"- Frases recientes del usuario: {' | '.join(ses.turnos[-4:])}.")
    bloques.append(
        "Combina esos datos con la frase nueva. "
        "No vuelvas a pedir campos que ya están en «Datos ya confirmados». "
        "Si faltan datos, llama la herramienta con lo que tengas o pide solo lo que falta. "
        "Si el usuario dicta nombre, teléfono y dirección en una sola frase, extráelos todos."
    )
    return "\n".join(bloques)


def _continuar_registrar_cliente(
    uid: str,
    ses: _SesionVoz | None,
    args: dict[str, Any],
    transcripcion: str,
) -> tuple[str, dict[str, Any], str | None, bool]:
    if _transcripcion_parece_eco_asistente(transcripcion):
        limpiar(uid)
        return (
            None,
            {},
            "Se grabó la voz del asistente o un ruido. Espera a que termine de hablar y dicta tu orden.",
            False,
        )

    base = ses.partial if ses else {}
    merged = enriquecer_args_desde_turno(
        "registrar_cliente",
        transcripcion,
        fusionar_args(base, _sanitizar_args_llm(args)),
    )
    merged = _depurar_nombre_registrar_cliente(merged)
    faltan = campos_faltantes_registrar_cliente(merged)
    if faltan:
        telefono_ruido = (
            "nombre" not in faltan
            and "telefono" in faltan
            and _es_ruido_transcripcion(transcripcion)
            and not _parece_telefono(transcripcion)
        )
        msg = mensaje_pendiente_registrar_cliente(
            merged,
            telefono_no_entendido=telefono_ruido,
        )
        actualizar_parcial_sesion(uid, "registrar_cliente", merged, transcripcion)
        return "registrar_cliente", merged, msg, False
    limpiar(uid)
    return "registrar_cliente", merged, None, True


def _sanitizar_args_pedido(args: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(args or {})
    cn = str(out.get("cliente_nombre") or out.get("nombre_cliente") or "").strip()
    if cn:
        out["cliente_nombre"] = cn
        out.pop("nombre_cliente", None)
    productos = out.get("productos")
    if isinstance(productos, list):
        limpios = []
        for item in productos:
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "").strip()
            if not nombre:
                continue
            cant = int(item.get("cantidad") or 1)
            limpios.append({"nombre": nombre, "cantidad": max(1, cant)})
        if limpios:
            out["productos"] = limpios
    return out


def _extraer_productos_desde_texto(texto: str) -> list[dict[str, Any]]:
    t = (texto or "").strip()
    if not t:
        return []
    found: list[dict[str, Any]] = []
    for m in re.finditer(
        r"(\d+)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})",
        t,
        re.I,
    ):
        found.append({"nombre": m.group(2).strip(), "cantidad": int(m.group(1))})
    return found


def enriquecer_pedido_desde_turno(
    transcripcion: str,
    args: dict[str, Any],
    partial_previo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = fusionar_args(partial_previo or {}, _sanitizar_args_pedido(args))
    texto = (transcripcion or "").strip()
    if not out.get("cliente_nombre"):
        m_cli = re.search(
            r"(?:\bpara\s+|\bcliente\s+|\ba\s+)"
            r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})"
            r"(?=\s|$|,|\.)",
            texto,
            re.I,
        )
        if m_cli:
            out["cliente_nombre"] = m_cli.group(1).strip().strip(",")
    extra_prod = _extraer_productos_desde_texto(texto)
    if extra_prod:
        base = list(out.get("productos") or [])
        out["productos"] = base + extra_prod
    if not out.get("metodo_pago"):
        baja = texto.lower()
        for met in ("efectivo", "transferencia", "pago_movil", "pago móvil"):
            if met.replace("_", " ") in baja or met in baja:
                out["metodo_pago"] = met.replace(" ", "_")
                break
    return out


def campos_faltantes_crear_pedido(args: dict[str, Any]) -> list[str]:
    faltan: list[str] = []
    if not str(args.get("cliente_nombre") or "").strip():
        faltan.append("cliente_nombre")
    productos = args.get("productos") or []
    if not isinstance(productos, list) or not productos:
        faltan.append("productos")
    return faltan


def mensaje_pendiente_crear_pedido(args: dict[str, Any]) -> str:
    faltan = campos_faltantes_crear_pedido(args)
    if "cliente_nombre" in faltan:
        return "¿A qué cliente le vendes? Di el nombre."
    if "productos" in faltan:
        cliente = str(args.get("cliente_nombre") or "").strip()
        pref = f"Para «{cliente}», " if cliente else ""
        return f"{pref}¿qué productos y cantidades? Por ejemplo: 3 camisas."
    return "Listo para registrar la venta. Procesando…"


def _continuar_crear_pedido(
    uid: str,
    ses: _SesionVoz | None,
    args: dict[str, Any],
    transcripcion: str,
) -> tuple[str, dict[str, Any], str | None, bool]:
    base = ses.partial if ses else {}
    merged = enriquecer_pedido_desde_turno(transcripcion, args, base)
    faltan = campos_faltantes_crear_pedido(merged)
    if faltan:
        msg = mensaje_pendiente_crear_pedido(merged)
        actualizar_parcial_sesion(uid, "crear_pedido", merged, transcripcion)
        return "crear_pedido", merged, msg, False
    limpiar(uid)
    return "crear_pedido", merged, None, True


def _sanitizar_args_cobro(args: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(args or {})
    cn = str(out.get("cliente_nombre") or out.get("nombre_cliente") or "").strip()
    if cn:
        out["cliente_nombre"] = cn
    if out.get("monto_usd") is None and out.get("monto") is not None:
        out["monto_usd"] = out.pop("monto")
    return out


def enriquecer_cobro_desde_turno(
    transcripcion: str,
    args: dict[str, Any],
    partial_previo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = fusionar_args(partial_previo or {}, _sanitizar_args_cobro(args))
    texto = (transcripcion or "").strip()
    if not out.get("cliente_nombre"):
        m_cli = re.search(
            r"(?:de|a|cliente)\s+"
            r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})",
            texto,
            re.I,
        )
        if m_cli:
            out["cliente_nombre"] = m_cli.group(1).strip()
    if out.get("monto_usd") is None:
        m_monto = re.search(
            r"(\d+(?:[.,]\d{1,2})?)\s*(?:d[oó]lares|usd|\$)?",
            texto,
            re.I,
        )
        if m_monto:
            out["monto_usd"] = float(m_monto.group(1).replace(",", "."))
    if not out.get("metodo_pago"):
        baja = texto.lower()
        for met in ("efectivo", "transferencia", "pago_movil", "pago móvil", "dolar"):
            if met.replace("_", " ") in baja or met in baja:
                out["metodo_pago"] = "pago_movil" if "movil" in met or "móvil" in met else met
                break
    return out


def campos_faltantes_registrar_cobro(args: dict[str, Any]) -> list[str]:
    faltan: list[str] = []
    if not str(args.get("cliente_nombre") or "").strip():
        faltan.append("cliente_nombre")
    if args.get("monto_usd") is None:
        faltan.append("monto_usd")
    if not str(args.get("metodo_pago") or "").strip():
        faltan.append("metodo_pago")
    return faltan


def mensaje_pendiente_registrar_cobro(args: dict[str, Any]) -> str:
    faltan = campos_faltantes_registrar_cobro(args)
    if "cliente_nombre" in faltan:
        return "¿De qué cliente es el cobro? Di el nombre."
    if "monto_usd" in faltan:
        cliente = str(args.get("cliente_nombre") or "").strip()
        return f"¿Cuántos dólares cobró{' a ' + cliente if cliente else ''}?"
    if "metodo_pago" in faltan:
        return "¿Fue en efectivo, transferencia o pago móvil?"
    return "Listo para registrar el cobro. Procesando…"


def _debe_abandonar_flujo_cobro(transcripcion: str, herramienta: str | None) -> bool:
    if herramienta in ("crear_pedido", "registrar_cliente"):
        return True
    otro = inferir_intent_desde_texto(transcripcion)
    if otro in ("crear_pedido", "registrar_cliente"):
        return True
    baja = (transcripcion or "").lower()
    return any(x in baja for x in ("cancelar", "cancela", "olvida", "otra cosa"))


def _debe_abandonar_flujo_pedido(transcripcion: str, herramienta: str | None) -> bool:
    if herramienta in ("registrar_cobro", "registrar_cliente"):
        return True
    otro = inferir_intent_desde_texto(transcripcion)
    if otro in ("registrar_cobro", "registrar_cliente"):
        return True
    baja = (transcripcion or "").lower()
    return any(x in baja for x in ("cancelar", "cancela", "olvida", "otra cosa"))


def _continuar_registrar_cobro(
    uid: str,
    ses: _SesionVoz | None,
    args: dict[str, Any],
    transcripcion: str,
) -> tuple[str, dict[str, Any], str | None, bool]:
    base = ses.partial if ses else {}
    merged = enriquecer_cobro_desde_turno(transcripcion, args, base)
    faltan = campos_faltantes_registrar_cobro(merged)
    if faltan:
        msg = mensaje_pendiente_registrar_cobro(merged)
        actualizar_parcial_sesion(uid, "registrar_cobro", merged, transcripcion)
        return "registrar_cobro", merged, msg, False
    limpiar(uid)
    return "registrar_cobro", merged, None, True


def preparar_ejecucion(
    usuario_id: str,
    herramienta: str | None,
    args: dict[str, Any],
    transcripcion: str,
    mensaje_libre: str | None,
) -> tuple[str | None, dict[str, Any], str | None, bool]:
    """
    Fusiona sesión + turno actual.
    Devuelve (herramienta, args, mensaje_usuario, listo_para_ejecutar).
    """
    uid = str(usuario_id)
    ses = obtener(uid)

    if ses and ses.intent == "registrar_cliente":
        if _debe_abandonar_registro_cliente(transcripcion, herramienta):
            limpiar(uid)
        else:
            return _continuar_registrar_cliente(uid, ses, args, transcripcion)

    if ses and ses.intent == "crear_pedido":
        if _debe_abandonar_flujo_pedido(transcripcion, herramienta):
            limpiar(uid)
        else:
            return _continuar_crear_pedido(uid, ses, args, transcripcion)

    if ses and ses.intent == "registrar_cobro":
        if _debe_abandonar_flujo_cobro(transcripcion, herramienta):
            limpiar(uid)
        else:
            return _continuar_registrar_cobro(uid, ses, args, transcripcion)

    intent = herramienta or inferir_intent_desde_texto(transcripcion)

    if intent == "registrar_cliente" or herramienta == "registrar_cliente":
        if not ses and transcripcion_debe_rechazarse(transcripcion):
            limpiar(uid)
            return (
                None,
                {},
                "No entendí el audio. Mantén pulsado el micrófono y di tu pedido, cobro o «registrar cliente …».",
                False,
            )
        return _continuar_registrar_cliente(uid, ses, args, transcripcion)

    if intent == "crear_pedido" or herramienta == "crear_pedido":
        return _continuar_crear_pedido(uid, ses, args, transcripcion)

    if intent == "registrar_cobro" or herramienta == "registrar_cobro":
        return _continuar_registrar_cobro(uid, ses, args, transcripcion)

    if herramienta:
        limpiar(uid)
        return herramienta, args, mensaje_libre, True

    if intent and inferir_intent_desde_texto(transcripcion):
        if intent == "registrar_cliente":
            return _continuar_registrar_cliente(uid, ses, args, transcripcion)
        if intent == "crear_pedido":
            return _continuar_crear_pedido(uid, ses, args, transcripcion)
        if intent == "registrar_cobro":
            return _continuar_registrar_cobro(uid, ses, args, transcripcion)
        actualizar_parcial_sesion(uid, intent, {}, transcripcion)
        return None, {}, mensaje_libre, False

    return herramienta, args, mensaje_libre, bool(herramienta)
