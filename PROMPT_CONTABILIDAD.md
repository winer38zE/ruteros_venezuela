# PROMPT_CONTABILIDAD — ED NET PRO / Ruteros

## Fase 1 ✅ Motor fiscal + integración contable básica
- `ConfiguracionFiscal` por empresa (multi-tenant vía `empresa_id`)
- Presets fiscales por país (VE, CO, PA…)
- Libro diario automático en Ventas y Cobros (partida doble)
- Consulta de asientos (`GET /api/v1/contabilidad/asientos`)
- Resumen contable básico (`GET /api/v1/contabilidad/resumen`)

## Fase 2 ✅ Inventario avanzado
- Multi-almacén, lotes FIFO, precios mayorista/detal
- Stock en tiempo real y movimientos auditables
- Ventas con detalle descuentan stock automáticamente

## Fase 3 ✅ Reportes ejecutivos Excel
- `GET /api/v1/contabilidad/exportar-excel/info` — previsualización (Flutter)
- `GET /api/v1/contabilidad/exportar-excel` — descarga `.xlsx` (solo DUEÑO)
- **Hoja 1:** Resumen Ejecutivo (ingresos, CxC, IVA, IGTF, Bs vs divisas, inventario)
- **Hoja 2:** Libro Diario con fórmulas SUM y conversión multimoneda
- **Hoja 3:** Inventario Valorado con totales automáticos
- Formato contable profesional (colores corporativos, freeze panes, bordes)

## Reglas
- No modificar columnas existentes en modelos base
- Nuevas tablas solo como extensiones
- Usar `Numeric` para montos; UUID (`GUID`) para IDs
- Todo filtrado por `empresa_id`

## Uso Flutter (botón un clic)
Ver carpeta `mobile/` — app Flutter con pantalla de Contabilidad e exportación Excel.
