"""Lógica de rutas diarias por vendedor/cobrador."""
from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.core import Cliente, DiaVisita, TipoVisitaRuta

DIAS_SEMANA = [
    DiaVisita.LUNES,
    DiaVisita.MARTES,
    DiaVisita.MIERCOLES,
    DiaVisita.JUEVES,
    DiaVisita.VIERNES,
    DiaVisita.SABADO,
    DiaVisita.DOMINGO,
]

MAPA_DIA = {d.value: d for d in DiaVisita}


def dia_actual() -> DiaVisita:
    return DIAS_SEMANA[datetime.now().weekday()]


def normalizar_dia(dia: str) -> DiaVisita:
    clave = dia.strip().upper()
    if clave not in MAPA_DIA:
        raise ValueError(f"Día inválido: {dia}. Use LUNES..DOMINGO")
    return MAPA_DIA[clave]


def siguiente_orden_secuencial(
    db: Session,
    vendedor_id: UUID,
    dia: DiaVisita,
    empresa_id: UUID,
) -> int:
    max_orden = (
        db.query(func.max(Cliente.orden_secuencial))
        .filter(
            Cliente.empresa_id == empresa_id,
            Cliente.vendedor_id == vendedor_id,
            Cliente.dia_visita == dia,
        )
        .scalar()
    )
    return (max_orden or 0) + 1


def asignar_cliente_a_ruta(
    db: Session,
    cliente: Cliente,
    vendedor_id: UUID,
    dia: Optional[DiaVisita] = None,
    es_nuevo: bool = True,
) -> None:
    """Integra un cliente en la secuencia del día (al final si es nuevo)."""
    dia_obj = dia or dia_actual()
    cliente.vendedor_id = vendedor_id
    cliente.dia_visita = dia_obj
    cliente.tipo_visita_ruta = TipoVisitaRuta.NUEVO if es_nuevo else TipoVisitaRuta.FRECUENTE

    if cliente.orden_secuencial is None:
        cliente.orden_secuencial = siguiente_orden_secuencial(
            db, vendedor_id, dia_obj, cliente.empresa_id
        )


def obtener_ruta_dia(
    db: Session,
    vendedor_id: UUID,
    dia: DiaVisita,
    empresa_id: UUID,
) -> list[Cliente]:
    return (
        db.query(Cliente)
        .filter(
            Cliente.empresa_id == empresa_id,
            Cliente.vendedor_id == vendedor_id,
            Cliente.dia_visita == dia,
            Cliente.orden_secuencial.isnot(None),
        )
        .order_by(Cliente.orden_secuencial.asc())
        .all()
    )


def serializar_cliente_ruta(cliente: Cliente) -> dict:
    lat = cliente.latitud_residencia
    lng = cliente.longitud_residencia
    if lat is None and lng is None:
        lat = cliente.latitud_trabajo
        lng = cliente.longitud_trabajo

    tipo = cliente.tipo_visita_ruta
    if hasattr(tipo, "value"):
        tipo = tipo.value

    dia = cliente.dia_visita
    if hasattr(dia, "value"):
        dia = dia.value

    return {
        "id": cliente.id,
        "vendedor_id": cliente.vendedor_id,
        "nombre": cliente.nombre,
        "direccion": cliente.direccion,
        "dia_visita": dia,
        "orden_secuencial": cliente.orden_secuencial or 0,
        "latitud": float(lat) if lat is not None else None,
        "longitud": float(lng) if lng is not None else None,
        "tipo_visita_ruta": tipo or "frecuente",
        "telefono": cliente.telefono,
    }
