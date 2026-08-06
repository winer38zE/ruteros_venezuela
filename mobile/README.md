# ED NET PRO — App Flutter (Ruteros Venezuela)

App móvil conectada al backend FastAPI multi-tenant.

## Requisitos

- Flutter SDK 3.2+
- Backend corriendo: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Configuración de la API

Edita `lib/config/api_config.dart` o usa variable de entorno al compilar:

| Entorno | URL base |
|---------|----------|
| Windows / desktop | `http://127.0.0.1:8000` |
| Android emulador | `http://10.0.2.2:8000` |
| Dispositivo físico | `http://<IP-de-tu-PC>:8000` |

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Instalación

```bash
cd mobile
flutter pub get
flutter run -d windows   # o android, chrome, etc.
```

> **Windows:** si falla con `ERROR_ACCESS_DENIED` al crear symlinks, activa **Modo de desarrollador** en Configuración de Windows o ejecuta la terminal como administrador.

## Módulos integrados

### Autenticación (Fase 1)
- Login por `username` → envía header `X-Usuario-Id` en cada request protegido

### Contabilidad (Fases 1 + 3) — solo DUEÑO
- Resumen contable en pantalla
- Previsualización del reporte Excel
- **Botón un clic:** exportar y abrir `.xlsx` para el contador

### Inventario (Fase 2) — solo DUEÑO
- Stock en tiempo real por producto
- Inventario valorado con totales

### Ventas en campo (VENDEDOR / DUEÑO)
- Listado de mis ventas (`GET /ventas/mis-ventas`)
- Nueva venta con carrito, cliente, almacén y descuento de stock
- Precio automático mayorista/detal según tipo de cliente
- ID de venta generado en el celular (offline-first)

### Cobros en campo (COBRADOR / DUEÑO)
- Ventas pendientes de cobro con saldo calculado
- Registro de cobro multimoneda (Bs, USD, EUR, Pago Móvil, Transferencia)
- Validación de monto vs saldo pendiente
- Listado de mis cobros
- ID de cobro generado en el celular (offline-first)

## Flujo de prueba

```bash
# Cargar datos demo (empresa, usuarios, productos, venta pendiente)
python scripts/seed_demo.py
```

1. Inicia el backend y crea datos (empresa, clientes, productos, almacén, tasa de cambio)
2. Crea usuarios: `dueno` (DUEÑO) y/o `vend` (VENDEDOR)
3. Login en la app → **Mis Ventas** → agrega productos → **Registrar Venta**
4. (Dueño) **Contabilidad** → **Exportar Excel para Contador**

## Estructura

```
mobile/lib/
  config/api_config.dart
  services/          # api_client, auth, catalogo, ventas, contabilidad, inventario
  screens/           # login, home, ventas, contabilidad, inventario
  providers/app_state.dart
```