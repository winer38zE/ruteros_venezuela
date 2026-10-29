"""Campos obligatorios de voz, tomados de los formularios de la app.

Cliente (`cliente_form_screen.dart` → `_guardar`): nombre, identificación de al
menos 5 caracteres y teléfono. La voz pide además apellido, WhatsApp con código
de país y dirección, de uno en uno. La cédula se pide si el formulario la exige
o si el país es Venezuela o Colombia.

Venta (`nueva_venta_screen.dart`): cliente y al menos un producto.
Cobro (`nuevo_cobro_screen.dart`): cliente, monto y método de pago.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# El formulario de cliente no deja guardar sin identificación (mín. 5).
FORMULARIO_EXIGE_CEDULA = True
_PAISES_CON_CEDULA = frozenset({"VE", "VEN", "CO", "COL"})


@dataclass(frozen=True)
class CampoFormulario:
    clave: str
    pregunta: str


_CLIENTE: tuple[CampoFormulario, ...] = (
    CampoFormulario("nombre", "¿Cuál es el nombre del cliente?"),
    CampoFormulario("apellido", "¿Cuál es el apellido?"),
    CampoFormulario("telefono", "¿Cuál es el teléfono?"),
    CampoFormulario(
        "whatsapp",
        "¿Cuál es el WhatsApp con código de país? Por ejemplo, más cincuenta y ocho.",
    ),
    CampoFormulario("direccion", "¿Cuál es la dirección?"),
    CampoFormulario("identificacion", "¿Cuál es la cédula?"),
)

_VENTA: tuple[CampoFormulario, ...] = (
    CampoFormulario("cliente_nombre", "¿A qué cliente le vendes? Di el nombre."),
    CampoFormulario("productos", "¿Qué productos y cantidades? Por ejemplo: 3 camisas."),
)

_COBRO: tuple[CampoFormulario, ...] = (
    CampoFormulario("cliente_nombre", "¿De qué cliente es el cobro? Di el nombre."),
    CampoFormulario("monto_usd", "¿Cuántos dólares cobraste?"),
    CampoFormulario("metodo_pago", "¿Fue en efectivo, transferencia o pago móvil?"),
)

_POR_HERRAMIENTA = {
    "registrar_cliente": _CLIENTE,
    "crear_pedido": _VENTA,
    "registrar_cobro": _COBRO,
}


def campos_formulario(herramienta: str) -> tuple[CampoFormulario, ...]:
    return _POR_HERRAMIENTA.get(herramienta, ())


def claves_obligatorias(herramienta: str) -> tuple[str, ...]:
    return tuple(c.clave for c in campos_formulario(herramienta))


def cedula_exigida(codigo_iso: str | None = None) -> bool:
    if FORMULARIO_EXIGE_CEDULA:
        return True
    codigo = (codigo_iso or "").strip().upper()
    return codigo in _PAISES_CON_CEDULA


def whatsapp_con_codigo_pais(valor: str | None) -> bool:
    texto = (valor or "").strip()
    digitos = re.sub(r"\D", "", texto)
    if texto.startswith("+") and len(digitos) >= 10:
        return True
    return len(digitos) >= 11 and (digitos.startswith("58") or digitos.startswith("57"))


def tiene_nombre_y_apellido(args: dict) -> bool:
    apellido = str(args.get("apellido") or "").strip()
    nombre = str(args.get("nombre") or "").strip()
    if nombre and apellido:
        return True
    return len(nombre.split()) >= 2


def faltantes_cliente(args: dict, *, codigo_iso: str | None = None) -> list[str]:
    """Solo claves vacías, en el orden del formulario. No rellena nada."""
    faltan: list[str] = []
    if not str(args.get("nombre") or "").strip():
        faltan.append("nombre")
    elif not tiene_nombre_y_apellido(args):
        faltan.append("apellido")
    if not str(args.get("telefono") or "").strip():
        faltan.append("telefono")
    if not whatsapp_con_codigo_pais(str(args.get("whatsapp") or "")):
        faltan.append("whatsapp")
    if not str(args.get("direccion") or "").strip():
        faltan.append("direccion")
    ident = str(args.get("identificacion") or "").strip()
    if cedula_exigida(codigo_iso) and len(ident) < 5:
        faltan.append("identificacion")
    return faltan


def pregunta_del_campo(herramienta: str, clave: str) -> str:
    for campo in campos_formulario(herramienta):
        if campo.clave == clave:
            return campo.pregunta
    return "Necesito un dato más."
