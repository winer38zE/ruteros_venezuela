"""Endpoints de tasas de cambio multimoneda."""
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.deps import require_dueno, require_admin_o_dueno, obtener_usuario_actual
from app.core.tenant import obtener_empresa_tenant
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


@router.post("/sincronizar-auto", response_model=TasaSincronizacionResponse)
async def sincronizar_tasas_auto(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    """Fuerza la obtención automática de tasas (BCV, paralelo, COP) vía scraper/API."""
    momento = momento_actual()
    empresa = obtener_empresa_tenant(db)

    try:
        creadas, externas, uso_fallback = await sincronizar_tasas_automaticas(
            db,
            momento=momento,
            empresa_id=empresa.id,
        )
    except Exception as exc:
        logger.exception("Sincronización manual de tasas falló por completo")
        externas = tasas_desde_ultima_db(db, empresa.id)
        externas.fuentes["error"] = str(exc)
        creadas = []
        uso_fallback = True

    tasa_empresa = next(
        (t for t in creadas if t.empresa_id == usuario.empresa_id),
        creadas[0] if creadas else obtener_ultima_tasa(db, usuario.empresa_id),
    )

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
        tasa=tasa_empresa,
    )


@router.post("/", response_model=TasaCambioResponse)
def registrar_tasa(
    tasa: TasaCambioCreate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    empresa = obtener_empresa_tenant(db)
    cop_ves = float(tasa.usd_bcv_bs) / float(tasa.cop_usd) if tasa.cop_usd else None

    nueva_tasa = TasaCambio(
        empresa_id=empresa.id,
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
        TasaCambio.empresa_id == empresa.id,
        TasaCambio.activa.is_(True),
    ).update({"activa": False})
    db.add(nueva_tasa)
    db.commit()
    db.refresh(nueva_tasa)
    return nueva_tasa


@router.get("/", response_model=List[TasaCambioResponse])
def listar_tasas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(obtener_usuario_actual),
):
    empresa = obtener_empresa_tenant(db)
    return (
        db.query(TasaCambio)
        .filter(TasaCambio.empresa_id == empresa.id)
        .order_by(TasaCambio.fecha.desc())
        .limit(60)
        .all()
    )


@router.get("/ultima", response_model=TasaCambioResponse)
def obtener_ultima(
    db: Session = Depends(get_db),
    _: Usuario = Depends(obtener_usuario_actual),
):
    empresa = obtener_empresa_tenant(db)
    ultima = obtener_ultima_tasa(db, empresa.id)
    if not ultima:
        raise HTTPException(status_code=404, detail="No hay tasas de cambio registradas")
    return ultima


@router.post("/convertir", response_model=ConversionMonedaResponse)
def convertir_moneda(
    body: ConversionMonedaRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(obtener_usuario_actual),
):
    empresa = obtener_empresa_tenant(db)
    tasa = obtener_ultima_tasa(db, empresa.id)
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
