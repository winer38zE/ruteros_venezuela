"""Claves biométricas aisladas por país + usuario."""


def scope_key(pais_id: str, usuario: str) -> str:
    return f"biometric:{pais_id.strip()}:{usuario.strip().lower()}"


def test_scope_key_incluye_pais_y_usuario():
    k_co = scope_key("pais-co", "Dueno")
    k_ve = scope_key("pais-ve", "Dueno")
    assert k_co != k_ve
    assert k_co == "biometric:pais-co:dueno"


def test_mismo_usuario_dos_paises_no_comparten_clave():
    usuario = "vendedor"
    paises = ["id-colombia", "id-mexico", "id-venezuela"]
    claves = {scope_key(p, usuario) for p in paises}
    assert len(claves) == 3
