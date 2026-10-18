# PocketBase — Fase 1 multiregión (manual o automático)

## Opción A — Automático (recomendado)

Con la API en marcha y variables `ADMIN_EMAIL` / `ADMIN_PASSWORD`:

```bash
python scripts/sync_pocketbase_schema.py
python scripts/seed_paises.py
```

Eso crea la colección **`paises`**, añade **`pais_id`** a las tablas del código y carga Colombia, Venezuela, Brasil, Ecuador, Perú, México y USA.

---

## Opción B — Panel administrativo PocketBase

### 1. Crear colección `paises`

| Campo | Tipo | Requerido |
|-------|------|-----------|
| nombre | Text | Sí |
| codigo_iso | Text (max 3) | Sí, único |
| moneda_principal | Text (max 3) | Sí |
| simbolo_moneda | Text (max 8) | Sí |
| locale | Text | No |
| zona_horaria | Text | No |
| activo | Bool | Sí (default true) |
| configuracion_bancaria | JSON | Sí |
| configuracion_fiscal | JSON | No |
| configuracion_ui | JSON | No |

**Reglas API:** `listRule` vacío (lectura pública para el login en Fase 3). Create/update/delete solo admin.

### 2. Insertar países (resumen)

| nombre | codigo_iso | moneda_principal | simbolo_moneda |
|--------|------------|------------------|----------------|
| Colombia | CO | COP | $ |
| Venezuela | VE | VES | Bs. |
| Brasil | BR | BRL | R$ |
| Ecuador | EC | USD | $ |
| Perú | PE | PEN | S/ |
| México | MX | MXN | $ |
| Estados Unidos | US | USD | $ |

Copia el JSON de `configuracion_bancaria` desde `app/data/catalogo_paises.py` o ejecuta `seed_paises.py`.

### 3. Añadir `pais_id` en otras colecciones

Campo **Relation** → `paises`, min 1, max 1.

Colecciones:

- empresas, usuarios
- cuentas_bancarias, cuentas_bancarias_empleados
- tasas_cambio
- productos, almacenes, lotes_inventario, movimientos_inventario
- movimientos_financieros, pagos_nomina

### 4. Migrar datos existentes

1. Copia el **ID** del registro Venezuela en `paises`.
2. En cada colección anterior, edita registros viejos y asigna ese `pais_id`.
3. Cuando no queden vacíos, marca `pais_id` como **Required** (opcional; el código acepta null durante la transición).

---

## Login Flutter (Fase 2)

La app carga países desde **`GET /api/v1/paises`** (FastAPI, sin login). No hace falta exponer PocketBase al cliente si usas ese endpoint.

**Opcional — lectura directa desde PocketBase:** en la colección `paises`, reglas **List** y **View** en blanco (`""`) o públicas, para que un SDK móvil pueda listar antes del login. Create/update/delete solo admin.

Tras desplegar la API:

1. `python scripts/sync_pocketbase_schema.py`
2. `python scripts/seed_paises.py`
3. Reinicia la API (bootstrap asigna `pais_id` Venezuela a usuarios demo sin país).

Login: **`POST /api/v1/auth/login`** con `username`, `password` y **`pais_id`** (obligatorio). Respuesta incluye objeto **`pais`** (moneda, símbolo, ISO).
