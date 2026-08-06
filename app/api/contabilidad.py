from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import AsientoContable, Empresa, Usuario
from app.schemas.core import (
    AsientoContableResponse,
    ResumenContableResponse,
    ExportacionExcelInfo,
)
from app.services.contabilidad import calcular_resumen_contable
from app.services.excel_export import generar_reporte_contable, obtener_metadatos_exportacion

router = APIRouter()


@router.get("/resumen", response_model=ResumenContableResponse)
def resumen_contable(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    return calcular_resumen_contable(db, dueno.empresa_id)


@router.get("/asientos", response_model=List[AsientoContableResponse])
def listar_asientos(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    return (
        db.query(AsientoContable)
        .filter(AsientoContable.empresa_id == dueno.empresa_id)
        .options(joinedload(AsientoContable.lineas))
        .order_by(AsientoContable.fecha.desc())
        .all()
    )


@router.get("/exportar-excel/info", response_model=ExportacionExcelInfo)
def info_exportacion_excel(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    """Previsualización del reporte antes de descargar (Flutter — botón un clic)."""
    empresa = db.query(Empresa).filter(Empresa.id == dueno.empresa_id).first()
    nombre = empresa.nombre if empresa else "Empresa"
    meta = obtener_metadatos_exportacion(
        db, dueno.empresa_id, nombre, fecha_desde, fecha_hasta
    )
    return {
        **meta,
        "hojas": [
            "Resumen Ejecutivo",
            "Libro Diario",
            "Inventario Valorado",
            "Movimientos Financieros",
            "Nomina Empleados",
        ],
        "formato": "xlsx",
    }


@router.get("/exportar-excel")
def exportar_excel_contable(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    """Fase 3 — descarga Excel profesional (solo rol DUEÑO)."""
    empresa = db.query(Empresa).filter(Empresa.id == dueno.empresa_id).first()
    nombre = empresa.nombre if empresa else "Empresa"

    buffer = generar_reporte_contable(
        db,
        dueno.empresa_id,
        nombre,
        fecha_desde,
        fecha_hasta,
    )

    slug = "".join(c if c.isalnum() else "_" for c in nombre)[:30]
    filename = f"EDNETPRO_{slug}_{datetime.utcnow():%Y%m%d_%H%M}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
