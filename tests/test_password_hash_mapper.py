"""El hash bcrypt no debe recortarse a 15 caracteres al persistir."""
from __future__ import annotations

from app.api.auth import get_password_hash, verify_password
from app.core.pb_orm.mapper import model_to_record
from app.models.core import RolUsuario, Usuario


def test_model_to_record_conserva_hash_bcrypt_con_simbolo_dolar():
    hashed = get_password_hash("clave-de-12-ok")
    assert "$" in hashed
    assert len(hashed) > 15
    usuario = Usuario(
        id="abc123def456789",
        empresa_id="emp123456789012",
        nombre="Admin",
        username="dueno",
        password_hash=hashed,
        rol=RolUsuario.DUENO,
        activo=True,
    )
    payload = model_to_record(usuario)
    assert payload["password_hash"] == hashed
    assert len(payload["password_hash"]) != 15
    assert verify_password("clave-de-12-ok", payload["password_hash"])
