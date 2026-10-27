"""Memoria de conversación del asistente de voz (por usuario, en proceso)."""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any

_TTL_SEGUNDOS = 900
_MAX_TURNOS = 8

_LOCK = threading.Lock()
_SESIONES: dict[str, "_SesionVoz"] = {}


@dataclass
class _SesionVoz:
    intent: str
    partial: dict[str, Any] = field(default_factory=dict)
    turnos: list[str] = field(default_factory=list)
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


def guardar(
    usuario_id: str,
    intent: str,
    partial: dict[str, Any],
    transcripcion: str,
) -> None:
    uid = str(usuario_id)
    with _LOCK:
        _limpiar_vencidas()
        prev = _SESIONES.get(uid)
        turnos = list(prev.turnos) if prev else []
        t = (transcripcion or "").strip()
        if t and (not turnos or turnos[-1] != t):
            turnos.append(t)
        turnos = turnos[-_MAX_TURNOS:]
        _SESIONES[uid] = _SesionVoz(
            intent=intent,
            partial=dict(partial),
            turnos=turnos,
            updated_at=_ahora(),
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


def _parece_nombre_propio(texto: str) -> bool:
    t = (texto or "").strip()
    if not t or _parece_telefono(t):
        return False
    if len(t) > 80:
        return False
    palabras = t.split()
    if len(palabras) > 6:
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
    return True


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
        if not out.get("telefono") and _parece_telefono(texto):
            digitos = re.sub(r"\D", "", texto)
            out["telefono"] = digitos[-11:] if len(digitos) > 11 else digitos
        if not out.get("nombre") and _parece_nombre_propio(texto):
            out["nombre"] = texto.strip()
        # "Registrar cliente Edwuar, teléfono 0414..."
        m_tel = re.search(
            r"(?:tel[eé]fono|celular|móvil|movil)\s*[:\s]*([+\d\s\-()]{8,})",
            texto,
            re.I,
        )
        if m_tel and not out.get("telefono"):
            out["telefono"] = re.sub(r"\D", "", m_tel.group(1))
        m_nom = re.search(
            r"(?:registrar\s+)?cliente\s+(?:llamado\s+)?"
            r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})"
            r"(?=\s+(?:tel[eé]fono|celular|m[oó]vil|direcci[oó]n)\b|\s*$)",
            texto,
            re.I,
        )
        if m_nom and not out.get("nombre"):
            candidato = m_nom.group(1).strip().strip(",")
            if _parece_nombre_propio(candidato):
                out["nombre"] = candidato
        if not out.get("nombre"):
            m_nom2 = re.search(
                r"(?:nombre|cliente)\s+(?:es\s+)?"
                r"([A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ][\w'.-]*){0,3})"
                r"(?=\s+(?:tel[eé]fono|celular|direcci[oó]n)\b|\s*$)",
                texto,
                re.I,
            )
            if m_nom2:
                candidato = m_nom2.group(1).strip().strip(",")
                if _parece_nombre_propio(candidato):
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


def mensaje_pendiente_registrar_cliente(args: dict[str, Any]) -> str:
    nombre = str(args.get("nombre") or "").strip()
    if not nombre:
        return "¿Cuál es el nombre del cliente?"
    if not str(args.get("telefono") or "").strip():
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
    intent = herramienta or (ses.intent if ses else None) or inferir_intent_desde_texto(transcripcion)

    if intent == "registrar_cliente":
        base = ses.partial if ses else {}
        merged = enriquecer_args_desde_turno(
            "registrar_cliente",
            transcripcion,
            fusionar_args(base, args),
            partial_previo=None,
        )
        faltan = campos_faltantes_registrar_cliente(merged)
        if faltan:
            guardar(uid, "registrar_cliente", merged, transcripcion)
            return "registrar_cliente", merged, mensaje_pendiente_registrar_cliente(merged), False
        limpiar(uid)
        return "registrar_cliente", merged, None, True

    if herramienta:
        limpiar(uid)
        return herramienta, args, mensaje_libre, True

    if intent and inferir_intent_desde_texto(transcripcion):
        guardar(uid, intent, {}, transcripcion)
        if intent == "registrar_cliente":
            return None, {}, "¿Cuál es el nombre del cliente?", False

    if ses and not herramienta:
        guardar(uid, ses.intent, ses.partial, transcripcion)
        if ses.intent == "registrar_cliente":
            merged = enriquecer_args_desde_turno(
                "registrar_cliente", transcripcion, dict(ses.partial)
            )
            faltan = campos_faltantes_registrar_cliente(merged)
            guardar(uid, "registrar_cliente", merged, transcripcion)
            if faltan:
                return None, merged, mensaje_pendiente_registrar_cliente(merged), False

    return herramienta, args, mensaje_libre, bool(herramienta)
