"""Endpoints de tasas de cambio multimoneda."""
import logging
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.deps import require_dueno, require_admin_o_dueno, obtener_usuario_actual
from app.models.core import TasaCambio, Usuario
from app.schemas.core import (
    TasaCambioCreate,
    TasaCambioResponse,
    ConversionMonedaRequest,
    ConversionMonedaResponse,
    TasaSincronizacionResponse,
)
from app.services.tasas_scraper import (
    sincronizar_tasas_automaticas,
    momento_actual,
    tasas_desde_ultima_db,
)
from app.services.tasas_cambio import (
    obtener_ultima_tasa,
    convertir_usd_a_ves,
    convertir_usd_a_cop,
    convertir_cop_a_usd,
    convertir_cop_a_ves,
    tasa_usd_a_ves,
    calcular_precios_equivalentes,
)
from app.models.core import TipoTasaUsd

logger = logging.getLogger(__name__)

router = APIRouter()


def _serializar_tasa(t: TasaCambio) -> TasaCambioResponse:
    usd_bcv = float(t.usd_bcv_bs or t.usd_bs or 0)
    usd_par = float(t.usd_paralelo_bs or usd_bcv)
    usd_bs = float(t.usd_bs or usd_bcv)
    cop = float(t.cop_usd or 0)
    return TasaCambioResponse(
        id=str(t.id),
        empresa_id=str(t.empresa_id),
        fecha=t.fecha or datetime.utcnow(),
        momento=t.momento or "manana",
        usd_bs=usd_bs,
        usd_bcv_bs=usd_bcv,
        usd_paralelo_bs=usd_par,
        eur_bs=float(t.eur_bs or 0),
        cop_usd=cop,
        cop_ves=float(t.cop_ves) if t.cop_ves is not None else None,
        activa=bool(t.activa if t.activa is not None else True),
        origen=t.origen or "manual",
    )


@router.post("/sincronizar-auto", response_model=TasaSincronizacionResponse)
async def sincronizar_tasas_auto(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    """Fuerza la obtención automática de tasas (BCV, paralelo, COP) vía scraper/API."""
    momento = momento_actual()
    empresa_id = usuario.empresa_id

    try:
        creadas, externas, uso_fallback = await sincronizar_tasas_automaticas(
            db,
            momento=momento,
            empresa_id=empresa_id,
        )
    except Exception as exc:
        logger.exception("Sincronización manual de tasas falló por completo")
        externas = tasas_desde_ultima_db(db, empresa_id)
        externas.fuentes["error"] = str(exc)
        creadas = []
        uso_fallback = True

    tasa_empresa = next(
        (t for t in creadas if t.empresa_id == empresa_id),
        None,
    )
    if tasa_empresa is None:
        tasa_empresa = obtener_ultima_tasa(db, empresa_id)

    if uso_fallback and not creadas:
        mensaje = (
            "No se pudieron obtener tasas en vivo; se devolvieron valores de respaldo "
            f"(BCV={externas.usd_bcv_bs:.2f}, Paralelo={externas.usd_paralelo_bs:.2f}, "
            f"COP/USD={externas.cop_usd:.2f})."
        )
        exito = False
    elif uso_fallback:
        mensaje = "Tasas sincronizadas con valores parciales o de respaldo."
        exito = True
    else:
        mensaje = "Tasas sincronizadas y marcadas como activas del día."
        exito = True

    return TasaSincronizacionResponse(
        exito=exito,
        momento=momento,
        empresas_actualizadas=len(creadas),
        usd_bcv_bs=externas.usd_bcv_bs,
        usd_paralelo_bs=externas.usd_paralelo_bs,
        cop_usd=externas.cop_usd,
        fuentes=externas.fuentes,
        mensaje=mensaje,
        tasa=_serializar_tasa(tasa_empresa) if tasa_empresa else None,
    )


@router.post("/", response_model=TasaCambioResponse)
def registrar_tasa(
    tasa: TasaCambioCreate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    empresa_id = dueno.empresa_id
    if tasa.cop_usd <= 0:
        raise HTTPException(status_code=400, detail="COP/USD debe ser mayor que cero")
    cop_ves = float(tasa.usd_bcv_bs) / float(tasa.cop_usd)

    nueva_tasa = TasaCambio(
        empresa_id=empresa_id,
        fecha=datetime.utcnow(),
        momento=tasa.momento,
        usd_bs=tasa.usd_bcv_bs,
        usd_bcv_bs=tasa.usd_bcv_bs,
        usd_paralelo_bs=tasa.usd_paralelo_bs,
        eur_bs=tasa.eur_bs,
        cop_usd=tasa.cop_usd,
        cop_ves=cop_ves,
        activa=True,
        origen="manual",
    )
    db.query(TasaCambio).filter(
        TasaCambio.empresa_id == empresa_id,
        TasaCambio.activa.is_(True),
    ).update({"activa": False})
    db.add(nueva_tasa)
    db.commit()
    db.refresh(nueva_tasa)
    return _serializar_tasa(nueva_tasa)


@router.get("/", response_model=List[TasaCambioResponse])
def listar_tasas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    items = (
        db.query(TasaCambio)
        .filter(TasaCambio.empresa_id == usuario.empresa_id)
        .order_by(TasaCambio.fecha.desc())
        .limit(60)
        .all()
    )
    return [_serializar_tasa(t) for t in items]


@router.get("/ultima", response_model=TasaCambioResponse)
def obtener_ultima(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    ultima = obtener_ultima_tasa(db, usuario.empresa_id)
    if not ultima:
        raise HTTPException(status_code=404, detail="No hay tasas de cambio registradas")
    return _serializar_tasa(ultima)


@router.post("/convertir", response_model=ConversionMonedaResponse)
def convertir_moneda(
    body: ConversionMonedaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    tasa = obtener_ultima_tasa(db, usuario.empresa_id)
    if not tasa:
        raise HTTPException(status_code=404, detail="Registra una tasa de cambio primero")

    tipo = TipoTasaUsd(body.tipo_tasa_usd)
    monto = Decimal(str(body.monto_origen))
    destino = body.moneda_destino

    if body.moneda_origen == "usd" and destino == "ves":
        resultado = convertir_usd_a_ves(monto, tasa, tipo)
    elif body.moneda_origen == "usd" and destino == "cop":
        resultado = convertir_usd_a_cop(monto, tasa)
    elif body.moneda_origen == "cop" and destino == "usd":
        resultado = convertir_cop_a_usd(monto, tasa)
    elif body.moneda_origen == "cop" and destino == "ves":
        resultado = convertir_cop_a_ves(monto, tasa, tipo)
    elif body.moneda_origen == "ves" and destino == "usd":
        tasa_ves = tasa_usd_a_ves(tasa, tipo)
        if tasa_ves == 0:
            raise HTTPException(status_code=400, detail="Tasa USD/VES inválida")
        resultado = (monto / tasa_ves).quantize(Decimal("0.01"))
    elif body.moneda_origen == destino:
        resultado = monto
    else:
        raise HTTPException(status_code=400, detail="Conversión no soportada")

    return ConversionMonedaResponse(
        monto_origen=body.monto,
        moneda_origen=body.moneda_origen,
        monto_destino=float(resultado),
        moneda_destino=destino,
        tipo_tasa_usd=body.tipo_tasa_usd,
        tasas_aplicadas=calcular_precios_equivalentes(Decimal("1"), tasa, tipo),
    )
