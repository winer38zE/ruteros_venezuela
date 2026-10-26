# PocketBase y asistente de voz IA

## Importante: no uses una colección `pedidos`

Ruteros guarda los pedidos de voz en:

| Intención IA | Colección PocketBase | Notas |
|--------------|----------------------|--------|
| `crear_pedido` | **`ventas`** + **`detalles_venta`** | Una venta al contado + líneas de producto |
| `registrar_cliente` | **`clientes`** | |
| `registrar_cobro` | **`cobros`** | Requiere **`ventas`** existente con saldo |

También necesitas **`productos`** (catálogo) y, en la práctica, **`empresas`**, **`usuarios`**, **`tasas_cambio`**.

---

## Opción recomendada: script automático (SSH al servidor API)

En Coolify, entra al contenedor **FastAPI** (no al de PocketBase) con las variables ya configuradas (`POCKETBASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`):

```bash
# Desde tu PC, SSH al VPS
ssh usuario@tu-servidor

# Contenedor API (nombre según Coolify; ej. ruteros-api)
docker ps
docker exec -it NOMBRE_CONTENEDOR_API bash

cd /app   # o la ruta donde está el repo
python scripts/sync_pocketbase_schema.py
python scripts/verificar_colecciones_asistente_ia.py
```

El primer script **crea o actualiza todas las colecciones** desde los modelos SQLAlchemy. El segundo confirma que las colecciones del asistente existen y son legibles.

Si la API ya arrancó con bootstrap correcto, el esquema suele crearse solo al iniciar; el script sirve cuando faltan colecciones tras un deploy manual.

---

## Opción manual en el panel PocketBase

Solo si no puedes ejecutar el script. Los nombres de campo deben coincidir **exactamente** con la API (snake_case).

### `clientes` (registrar_cliente)

Campos mínimos que escribe la IA / ORM:

| Campo | Tipo PB | Requerido |
|-------|---------|-----------|
| empresa_id | Relation → empresas | Sí |
| nombre | Text | Sí |
| identificacion | Text | Sí (único global) |
| telefono | Text | No |
| direccion | Text / Editor | No |
| vendedor_id | Relation → usuarios | No |
| tipo_cliente | Text | No (detal/mayorista) |
| score_credito, total_compras, monto_compras_usd, total_pagos, monto_pagos_usd | Number | Defaults en código |
| estado_morosidad, clasificacion_credito | Text | Defaults |
| tipo_visita_ruta, dia_visita, orden_secuencial, dia_ruta, orden_ruta | según modelo | No |

### `ventas` (crear_pedido — cabecera)

| Campo | Tipo PB | Requerido |
|-------|---------|-----------|
| empresa_id | Relation → empresas | Sí |
| cliente_id | Relation → clientes | Sí |
| vendedor_id | Relation → usuarios | Sí |
| fecha | Date | Sí |
| total_usd | Number | Sí |
| tasa_usd_aplicada, tasa_eur_aplicada | Number | Sí |
| frecuencia_pago | Text | Sí (`contado`, etc.) |
| estado | Text | Sí (`pagada`, `pendiente`, …) |
| metodo_pago | Text | Sí |
| tipo_tasa_usd | Text | No (bcv) |

### `detalles_venta` (crear_pedido — líneas)

| Campo | Tipo PB | Requerido |
|-------|---------|-----------|
| venta_id | Relation → ventas | Sí |
| producto_id | Relation → productos | Sí |
| cantidad | Number | Sí |
| precio_unitario_usd | Number | Sí |

### `cobros` (registrar_cobro)

| Campo | Tipo PB | Requerido |
|-------|---------|-----------|
| empresa_id | Relation → empresas | Sí |
| venta_id | Relation → ventas | Sí |
| cobrador_id | Relation → usuarios | Sí |
| fecha | Date | Sí |
| monto_usd | Number | Sí |
| moneda_pago | Text | Sí (`dolar`, `transferencia`, `pago_movil`, …) |
| tasa_usd_aplicada, tasa_eur_aplicada | Number | Sí |
| es_transferencia, verificado | Bool | Sí |

---

## Comprobar desde fuera

```bash
curl -s "$POCKETBASE_URL/api/collections/clientes" -H "Authorization: Bearer ADMIN_TOKEN"
```

O reinicia la API y revisa logs: `preparar_esquema_pocketbase` no debe listar colecciones faltantes.
