from datetime import date
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_ruta_o_superior, require_admin_o_dueno
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Usuario, RolUsuario
from app.schemas.core import (
    RutaClienteResponse,
    RutasDiaResponse,
    ReordenarRutaRequest,
    VisitaCreate,
    VisitaLoteRequest,
    VisitaResponse,
    RutasResumenResponse,
    ResumenVendedorRuta,
    WhatsappReporteRequest,
    WhatsappReporteResponse,
)
from app.services.rutas import (
    dia_actual,
    normalizar_dia,
    puede_gestionar_ruta,
    construir_ruta_dia_response,
    reordenar_ruta_dia,
    registrar_visita,
    registrar_visitas_lote,
    serializar_visita,
    resumen_rutas_dia,
)
from app.services.evolution_service import enviar_texto, formatear_resumen_rutas, normalizar_telefono

router = APIRouter()


def _resolver_vendedor_id(
    vendedor_id: Optional[UUID],
    usuario: Usuario,
) -> UUID:
    if vendedor_id is not None:
        return vendedor_id
    if usuario.rol in (RolUsuario.VENDEDOR, RolUsuario.COBRADOR):
        return usuario.id
    raise HTTPException(
        status_code=400,
        detail="Debe indicar vendedor_id o iniciar sesión como vendedor/cobrador",
    )


def _verificar_acceso_ruta(usuario: Usuario, vendedor_id: UUID) -> None:
    if not puede_gestionar_ruta(usuario, vendedor_id):
        raise HTTPException(status_code=403, detail="No puede gestionar la ruta de otro vendedor")


@router.get("/dia", response_model=RutasDiaResponse)
def listar_ruta_del_dia(
    vendedor_id: Optional[UUID] = Query(None, description="ID del vendedor/cobrador"),
    dia: Optional[str] = Query(None, description="Día de visita: LUNES, MARTES, ..."),
    fecha: Optional[date] = Query(None, description="Fecha calendario para estados de visita"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    empresa = obtener_empresa_tenant(db)
    vid = _resolver_vendedor_id(vendedor_id, usuario)
    _verificar_acceso_ruta(usuario, vid)

    try:
        dia_obj = normalizar_dia(dia) if dia else dia_actual()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    data = construir_ruta_dia_response(db, vid, dia_obj, empresa.id, fecha)
    return RutasDiaResponse(
        vendedor_id=data["vendedor_id"],
        dia=data["dia"],
        fecha=data["fecha"],
        total_clientes=data["total_clientes"],
        visitados=data["visitados"],
        pendientes=data["pendientes"],
        clientes=[RutaClienteResponse(**c) for c in data["clientes"]],
    )


@router.put("/dia/reordenar", response_model=RutasDiaResponse)
def reordenar_ruta(
    body: ReordenarRutaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    empresa = obtener_empresa_tenant(db)
    vid = _resolver_vendedor_id(body.vendedor_id, usuario)
    _verificar_acceso_ruta(usuario, vid)

    try:
        dia_obj = normalizar_dia(body.dia)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        orden = [
            {
                "cliente_id": i.cliente_id,
                "orden_ruta": i.orden_ruta if i.orden_ruta is not None else i.orden_secuencial,
                "orden_secuencial": i.orden_secuencial,
            }
            for i in body.orden
        ]
        data = reordenar_ruta_dia(db, vid, dia_obj, orden, empresa.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RutasDiaResponse(
        vendedor_id=data["vendedor_id"],
        dia=data["dia"],
        fecha=data["fecha"],
        total_clientes=data["total_clientes"],
        visitados=data["visitados"],
        pendientes=data["pendientes"],
        clientes=[RutaClienteResponse(**c) for c in data["clientes"]],
    )


@router.post("/visitas", response_model=VisitaResponse)
def marcar_visita(
    body: VisitaCreate,
    vendedor_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    empresa = obtener_empresa_tenant(db)
    vid = _resolver_vendedor_id(vendedor_id, usuario)
    _verificar_acceso_ruta(usuario, vid)

    try:
        visita = registrar_visita(
            db=db,
            cliente_id=body.cliente_id,
            vendedor_id=vid,
            empresa_id=empresa.id,
            estado=body.estado,
            fecha=body.fecha,
            notas=body.notas,
            latitud_visita=body.latitud_visita,
            longitud_visita=body.longitud_visita,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return VisitaResponse(**serializar_visita(visita))


@router.post("/visitas/lote", response_model=List[VisitaResponse])
def marcar_visitas_lote(
    body: VisitaLoteRequest,
    vendedor_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    empresa = obtener_empresa_tenant(db)
    vid = _resolver_vendedor_id(vendedor_id, usuario)
    _verificar_acceso_ruta(usuario, vid)

    visitas_data = [v.model_dump() for v in body.visitas]
    try:
        visitas = registrar_visitas_lote(db, visitas_data, vid, empresa.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return [VisitaResponse(**serializar_visita(v)) for v in visitas]


@router.get("/resumen", response_model=RutasResumenResponse)
def resumen_rutas(
    fecha: Optional[date] = Query(None),
    dia: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    empresa = obtener_empresa_tenant(db)

    try:
        dia_obj = normalizar_dia(dia) if dia else dia_actual()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    data = resumen_rutas_dia(db, empresa.id, fecha, dia_obj)
    return RutasResumenResponse(
        fecha=data["fecha"],
        dia=data["dia"],
        vendedores=[ResumenVendedorRuta(**v) for v in data["vendedores"]],
    )


@router.post("/resumen/whatsapp", response_model=WhatsappReporteResponse)
def enviar_resumen_whatsapp(
    body: WhatsappReporteRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    """Envía el resumen del día, o un texto ya armado, por Evolution API."""
    empresa = obtener_empresa_tenant(db)
    telefono = (body.telefono or usuario.telefono or "").strip()
    if not telefono:
        raise HTTPException(
            status_code=400,
            detail="Indique el teléfono del dueño o cliente que recibirá el reporte",
        )

    try:
        destino = normalizar_telefono(telefono)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if body.texto and body.texto.strip():
        texto = body.texto.strip()
    else:
        try:
            dia_obj = normalizar_dia(body.dia) if body.dia else dia_actual()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        data = resumen_rutas_dia(db, empresa.id, body.fecha, dia_obj)
        texto = formatear_resumen_rutas(data)

    ok, mensaje = enviar_texto(destino, texto)
    if not ok:
        status = 503 if "no está configurada" in mensaje else 502
        raise HTTPException(status_code=status, detail=mensaje)

    return WhatsappReporteResponse(enviado=True, telefono=destino, mensaje=mensaje)
