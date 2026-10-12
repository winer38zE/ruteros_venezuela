"""Lógica de rutas diarias por vendedor/cobrador."""
import unicodedata
from datetime import datetime, date
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models.core import (
    Cliente,
    Usuario,
    VisitaDiaria,
    DiaVisita,
    TipoVisitaRuta,
    EstadoVisita,
    RolUsuario,
)

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

ETIQUETA_DIA = {
    DiaVisita.LUNES: "Lunes",
    DiaVisita.MARTES: "Martes",
    DiaVisita.MIERCOLES: "Miércoles",
    DiaVisita.JUEVES: "Jueves",
    DiaVisita.VIERNES: "Viernes",
    DiaVisita.SABADO: "Sábado",
    DiaVisita.DOMINGO: "Domingo",
}


def dia_actual() -> DiaVisita:
    return DIAS_SEMANA[datetime.now().weekday()]


def fecha_actual() -> date:
    return date.today()


def _clave_dia(dia: str) -> str:
    texto = unicodedata.normalize("NFD", dia.strip())
    sin_acentos = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return sin_acentos.upper()


def normalizar_dia(dia: str) -> DiaVisita:
    clave = _clave_dia(dia)
    if clave not in MAPA_DIA:
        raise ValueError(f"Día inválido: {dia}. Use Lunes..Domingo")
    return MAPA_DIA[clave]


def etiqueta_dia(dia: DiaVisita) -> str:
    return ETIQUETA_DIA[dia]


def resolver_dia(dia_ruta: Optional[str], dia_visita: Optional[str] = None) -> Optional[DiaVisita]:
    raw = (dia_ruta or "").strip() or (dia_visita or "").strip()
    if not raw:
        return None
    return normalizar_dia(raw)


def asignar_dia_orden(cliente: Cliente, dia: Optional[DiaVisita], orden: Optional[int]) -> None:
    """Escribe el día y la parada en los campos de ruta y en los alias históricos."""
    cliente.dia_visita = dia
    cliente.dia_ruta = etiqueta_dia(dia) if dia is not None else None
    cliente.orden_secuencial = orden
    cliente.orden_ruta = orden


def dia_ruta_de_cliente(cliente: Cliente) -> Optional[str]:
    if cliente.dia_ruta:
        return cliente.dia_ruta
    dia = cliente.dia_visita
    if dia is None:
        return None
    if not isinstance(dia, DiaVisita):
        try:
            dia = normalizar_dia(str(dia))
        except ValueError:
            return str(cliente.dia_visita)
    return etiqueta_dia(dia)


def orden_ruta_de_cliente(cliente: Cliente) -> Optional[int]:
    if cliente.orden_ruta is not None:
        return int(cliente.orden_ruta)
    if cliente.orden_secuencial is not None:
        return int(cliente.orden_secuencial)
    return None


def _filtro_mismo_dia(dia: DiaVisita):
    etiqueta = etiqueta_dia(dia)
    return or_(
        Cliente.dia_ruta == etiqueta,
        and_(
            or_(Cliente.dia_ruta.is_(None), Cliente.dia_ruta == ""),
            Cliente.dia_visita == dia,
        ),
    )


def puede_gestionar_ruta(usuario: Usuario, vendedor_id: UUID) -> bool:
    if usuario.rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        return True
    if usuario.rol in (RolUsuario.VENDEDOR, RolUsuario.COBRADOR):
        return usuario.id == vendedor_id
    return False


def siguiente_orden_secuencial(
    db: Session,
    vendedor_id: UUID,
    dia: DiaVisita,
    empresa_id: UUID,
) -> int:
    max_orden = (
        db.query(func.max(func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial)))
        .filter(
            Cliente.empresa_id == empresa_id,
            Cliente.vendedor_id == vendedor_id,
            _filtro_mismo_dia(dia),
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
    dia_obj = dia or dia_actual()
    cliente.vendedor_id = vendedor_id
    cliente.tipo_visita_ruta = TipoVisitaRuta.NUEVO if es_nuevo else TipoVisitaRuta.FRECUENTE

    orden = orden_ruta_de_cliente(cliente)
    if orden is None:
        orden = siguiente_orden_secuencial(db, vendedor_id, dia_obj, cliente.empresa_id)
    asignar_dia_orden(cliente, dia_obj, orden)


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
            _filtro_mismo_dia(dia),
            or_(Cliente.orden_ruta.isnot(None), Cliente.orden_secuencial.isnot(None)),
        )
        .order_by(
            func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial).asc(),
            Cliente.nombre.asc(),
        )
        .all()
    )


def mapa_visitas_dia(
    db: Session,
    vendedor_id: UUID,
    fecha: date,
    cliente_ids: list[UUID],
    empresa_id: UUID,
) -> dict[UUID, VisitaDiaria]:
    if not cliente_ids:
        return {}
    visitas = (
        db.query(VisitaDiaria)
        .filter(
            VisitaDiaria.empresa_id == empresa_id,
            VisitaDiaria.vendedor_id == vendedor_id,
            VisitaDiaria.fecha == fecha,
            VisitaDiaria.cliente_id.in_(cliente_ids),
        )
        .all()
    )
    return {v.cliente_id: v for v in visitas}


def serializar_cliente_ruta(
    cliente: Cliente,
    visita: Optional[VisitaDiaria] = None,
) -> dict:
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
    dia_legible = dia_ruta_de_cliente(cliente)
    if not dia and dia_legible:
        dia = normalizar_dia(dia_legible).value
    if not dia_legible and dia:
        dia_legible = etiqueta_dia(normalizar_dia(str(dia)))
    orden = orden_ruta_de_cliente(cliente) or 0

    estado = EstadoVisita.PENDIENTE.value
    marcado_en = None
    if visita:
        estado = visita.estado.value if hasattr(visita.estado, "value") else visita.estado
        marcado_en = visita.marcado_en

    return {
        "id": cliente.id,
        "vendedor_id": cliente.vendedor_id,
        "nombre": cliente.nombre,
        "direccion": cliente.direccion,
        "dia_visita": dia,
        "dia_ruta": dia_legible,
        "orden_secuencial": orden,
        "orden_ruta": orden,
        "latitud": float(lat) if lat is not None else None,
        "longitud": float(lng) if lng is not None else None,
        "tipo_visita_ruta": tipo or "frecuente",
        "telefono": cliente.telefono,
        "estado_visita": estado,
        "marcado_en": marcado_en,
    }


def construir_ruta_dia_response(
    db: Session,
    vendedor_id: UUID,
    dia: DiaVisita,
    empresa_id: UUID,
    fecha: Optional[date] = None,
) -> dict:
    fecha_obj = fecha or fecha_actual()
    clientes = obtener_ruta_dia(db, vendedor_id, dia, empresa_id)
    ids = [c.id for c in clientes]
    visitas = mapa_visitas_dia(db, vendedor_id, fecha_obj, ids, empresa_id)

    items = [
        serializar_cliente_ruta(c, visitas.get(c.id))
        for c in clientes
    ]
    visitados = sum(1 for i in items if i["estado_visita"] == EstadoVisita.VISITADO.value)
    no_enc = sum(1 for i in items if i["estado_visita"] == EstadoVisita.NO_ENCONTRADO.value)
    pendientes = len(items) - visitados - no_enc

    return {
        "vendedor_id": vendedor_id,
        "dia": dia.value,
        "fecha": fecha_obj,
        "total_clientes": len(items),
        "visitados": visitados,
        "pendientes": pendientes,
        "clientes": items,
    }


def reordenar_ruta_dia(
    db: Session,
    vendedor_id: UUID,
    dia: DiaVisita,
    orden_items: list[dict],
    empresa_id: UUID,
) -> dict:
    clientes_ruta = obtener_ruta_dia(db, vendedor_id, dia, empresa_id)
    ids_ruta = {c.id for c in clientes_ruta}
    ids_payload = {item["cliente_id"] for item in orden_items}

    if ids_ruta != ids_payload:
        raise ValueError("El orden debe incluir exactamente los clientes de la ruta del día")

    ordenes = sorted(
        item.get("orden_ruta", item.get("orden_secuencial")) for item in orden_items
    )
    esperado = list(range(1, len(ordenes) + 1))
    if ordenes != esperado:
        raise ValueError("Los órdenes deben ser consecutivos desde 1 hasta N sin duplicados")

    etiqueta = etiqueta_dia(dia)
    mapa = {c.id: c for c in clientes_ruta}
    for item in orden_items:
        orden = item.get("orden_ruta", item.get("orden_secuencial"))
        cliente = mapa[item["cliente_id"]]
        cliente.dia_visita = dia
        cliente.dia_ruta = etiqueta
        cliente.orden_secuencial = orden
        cliente.orden_ruta = orden

    db.commit()
    return construir_ruta_dia_response(db, vendedor_id, dia, empresa_id)


def registrar_visita(
    db: Session,
    cliente_id: UUID,
    vendedor_id: UUID,
    empresa_id: UUID,
    estado: str,
    fecha: Optional[date] = None,
    notas: Optional[str] = None,
    latitud_visita: Optional[float] = None,
    longitud_visita: Optional[float] = None,
) -> VisitaDiaria:
    fecha_obj = fecha or fecha_actual()
    estado_enum = EstadoVisita(estado)

    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id, Cliente.empresa_id == empresa_id)
        .first()
    )
    if not cliente:
        raise ValueError("Cliente no encontrado")

    existente = (
        db.query(VisitaDiaria)
        .filter(
            VisitaDiaria.cliente_id == cliente_id,
            VisitaDiaria.vendedor_id == vendedor_id,
            VisitaDiaria.fecha == fecha_obj,
        )
        .first()
    )

    if existente:
        existente.estado = estado_enum
        existente.notas = notas
        existente.latitud_visita = latitud_visita
        existente.longitud_visita = longitud_visita
        existente.marcado_en = datetime.utcnow()
        db.commit()
        db.refresh(existente)
        return existente

    visita = VisitaDiaria(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        fecha=fecha_obj,
        estado=estado_enum,
        notas=notas,
        latitud_visita=latitud_visita,
        longitud_visita=longitud_visita,
    )
    db.add(visita)
    db.commit()
    db.refresh(visita)
    return visita


def registrar_visitas_lote(
    db: Session,
    visitas_data: list[dict],
    vendedor_id: UUID,
    empresa_id: UUID,
) -> list[VisitaDiaria]:
    resultados = []
    for item in visitas_data:
        visita = registrar_visita(
            db=db,
            cliente_id=item["cliente_id"],
            vendedor_id=vendedor_id,
            empresa_id=empresa_id,
            estado=item.get("estado", "visitado"),
            fecha=item.get("fecha"),
            notas=item.get("notas"),
            latitud_visita=item.get("latitud_visita"),
            longitud_visita=item.get("longitud_visita"),
        )
        resultados.append(visita)
    return resultados


def serializar_visita(v: VisitaDiaria) -> dict:
    estado = v.estado.value if hasattr(v.estado, "value") else v.estado
    return {
        "id": v.id,
        "cliente_id": v.cliente_id,
        "vendedor_id": v.vendedor_id,
        "fecha": v.fecha,
        "estado": estado,
        "notas": v.notas,
        "latitud_visita": float(v.latitud_visita) if v.latitud_visita is not None else None,
        "longitud_visita": float(v.longitud_visita) if v.longitud_visita is not None else None,
        "marcado_en": v.marcado_en,
    }


def resumen_rutas_dia(
    db: Session,
    empresa_id: UUID,
    fecha: Optional[date] = None,
    dia: Optional[DiaVisita] = None,
) -> dict:
    fecha_obj = fecha or fecha_actual()
    dia_obj = dia or dia_actual()

    vendedores = (
        db.query(Usuario)
        .filter(
            Usuario.empresa_id == empresa_id,
            Usuario.activo.is_(True),
            Usuario.rol.in_([RolUsuario.VENDEDOR, RolUsuario.COBRADOR]),
        )
        .all()
    )

    resumen = []
    for vendedor in vendedores:
        clientes = obtener_ruta_dia(db, vendedor.id, dia_obj, empresa_id)
        if not clientes:
            continue
        ids = [c.id for c in clientes]
        visitas = mapa_visitas_dia(db, vendedor.id, fecha_obj, ids, empresa_id)
        visitados = sum(
            1 for vid in visitas.values()
            if (vid.estado.value if hasattr(vid.estado, "value") else vid.estado) == EstadoVisita.VISITADO.value
        )
        no_enc = sum(
            1 for vid in visitas.values()
            if (vid.estado.value if hasattr(vid.estado, "value") else vid.estado) == EstadoVisita.NO_ENCONTRADO.value
        )
        total = len(clientes)
        pendientes = total - visitados - no_enc
        pct = round((visitados / total) * 100, 1) if total else 0.0

        resumen.append({
            "vendedor_id": vendedor.id,
            "vendedor_nombre": vendedor.nombre,
            "total_clientes": total,
            "visitados": visitados,
            "pendientes": pendientes,
            "no_encontrados": no_enc,
            "porcentaje_avance": pct,
        })

    return {
        "fecha": fecha_obj,
        "dia": dia_obj.value,
        "vendedores": resumen,
    }
