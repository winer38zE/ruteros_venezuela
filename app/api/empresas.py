from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import obtener_usuario_actual, require_admin_o_dueno
from app.core.tenant import obtener_empresa_tenant
from app.models.core import CuentaBancaria, Empresa, Usuario
from app.schemas.core import (
    EmpresaCreate,
    EmpresaResponse,
    DatosBancariosResponse,
    DatosBancariosUpdate,
    CuentaBancariaCreate,
    CuentaBancariaResponse,
)

# APIRouter nos permite agrupar rutas relacionadas
router = APIRouter()

@router.post("/", response_model=EmpresaResponse)
def crear_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    # 1. Creamos la instancia basada en el modelo de base de datos
    # No le pasamos el 'id' porque SQLAlchemy generará el UUID automáticamente
    nueva_empresa = Empresa(nombre=empresa.nombre)
    
    # 2. La añadimos a la sesión y guardamos (commit)
    db.add(nueva_empresa)
    db.commit()
    
    # 3. Refrescamos para obtener los datos generados por la BD (como el id y fecha)
    db.refresh(nueva_empresa)
    
    return nueva_empresa


def _datos_bancarios(empresa: Empresa) -> DatosBancariosResponse:
    banco = (empresa.banco or "").strip() or None
    tipo = (empresa.tipo_cuenta or "").strip() or None
    numero = (empresa.numero_cuenta or "").strip() or None
    cedula = (empresa.cedula_nit or "").strip() or None
    return DatosBancariosResponse(
        banco=banco,
        tipo_cuenta=tipo,
        numero_cuenta=numero,
        cedula_nit=cedula,
        configurado=bool(banco or numero),
    )


def _empresa_del_usuario(db: Session, usuario: Usuario) -> Empresa:
    empresa = obtener_empresa_tenant(db)
    if usuario.empresa_id != empresa.id:
        raise HTTPException(status_code=403, detail="La empresa no corresponde al usuario")
    return empresa


@router.get("/datos-bancarios", response_model=DatosBancariosResponse)
def obtener_datos_bancarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return _datos_bancarios(_empresa_del_usuario(db, usuario))


@router.put("/datos-bancarios", response_model=DatosBancariosResponse)
def actualizar_datos_bancarios(
    datos: DatosBancariosUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    empresa = _empresa_del_usuario(db, usuario)
    empresa.banco = (datos.banco or "").strip() or None
    empresa.tipo_cuenta = (datos.tipo_cuenta or "").strip() or None
    empresa.numero_cuenta = (datos.numero_cuenta or "").strip() or None
    empresa.cedula_nit = (datos.cedula_nit or "").strip() or None
    db.commit()
    db.refresh(empresa)
    return _datos_bancarios(empresa)


def _texto(valor: Optional[str], respaldo: str) -> str:
    limpio = (valor or "").strip()
    return limpio or respaldo


def sembrar_cuenta_inicial(db: Session, empresa: Empresa) -> None:
    existe = (
        db.query(CuentaBancaria.id)
        .filter(CuentaBancaria.empresa_id == empresa.id)
        .first()
    )
    if existe:
        return
    numero = (empresa.numero_cuenta or "").strip()
    if not numero:
        return
    db.add(
        CuentaBancaria(
            empresa_id=empresa.id,
            banco=_texto(empresa.banco, "Banco"),
            tipo_cuenta=_texto(empresa.tipo_cuenta, "Ahorro"),
            numero_cuenta=numero,
            titular=_texto(empresa.nombre, "Titular"),
            documento=_texto(empresa.cedula_nit, "Sin documento"),
            canal="transferencia",
            activa=True,
        )
    )
    db.commit()


def resolver_cuenta_transferencia(
    db: Session,
    empresa_id,
    cuenta_id: Optional[UUID],
    canal: str = "transferencia",
) -> Optional[CuentaBancaria]:
    canal = canal if canal in ("transferencia", "pago_movil") else "transferencia"
    activas = (
        db.query(CuentaBancaria)
        .filter(CuentaBancaria.empresa_id == empresa_id, CuentaBancaria.activa.is_(True))
        .all()
    )
    del_canal = [item for item in activas if (item.canal or "transferencia") == canal]
    if cuenta_id is None:
        if del_canal:
            raise HTTPException(status_code=400, detail="Selecciona la cuenta de destino")
        return None
    cuenta = next((item for item in del_canal if item.id == cuenta_id), None)
    if not cuenta:
        raise HTTPException(
            status_code=400,
            detail="La cuenta no corresponde a este método de pago",
        )
    return cuenta


def _listar_cuentas_activas(db: Session, empresa: Empresa) -> List[CuentaBancaria]:
    sembrar_cuenta_inicial(db, empresa)
    return (
        db.query(CuentaBancaria)
        .filter(CuentaBancaria.empresa_id == empresa.id, CuentaBancaria.activa.is_(True))
        .order_by(CuentaBancaria.banco.asc(), CuentaBancaria.numero_cuenta.asc())
        .all()
    )


@router.get("/cuentas-bancarias", response_model=List[CuentaBancariaResponse])
def listar_cuentas_bancarias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return _listar_cuentas_activas(db, _empresa_del_usuario(db, usuario))


@router.post("/cuentas-bancarias", response_model=CuentaBancariaResponse)
def crear_cuenta_bancaria(
    datos: CuentaBancariaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    empresa = _empresa_del_usuario(db, usuario)
    canal = datos.canal
    if canal == "pago_movil":
        telefono = (datos.telefono or "").strip()
        if not telefono:
            raise HTTPException(status_code=400, detail="Indica el teléfono del Pago Móvil")
        tipo_cuenta = "Pago móvil"
        numero_cuenta = telefono
    else:
        tipo_cuenta = (datos.tipo_cuenta or "").strip()
        numero_cuenta = (datos.numero_cuenta or "").strip()
        telefono = None
        if not tipo_cuenta or not numero_cuenta:
            raise HTTPException(
                status_code=400,
                detail="Indica el tipo y el número de cuenta de la transferencia",
            )
    cuenta = CuentaBancaria(
        empresa_id=empresa.id,
        banco=datos.banco.strip(),
        tipo_cuenta=tipo_cuenta,
        numero_cuenta=numero_cuenta,
        telefono=telefono,
        titular=datos.titular.strip(),
        documento=datos.documento.strip(),
        canal=canal,
        activa=True,
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.post("/cuentas-bancarias/{cuenta_id}/archivar", response_model=CuentaBancariaResponse)
def archivar_cuenta_bancaria(
    cuenta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    empresa = _empresa_del_usuario(db, usuario)
    cuenta = (
        db.query(CuentaBancaria)
        .filter(CuentaBancaria.id == cuenta_id, CuentaBancaria.empresa_id == empresa.id)
        .first()
    )
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
    cuenta.activa = False
    db.commit()
    db.refresh(cuenta)
    return cuenta