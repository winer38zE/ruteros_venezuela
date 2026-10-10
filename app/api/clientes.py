from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Cliente, TipoCliente, DiaVisita, TipoVisitaRuta
from app.schemas.core import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    BuroCreditoResponse,
    ClienteAutocompletadoResponse,
    HistorialBuroItem,
)
from app.services.buro_credito import (
    actualizar_historial_comportamiento,
    clasificacion_por_score,
    clasificar_score,
    consultar_buro,
    datos_autocompletado_buro,
    normalizar_identificacion,
    sincronizar_score_inicial,
)
from app.services.rutas import (
    asignar_dia_orden,
    dia_actual,
    dia_ruta_de_cliente,
    etiqueta_dia,
    orden_ruta_de_cliente,
    resolver_dia,
    siguiente_orden_secuencial,
)
from app.core.deps import obtener_usuario_opcional
from app.models.core import Usuario
from typing import List, Optional

router = APIRouter()


def _serializar_cliente(c: Cliente) -> ClienteResponse:
    score = c.score_credito or 70
    en_mora = (c.estado_morosidad or "") == "moroso"
    nivel = "malo" if en_mora or score <= 35 else clasificar_score(score)
    clasif = c.clasificacion_credito or clasificacion_por_score(score, en_mora)
    return ClienteResponse(
        id=c.id,
        empresa_id=c.empresa_id,
        nombre=c.nombre,
        identificacion=c.identificacion,
        telefono=c.telefono,
        telefono_secundario=c.telefono_secundario,
        direccion=c.direccion,
        punto_referencia=c.punto_referencia,
        latitud_residencia=float(c.latitud_residencia) if c.latitud_residencia is not None else None,
        longitud_residencia=float(c.longitud_residencia) if c.longitud_residencia is not None else None,
        empresa_trabajo=c.empresa_trabajo,
        direccion_laboral=c.direccion_laboral,
        latitud_trabajo=float(c.latitud_trabajo) if c.latitud_trabajo is not None else None,
        longitud_trabajo=float(c.longitud_trabajo) if c.longitud_trabajo is not None else None,
        ref_familiar_nombre=c.ref_familiar_nombre,
        ref_familiar_parentesco=c.ref_familiar_parentesco,
        ref_familiar_telefono=c.ref_familiar_telefono,
        email=c.email,
        score_credito=score,
        nivel_riesgo=nivel,
        estado_credito=clasif,
        clasificacion_credito=clasif,
        total_compras=int(c.total_compras or 0),
        monto_compras_usd=float(c.monto_compras_usd or 0),
        total_pagos=int(c.total_pagos or 0),
        monto_pagos_usd=float(c.monto_pagos_usd or 0),
        estado_morosidad=c.estado_morosidad or "al_dia",
        tipo_cliente=c.tipo_cliente.value if hasattr(c.tipo_cliente, "value") else (c.tipo_cliente or "detal"),
        vendedor_id=c.vendedor_id,
        dia_visita=c.dia_visita.value if hasattr(c.dia_visita, "value") else c.dia_visita,
        orden_secuencial=orden_ruta_de_cliente(c),
        dia_ruta=dia_ruta_de_cliente(c),
        orden_ruta=orden_ruta_de_cliente(c),
        tipo_visita_ruta=(
            c.tipo_visita_ruta.value
            if hasattr(c.tipo_visita_ruta, "value")
            else (c.tipo_visita_ruta or "frecuente")
        ),
    )


@router.post("/", response_model=ClienteResponse)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(obtener_usuario_opcional),
):
    empresa_actual = obtener_empresa_tenant(db)
    ident = normalizar_identificacion(cliente.identificacion)

    existente = db.query(Cliente).filter(Cliente.identificacion == ident).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Esta identificación ya está registrada en la red Ruteros. Use buró para verificar.",
        )

    vendedor_id = cliente.vendedor_id
    if vendedor_id is None and usuario is not None:
        vendedor_id = usuario.id

    try:
        dia_visita = resolver_dia(cliente.dia_ruta, cliente.dia_visita)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if dia_visita is None and vendedor_id is not None:
        dia_visita = dia_actual()

    orden = cliente.orden_ruta if cliente.orden_ruta is not None else cliente.orden_secuencial
    if orden is None and vendedor_id is not None and dia_visita is not None:
        orden = siguiente_orden_secuencial(db, vendedor_id, dia_visita, empresa_actual.id)

    nuevo_cliente = Cliente(
        nombre=cliente.nombre_completo,
        identificacion=ident,
        telefono=cliente.telefono,
        telefono_secundario=cliente.telefono_secundario,
        direccion=cliente.direccion,
        punto_referencia=cliente.punto_referencia,
        latitud_residencia=cliente.latitud_residencia,
        longitud_residencia=cliente.longitud_residencia,
        empresa_trabajo=cliente.empresa_trabajo,
        direccion_laboral=cliente.direccion_laboral,
        latitud_trabajo=cliente.latitud_trabajo,
        longitud_trabajo=cliente.longitud_trabajo,
        ref_familiar_nombre=cliente.ref_familiar_nombre,
        ref_familiar_parentesco=cliente.ref_familiar_parentesco,
        ref_familiar_telefono=cliente.ref_familiar_telefono,
        email=cliente.email,
        tipo_cliente=TipoCliente(cliente.tipo_cliente or "detal"),
        vendedor_id=vendedor_id,
        tipo_visita_ruta=TipoVisitaRuta.NUEVO if vendedor_id else TipoVisitaRuta.FRECUENTE,
        empresa_id=empresa_actual.id,
    )
    asignar_dia_orden(nuevo_cliente, dia_visita, orden)
    sincronizar_score_inicial(db, nuevo_cliente)
    actualizar_historial_comportamiento(db, nuevo_cliente)

    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return _serializar_cliente(nuevo_cliente)


@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Buscar por nombre, teléfono o cédula"),
):
    empresa = obtener_empresa_tenant(db)
    query = db.query(Cliente).filter(Cliente.empresa_id == empresa.id)
    if q:
        term = f"%{q.strip()}%"
        ident = normalizar_identificacion(q) if q.strip() else ""
        filtros = [
            Cliente.nombre.ilike(term),
            Cliente.telefono.ilike(term),
            Cliente.telefono_secundario.ilike(term),
        ]
        if ident:
            filtros.append(Cliente.identificacion.ilike(f"%{ident}%"))
        query = query.filter(or_(*filtros))
    clientes = query.order_by(Cliente.nombre.asc()).all()
    return [_serializar_cliente(c) for c in clientes]


@router.get("/buro/{identificacion}", response_model=BuroCreditoResponse)
def consultar_buro_credito(identificacion: str, db: Session = Depends(get_db)):
    data = consultar_buro(db, identificacion)
    return BuroCreditoResponse(
        identificacion=data["identificacion"],
        encontrado=data["encontrado"],
        score_global=data["score_global"],
        nivel_riesgo=data["nivel_riesgo"],
        estado_credito=data["estado_credito"],
        historial_cumplimiento=[
            HistorialBuroItem(**h) for h in data["historial_cumplimiento"]
        ],
    )


@router.get("/verificar/{identificacion}", response_model=ClienteAutocompletadoResponse)
def verificar_identificacion(identificacion: str, db: Session = Depends(get_db)):
    data = datos_autocompletado_buro(db, identificacion)
    if not data:
        return ClienteAutocompletadoResponse(
            identificacion=normalizar_identificacion(identificacion),
            en_red=False,
        )
    return ClienteAutocompletadoResponse(**data)


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: UUID, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id, Cliente.empresa_id == empresa.id)
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    actualizar_historial_comportamiento(db, cliente)
    db.commit()
    db.refresh(cliente)
    return _serializar_cliente(cliente)


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: UUID,
    body: ClienteUpdate,
    db: Session = Depends(get_db),
):
    empresa = obtener_empresa_tenant(db)
    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id, Cliente.empresa_id == empresa.id)
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if body.identificacion is not None:
        ident = normalizar_identificacion(body.identificacion)
        dup = (
            db.query(Cliente)
            .filter(Cliente.identificacion == ident, Cliente.id != cliente.id)
            .first()
        )
        if dup:
            raise HTTPException(status_code=400, detail="La identificación ya está en uso en la red")
        cliente.identificacion = ident

    if body.nombre_completo is not None:
        cliente.nombre = body.nombre_completo
    if body.telefono is not None:
        cliente.telefono = body.telefono
    if body.telefono_secundario is not None:
        cliente.telefono_secundario = body.telefono_secundario
    if body.direccion is not None:
        cliente.direccion = body.direccion
    if body.punto_referencia is not None:
        cliente.punto_referencia = body.punto_referencia
    if body.empresa_trabajo is not None:
        cliente.empresa_trabajo = body.empresa_trabajo
    if body.direccion_laboral is not None:
        cliente.direccion_laboral = body.direccion_laboral
    if body.latitud_residencia is not None:
        cliente.latitud_residencia = body.latitud_residencia
    if body.longitud_residencia is not None:
        cliente.longitud_residencia = body.longitud_residencia
    if body.latitud_trabajo is not None:
        cliente.latitud_trabajo = body.latitud_trabajo
    if body.longitud_trabajo is not None:
        cliente.longitud_trabajo = body.longitud_trabajo
    if body.ref_familiar_nombre is not None:
        cliente.ref_familiar_nombre = body.ref_familiar_nombre
    if body.ref_familiar_parentesco is not None:
        cliente.ref_familiar_parentesco = body.ref_familiar_parentesco
    if body.ref_familiar_telefono is not None:
        cliente.ref_familiar_telefono = body.ref_familiar_telefono
    if body.email is not None:
        cliente.email = body.email
    if body.tipo_cliente is not None:
        cliente.tipo_cliente = TipoCliente(body.tipo_cliente)
    if body.vendedor_id is not None:
        cliente.vendedor_id = body.vendedor_id
    dia_en_body = body.dia_ruta is not None or body.dia_visita is not None
    orden_en_body = body.orden_ruta is not None or body.orden_secuencial is not None
    if dia_en_body or orden_en_body:
        try:
            nuevo_dia = resolver_dia(body.dia_ruta, body.dia_visita) if dia_en_body else cliente.dia_visita
            if dia_en_body and nuevo_dia is not None and not isinstance(nuevo_dia, DiaVisita):
                nuevo_dia = resolver_dia(None, str(nuevo_dia))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        etiqueta_nueva = etiqueta_dia(nuevo_dia) if isinstance(nuevo_dia, DiaVisita) else None
        dia_cambio = dia_en_body and (
            cliente.dia_visita != nuevo_dia or cliente.dia_ruta != etiqueta_nueva
        )
        if orden_en_body:
            orden = body.orden_ruta if body.orden_ruta is not None else body.orden_secuencial
        elif dia_cambio and isinstance(nuevo_dia, DiaVisita) and cliente.vendedor_id is not None:
            orden = siguiente_orden_secuencial(db, cliente.vendedor_id, nuevo_dia, empresa.id)
        else:
            orden = orden_ruta_de_cliente(cliente)
        asignar_dia_orden(cliente, nuevo_dia if isinstance(nuevo_dia, DiaVisita) else None, orden)
    if body.tipo_visita_ruta is not None:
        cliente.tipo_visita_ruta = TipoVisitaRuta(body.tipo_visita_ruta)

    actualizar_historial_comportamiento(db, cliente)
    db.commit()
    db.refresh(cliente)
    return _serializar_cliente(cliente)
