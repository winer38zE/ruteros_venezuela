"""Historial de comportamiento sin consultar ventas si el cliente aún no tiene id."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.models.core import Cliente
from app.services.buro_credito import actualizar_historial_comportamiento


def test_actualizar_historial_sin_id_no_consulta_ventas():
    db = MagicMock()
    cliente = Cliente(nombre="Nuevo", identificacion="V12345678")
    assert cliente.id is None

    actualizar_historial_comportamiento(db, cliente)

    db.query.assert_not_called()
