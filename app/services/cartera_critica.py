"""Cartera crítica: créditos o facturas con más de 21 días de atraso.

El umbral es estricto: 21 días exactos siguen en el panel normal.
Entran aquí solo los saldos cuya cuota impaga (o la factura, si no
tiene plan de cuotas) venció hace más de tres semanas.

No altera ventas, cobros, rutas ni el buró. Solo lee cartera y escribe
el historial de notas de seguimiento.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.core import (
    Cliente,
    CuotaAmortizacion,
    EstadoCuota,
    EstadoVenta,
    NotaSeguimientoCobranza,
    Usuario,
    Venta,
)

# Más de 21 días. Tres semanas cumplidas no alcanzan; hace falta el día 22.
DIAS_ATRASO_CRITICO = 21

MOTIVOS_NO_PAGO: dict[str, str] = {
    "desempleado_temporal": "Desempleado temporal",
    "problema_familiar": "Problema familiar",
    "negativa_pago": "Negativa de pago / Moroso real",
    "alquiler_pendiente": "Alquiler pendiente",
    "otro": "Otro",
}

ESTADOS_CONSIDERACION: dict[str, str] = {
    "en_observacion": "En observación",
    "acuerdo_pago": "Acuerdo de pago",
    "cobro_juridico": "Cobro jurídico/estricto",
}

# Alias que acepta el query param motivo_mora. El valor canónico es la clave.
GRUPOS_MOTIVO: list[tuple[str, str]] = [
    ("todos", "Todos"),
    ("desempleo", "Desempleo"),
    ("alquiler", "Alquiler"),
    ("moroso_real", "Moroso real"),
    ("problema_familiar", "Familiar"),
    ("otro", "Otro"),
    ("sin_motivo", "Sin motivo"),
]

_MOTIVO_A_GRUPO = {
    "desempleado_temporal": "desempleo",
    "alquiler_pendiente": "alquiler",
    "negativa_pago": "moroso_real",
    "problema_familiar": "problema_familiar",
    "otro": "otro",
}

_ALIAS_FILTRO = {
    "todos": "todos",
    "desempleo": "desempleo",
    "desempleado": "desempleo",
    "desempleado_temporal": "desempleo",
    "alquiler": "alquiler",
    "alquiler_pendiente": "alquiler",
    "moroso_real": "moroso_real",
    "moroso": "moroso_real",
    "negativa_pago": "moroso_real",
    "problema_familiar": "problema_familiar",
    "familiar": "problema_familiar",
    "otro": "otro",
    "sin_motivo": "sin_motivo",
}

_ESTADOS_ABIERTOS = (EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL)
_CUOTAS_ABIERTAS = (EstadoCuota.PENDIENTE, EstadoCuota.PARCIAL)


def dias_de_atraso(fecha: datetime, hoy: Optional[date] = None) -> int:
    """Días corridos desde el vencimiento. Negativo si todavía no vence."""
    referencia = hoy or datetime.utcnow().date()
    momento = fecha.date() if isinstance(fecha, datetime) else fecha
    return (referencia - momento).days


def es_atraso_critico(dias: int, umbral: int = DIAS_ATRASO_CRITICO) -> bool:
    return dias > umbral


def etiqueta_motivo(codigo: Optional[str]) -> Optional[str]:
    if not codigo:
        return None
    return MOTIVOS_NO_PAGO.get(codigo, codigo)


def etiqueta_estado(codigo: Optional[str]) -> Optional[str]:
    if not codigo:
        return None
    return ESTADOS_CONSIDERACION.get(codigo, codigo)


def grupo_de_motivo(codigo: Optional[str]) -> str:
    if not codigo:
        return "sin_motivo"
    return _MOTIVO_A_GRUPO.get(codigo, "otro")


def normalizar_motivo_mora(valor: Optional[str]) -> str:
    """Acepta desempleo, alquiler, moroso_real, todos y los códigos internos."""
    if valor is None or str(valor).strip() == "":
        return "todos"
    clave = str(valor).strip().lower()
    canonico = _ALIAS_FILTRO.get(clave)
    if canonico is None:
        raise ValueError(
            "Filtro de motivo no reconocido. Usa desempleo, alquiler, moroso_real o todos."
        )
    return canonico


def conteos_por_motivo(clientes: list[dict]) -> list[dict]:
    totales = {codigo: 0 for codigo, _ in GRUPOS_MOTIVO}
    totales["todos"] = len(clientes)
    for cliente in clientes:
        grupo = cliente.get("grupo_motivo") or "sin_motivo"
        if grupo not in totales:
            grupo = "otro"
        if grupo != "todos":
            totales[grupo] += 1
    return [
        {"codigo": codigo, "etiqueta": etiqueta, "total": totales[codigo]}
        for codigo, etiqueta in GRUPOS_MOTIVO
    ]


def catalogo() -> dict:
    return {
        "dias_atraso_minimo": DIAS_ATRASO_CRITICO,
        "motivos": [
            {"codigo": codigo, "etiqueta": etiqueta}
            for codigo, etiqueta in MOTIVOS_NO_PAGO.items()
        ],
        "estados": [
            {"codigo": codigo, "etiqueta": etiqueta}
            for codigo, etiqueta in ESTADOS_CONSIDERACION.items()
        ],
    }


def _saldo_venta(venta: Venta) -> Decimal:
    cobrado = sum((Decimal(str(c.monto_usd)) for c in venta.cobros), Decimal("0"))
    return Decimal(str(venta.total_usd)) - cobrado


def _atraso_de_venta(
    venta: Venta,
    cuotas: list[CuotaAmortizacion],
    hoy: date,
) -> Optional[tuple[int, datetime]]:
    """Devuelve (días, fecha de referencia) solo si el atraso supera el umbral."""
    if cuotas:
        abiertas = [c for c in cuotas if c.estado in _CUOTAS_ABIERTAS]
        if not abiertas:
            return None
        vencidas = [c for c in abiertas if dias_de_atraso(c.fecha_vencimiento, hoy) > 0]
        if not vencidas:
            return None
        peor = max(vencidas, key=lambda c: dias_de_atraso(c.fecha_vencimiento, hoy))
        dias = dias_de_atraso(peor.fecha_vencimiento, hoy)
        if not es_atraso_critico(dias):
            return None
        return dias, peor.fecha_vencimiento

    # Factura pendiente sin plan de cuotas: el atraso corre desde la venta.
    if not venta.fecha:
        return None
    dias = dias_de_atraso(venta.fecha, hoy)
    if not es_atraso_critico(dias):
        return None
    return dias, venta.fecha


def _notas_vigentes(
    db: Session,
    empresa_id: uuid.UUID,
    cliente_ids: list[uuid.UUID],
) -> dict[uuid.UUID, NotaSeguimientoCobranza]:
    if not cliente_ids:
        return {}
    notas = (
        db.query(NotaSeguimientoCobranza)
        .filter(
            NotaSeguimientoCobranza.empresa_id == empresa_id,
            NotaSeguimientoCobranza.cliente_id.in_(cliente_ids),
        )
        .order_by(
            NotaSeguimientoCobranza.fecha.desc(),
            NotaSeguimientoCobranza.fecha_creacion.desc(),
        )
        .all()
    )
    vigentes: dict[uuid.UUID, NotaSeguimientoCobranza] = {}
    for nota in notas:
        vigentes.setdefault(nota.cliente_id, nota)
    return vigentes


def listar_clientes_criticos(
    db: Session,
    empresa_id: uuid.UUID,
    hoy: Optional[date] = None,
    motivo_mora: Optional[str] = None,
) -> dict:
    """Agrupa por cliente los créditos con atraso > 21 días.

    motivo_mora filtra el arreglo `clientes`. Los conteos siempre salen
    de la carpeta completa, para que los chips no pierdan el total.
    """
    filtro = normalizar_motivo_mora(motivo_mora)
    referencia = hoy or datetime.utcnow().date()
    ventas = (
        db.query(Venta)
        .options(joinedload(Venta.cliente), joinedload(Venta.cobros))
        .filter(
            Venta.empresa_id == empresa_id,
            Venta.estado.in_(_ESTADOS_ABIERTOS),
        )
        .all()
    )
    # joinedload de cobros puede repetir la venta en el resultado.
    ventas = list({venta.id: venta for venta in ventas}.values())
    if not ventas:
        return _respuesta_vacia(filtro)

    venta_ids = [v.id for v in ventas]
    cuotas = (
        db.query(CuotaAmortizacion)
        .filter(CuotaAmortizacion.venta_id.in_(venta_ids))
        .all()
    )
    cuotas_por_venta: dict[uuid.UUID, list[CuotaAmortizacion]] = defaultdict(list)
    for cuota in cuotas:
        cuotas_por_venta[cuota.venta_id].append(cuota)

    por_cliente: dict[uuid.UUID, dict] = {}
    saldos_abiertos: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0"))
    for venta in ventas:
        saldo = _saldo_venta(venta)
        if saldo <= 0:
            continue
        cliente = venta.cliente
        if cliente is None or cliente.empresa_id != empresa_id:
            continue
        saldos_abiertos[cliente.id] += saldo
        atraso = _atraso_de_venta(venta, cuotas_por_venta.get(venta.id, []), referencia)
        if atraso is None:
            continue
        dias, fecha_ref = atraso

        ficha = por_cliente.get(cliente.id)
        if ficha is None:
            ficha = {
                "cliente_id": cliente.id,
                "cliente_nombre": cliente.nombre,
                "cliente_telefono": cliente.telefono,
                "cliente_direccion": cliente.direccion,
                "dias_atraso": dias,
                "saldo_pendiente_usd": Decimal("0"),
                "creditos": [],
            }
            por_cliente[cliente.id] = ficha

        ficha["saldo_pendiente_usd"] += saldo
        ficha["dias_atraso"] = max(ficha["dias_atraso"], dias)
        freq = venta.frecuencia_pago.value if venta.frecuencia_pago else "contado"
        ficha["creditos"].append(
            {
                "venta_id": venta.id,
                "saldo_pendiente_usd": float(saldo),
                "dias_atraso": dias,
                "fecha_referencia": fecha_ref,
                "frecuencia_pago": freq,
            }
        )

    vigentes = _notas_vigentes(db, empresa_id, list(por_cliente.keys()))
    resultado = []
    for ficha in por_cliente.values():
        nota = vigentes.get(ficha["cliente_id"])
        ficha["saldo_pendiente_usd"] = float(ficha["saldo_pendiente_usd"])
        ficha["creditos"].sort(key=lambda c: c["dias_atraso"], reverse=True)
        ficha["motivo"] = nota.motivo if nota else None
        ficha["motivo_etiqueta"] = etiqueta_motivo(nota.motivo) if nota else None
        ficha["grupo_motivo"] = grupo_de_motivo(nota.motivo if nota else None)
        ficha["estado_consideracion"] = nota.estado_consideracion if nota else None
        ficha["estado_etiqueta"] = etiqueta_estado(nota.estado_consideracion) if nota else None
        ficha["ultima_observacion"] = nota.observacion if nota else None
        ficha["ultima_nota_fecha"] = nota.fecha if nota else None
        resultado.append(ficha)

    from app.services.acuerdos_pago import aplicar_gracia

    aplicar_gracia(db, empresa_id, resultado, saldos_abiertos, referencia)
    resultado.sort(
        key=lambda item: (
            0 if item.get("alerta_estricta", True) else 1,
            -item["dias_atraso"],
            -item["saldo_pendiente_usd"],
        )
    )
    conteos = conteos_por_motivo(resultado)
    if filtro != "todos":
        resultado = [item for item in resultado if item.get("grupo_motivo") == filtro]
    return {
        "motivo_mora": filtro,
        "conteos": conteos,
        "clientes": resultado,
    }


def _respuesta_vacia(filtro: str) -> dict:
    return {
        "motivo_mora": filtro,
        "conteos": conteos_por_motivo([]),
        "clientes": [],
    }


def cliente_de_empresa(
    db: Session,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> Optional[Cliente]:
    return (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id, Cliente.empresa_id == empresa_id)
        .first()
    )


def listar_notas(
    db: Session,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> list[dict]:
    filas = (
        db.query(NotaSeguimientoCobranza, Usuario.nombre)
        .join(Usuario, Usuario.id == NotaSeguimientoCobranza.usuario_id)
        .filter(
            NotaSeguimientoCobranza.empresa_id == empresa_id,
            NotaSeguimientoCobranza.cliente_id == cliente_id,
        )
        .order_by(
            NotaSeguimientoCobranza.fecha.desc(),
            NotaSeguimientoCobranza.fecha_creacion.desc(),
        )
        .all()
    )
    return [_serializar_nota(nota, nombre) for nota, nombre in filas]


def crear_nota(
    db: Session,
    *,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    usuario_id: uuid.UUID,
    usuario_nombre: str,
    motivo: str,
    estado_consideracion: str,
    observacion: str,
    commit: bool = True,
) -> dict:
    if motivo not in MOTIVOS_NO_PAGO:
        raise ValueError("Motivo de no pago no reconocido")
    if estado_consideracion not in ESTADOS_CONSIDERACION:
        raise ValueError("Estado de consideración no reconocido")
    texto = observacion.strip()
    if len(texto) < 3:
        raise ValueError("La observación debe explicar el caso del cliente")

    ahora = datetime.utcnow()
    nota = NotaSeguimientoCobranza(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        fecha=ahora,
        motivo=motivo,
        estado_consideracion=estado_consideracion,
        observacion=texto,
        fecha_creacion=ahora,
    )
    db.add(nota)
    if commit:
        db.commit()
        db.refresh(nota)
    return _serializar_nota(nota, usuario_nombre)


def _serializar_nota(nota: NotaSeguimientoCobranza, usuario_nombre: str) -> dict:
    return {
        "id": nota.id,
        "empresa_id": nota.empresa_id,
        "cliente_id": nota.cliente_id,
        "usuario_id": nota.usuario_id,
        "usuario_nombre": usuario_nombre,
        "fecha": nota.fecha,
        "motivo": nota.motivo,
        "motivo_etiqueta": etiqueta_motivo(nota.motivo),
        "estado_consideracion": nota.estado_consideracion,
        "estado_etiqueta": etiqueta_estado(nota.estado_consideracion),
        "observacion": nota.observacion,
        "fecha_creacion": nota.fecha_creacion,
    }
