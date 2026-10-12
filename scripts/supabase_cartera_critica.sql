-- Cartera crítica: historial de notas de seguimiento.
-- Idempotente. Úsalo en el editor SQL de Supabase si la API no crea
-- el esquema con SQLAlchemy (create_all). Los códigos se guardan como
-- texto; la app valida motivo y estado.

CREATE TABLE IF NOT EXISTS notas_seguimiento_cobranza (
    id UUID PRIMARY KEY,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    fecha TIMESTAMP NOT NULL,
    motivo VARCHAR(40) NOT NULL,
    estado_consideracion VARCHAR(40) NOT NULL,
    observacion TEXT NOT NULL,
    fecha_creacion TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_notas_seguimiento_empresa
    ON notas_seguimiento_cobranza (empresa_id);

CREATE INDEX IF NOT EXISTS ix_notas_seguimiento_cliente
    ON notas_seguimiento_cobranza (cliente_id);

CREATE INDEX IF NOT EXISTS ix_notas_seguimiento_empresa_cliente
    ON notas_seguimiento_cobranza (empresa_id, cliente_id);

-- Plazos de gracia. No altera cuotas ni ventas.
CREATE TABLE IF NOT EXISTS acuerdos_pago (
    id UUID PRIMARY KEY,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    monto_acordado_usd NUMERIC(12, 2) NOT NULL,
    fecha_limite DATE NOT NULL,
    cuotas_pactadas INTEGER NOT NULL DEFAULT 1,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    nota_consideracion TEXT NOT NULL,
    fecha_creacion TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_acuerdos_pago_empresa_cliente
    ON acuerdos_pago (empresa_id, cliente_id);
