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
    normalizar_identificacion,
    clasificar_score,
    etiqueta_estado,
    consultar_buro,
    datos_autocompletado_buro,
    sincronizar_score_inicial,
)
from app.services.rutas import (
    dia_actual,
    normalizar_dia,
    siguiente_orden_secuencial,
)
from app.core.deps import obtener_usuario_opcional
from app.models.core import Usuario
from typing import List, Optional

router = APIRouter()


def _serializar_cliente(c: Cliente) -> ClienteResponse:
    score = c.score_credito or 70
    nivel = clasificar_score(score)
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
        estado_credito=etiqueta_estado(score),
        tipo_cliente=c.tipo_cliente.value if hasattr(c.tipo_cliente, "value") else (c.tipo_cliente or "detal"),
        vendedor_id=c.vendedor_id,
        dia_visita=c.dia_visita.value if hasattr(c.dia_visita, "value") else c.dia_visita,
        orden_secuencial=c.orden_secuencial,
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

    dia_visita = None
    if cliente.dia_visita:
        try:
            dia_visita = normalizar_dia(cliente.dia_visita)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    elif vendedor_id is not None:
        dia_visita = dia_actual()

    orden = cliente.orden_secuencial
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
        dia_visita=dia_visita,
        orden_secuencial=orden,
        tipo_visita_ruta=TipoVisitaRuta.NUEVO if vendedor_id else TipoVisitaRuta.FRECUENTE,
        empresa_id=empresa_actual.id,
    )
    sincronizar_score_inicial(db, nuevo_cliente)

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
    if body.dia_visita is not None:
        try:
            cliente.dia_visita = normalizar_dia(body.dia_visita)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    if body.orden_secuencial is not None:
        cliente.orden_secuencial = body.orden_secuencial
    if body.tipo_visita_ruta is not None:
        cliente.tipo_visita_ruta = TipoVisitaRuta(body.tipo_visita_ruta)

    db.commit()
    db.refresh(cliente)
    return _serializar_cliente(cliente)
