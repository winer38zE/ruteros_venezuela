from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.models.core import ConfiguracionFiscal, Empresa
from app.schemas.core import (
    ConfiguracionFiscalCreate,
    ConfiguracionFiscalUpdate,
    ConfiguracionFiscalResponse,
    PresetFiscalResponse,
)
from app.services.fiscal_engine import (
    listar_paises_disponibles,
    obtener_preset_pais,
    aplicar_preset_a_config,
)

router = APIRouter()


def _obtener_empresa(db: Session) -> Empresa:
    empresa = db.query(Empresa).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")
    return empresa


@router.get("/presets", response_model=List[PresetFiscalResponse])
def listar_presets_fiscales():
    return listar_paises_disponibles()


@router.get("/presets/{pais}", response_model=PresetFiscalResponse)
def obtener_preset_fiscal(pais: str):
    try:
        return obtener_preset_pais(pais)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=ConfiguracionFiscalResponse)
def crear_configuracion_fiscal(
    config: ConfiguracionFiscalCreate,
    db: Session = Depends(get_db),
):
    empresa = _obtener_empresa(db)

    existente = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa.id)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="La empresa ya tiene configuración fiscal. Use PUT para actualizar.",
        )

    nueva = ConfiguracionFiscal(empresa_id=empresa.id, **config.model_dump())
    aplicar_preset_a_config(nueva, config.pais)
    # Restaurar overrides explícitos del request
    for campo in ("iva_porcentaje", "igtf_porcentaje", "aplica_igtf_divisas", "moneda_base", "razon_social", "rif"):
        valor = getattr(config, campo, None)
        if valor is not None:
            setattr(nueva, campo, valor)

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=ConfiguracionFiscalResponse)
def obtener_configuracion_fiscal(db: Session = Depends(get_db)):
    empresa = _obtener_empresa(db)

    config = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa.id)
        .first()
    )
    if not config:
        config = ConfiguracionFiscal(empresa_id=empresa.id, pais="VE")
        aplicar_preset_a_config(config, "VE")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/", response_model=ConfiguracionFiscalResponse)
def actualizar_configuracion_fiscal(
    config: ConfiguracionFiscalUpdate,
    db: Session = Depends(get_db),
):
    empresa = _obtener_empresa(db)

    existente = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa.id)
        .first()
    )
    if not existente:
        existente = ConfiguracionFiscal(empresa_id=empresa.id, pais="VE")
        aplicar_preset_a_config(existente, "VE")
        db.add(existente)
        db.flush()

    datos = config.model_dump(exclude_unset=True)
    if "pais" in datos:
        aplicar_preset_a_config(existente, datos["pais"])
        datos.pop("pais", None)

    for campo, valor in datos.items():
        setattr(existente, campo, valor)

    db.commit()
    db.refresh(existente)
    return existente
