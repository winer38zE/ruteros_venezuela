from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import TasaCambio, Empresa
from app.schemas.core import TasaCambioCreate, TasaCambioResponse
from typing import List

router = APIRouter()


@router.post("/", response_model=TasaCambioResponse)
def registrar_tasa(tasa: TasaCambioCreate, db: Session = Depends(get_db)):
    empresa_actual = db.query(Empresa).first()
    if not empresa_actual:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")

    nueva_tasa = TasaCambio(
        empresa_id=empresa_actual.id,
        momento=tasa.momento,
        usd_bs=tasa.usd_bs,
        eur_bs=tasa.eur_bs,
    )

    db.add(nueva_tasa)
    db.commit()
    db.refresh(nueva_tasa)

    return nueva_tasa


@router.get("/", response_model=List[TasaCambioResponse])
def listar_tasas(db: Session = Depends(get_db)):
    return db.query(TasaCambio).all()


@router.get("/ultima", response_model=TasaCambioResponse)
def obtener_ultima_tasa(db: Session = Depends(get_db)):
    ultima = (
        db.query(TasaCambio)
        .order_by(TasaCambio.fecha.desc())
        .first()
    )
    if not ultima:
        raise HTTPException(status_code=400, detail="No hay tasas de cambio registradas")
    return ultima
