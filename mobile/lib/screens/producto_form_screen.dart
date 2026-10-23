import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/productos_service.dart';
import '../services/proveedores_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class ProductoFormScreen extends StatefulWidget {
  const ProductoFormScreen({super.key, this.producto});

  final ProductoDetalle? producto;

  bool get esEdicion => producto != null;

  @override
  State<ProductoFormScreen> createState() => _ProductoFormScreenState();
}

class _ProductoFormScreenState extends State<ProductoFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombreCtrl = TextEditingController();
  final _skuCtrl = TextEditingController();
  final _precioUsdCtrl = TextEditingController();
  final _precioVesCtrl = TextEditingController();
  final _precioCopCtrl = TextEditingController();
  final _costoCtrl = TextEditingController();
  final _stockCtrl = TextEditingController();
  final _stockMinCtrl = TextEditingController();

  static const _nuevaCategoriaToken = '__nueva_categoria__';

  late List<String> _categorias;
  String? _categoria;
  String? _proveedorId;
  List<Proveedor> _proveedores = [];
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    final p = widget.producto;
    _categorias = ProductosService.combinarCategorias(
      extra: p?.categoria != null ? [p!.categoria!] : null,
    );
    if (p != null) {
      _nombreCtrl.text = p.nombre;
      _skuCtrl.text = p.sku ?? '';
      _precioUsdCtrl.text = p.precioUsd.toString();
      if (p.precioVes != null) _precioVesCtrl.text = p.precioVes.toString();
      if (p.precioCop != null) _precioCopCtrl.text = p.precioCop.toString();
      _costoCtrl.text = p.costoUsd.toString();
      _stockCtrl.text = p.stock.toString();
      _stockMinCtrl.text = p.stockMinimo.toString();
      _categoria = p.categoria ?? _categorias.first;
    } else {
      _categoria = _categorias.first;
    }
    _cargarProveedores();
  }

  Future<void> _cargarProveedores() async {
    try {
      _proveedores = await context.read<AppState>().proveedores.listar();
      if (mounted) setState(() {});
    } catch (_) {}
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _skuCtrl.dispose();
    _precioUsdCtrl.dispose();
    _precioVesCtrl.dispose();
    _precioCopCtrl.dispose();
    _costoCtrl.dispose();
    _stockCtrl.dispose();
    _stockMinCtrl.dispose();
    super.dispose();
  }

  double? _parseOpt(String text) {
    if (text.trim().isEmpty) return null;
    return double.tryParse(text.replaceAll(',', '.'));
  }

  Future<void> _agregarCategoriaPersonalizada() async {
    final ctrl = TextEditingController();
    final nombre = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgElevated,
        title: const Text('Nueva categoría'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Ej. Bebidas, Limpieza…'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () {
              final t = ctrl.text.trim();
              if (t.isNotEmpty) Navigator.pop(ctx, t);
            },
            child: const Text('Agregar'),
          ),
        ],
      ),
    );
    ctrl.dispose();
    if (nombre == null || !mounted) return;
    setState(() {
      if (!_categorias.contains(nombre)) {
        _categorias = ProductosService.combinarCategorias(extra: [nombre]);
      }
      _categoria = nombre;
    });
  }

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Revisa los campos marcados en rojo')),
      );
      return;
    }

    final nombre = _nombreCtrl.text.trim();
    final precioUsd = _parseOpt(_precioUsdCtrl.text)!;
    final costo = _parseOpt(_costoCtrl.text) ?? 0;
    final stockMin = int.tryParse(_stockMinCtrl.text.trim()) ?? 0;

    setState(() => _guardando = true);
    try {
      final svc = context.read<AppState>().productos;
      if (widget.esEdicion) {
        await svc.actualizar(
          widget.producto!.id,
          nombre: nombre,
          sku: _skuCtrl.text.trim(),
          categoria: _categoria,
          precioUsd: precioUsd,
          precioVes: _parseOpt(_precioVesCtrl.text),
          precioCop: _parseOpt(_precioCopCtrl.text),
          costoUsd: costo,
          stockMinimo: stockMin,
        );
      } else {
        final stockInicial = int.parse(_stockCtrl.text.trim());
        await svc.crear(
          nombre: nombre,
          sku: _skuCtrl.text.trim().isEmpty ? null : _skuCtrl.text.trim(),
          categoria: _categoria,
          precioUsd: precioUsd,
          precioVes: _parseOpt(_precioVesCtrl.text),
          precioCop: _parseOpt(_precioCopCtrl.text),
          costoUsd: costo,
          stockInicial: stockInicial,
          stockMinimo: stockMin,
          proveedorId: _proveedorId,
        );
      }
      if (!mounted) return;
      Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  String? _validarNombre(String? v) {
    if (v == null || v.trim().isEmpty) return 'El nombre es obligatorio';
    return null;
  }

  String? _validarPrecioUsd(String? v) {
    final n = _parseOpt(v ?? '');
    if (n == null || n <= 0) return 'Indica un precio USD mayor a 0';
    return null;
  }

  String? _validarStockInicial(String? v) {
    if (widget.esEdicion) return null;
    if (v == null || v.trim().isEmpty) return 'El stock inicial es obligatorio';
    final n = int.tryParse(v.trim());
    if (n == null || n < 0) return 'Indica un número entero ≥ 0';
    return null;
  }

  String? _validarOpcionalPositivo(String? v, {bool entero = false}) {
    if (v == null || v.trim().isEmpty) return null;
    if (entero) {
      final n = int.tryParse(v.trim());
      if (n == null || n < 0) return 'Número entero inválido';
    } else {
      final n = _parseOpt(v);
      if (n == null || n < 0) return 'Monto inválido';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: widget.esEdicion ? 'Editar Producto' : 'Nuevo Producto',
      accentColor: AppColors.violet,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: _guardando
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.bgDeep),
                  )
                : const Icon(Icons.save_rounded),
            label: Text(_guardando ? 'Guardando…' : 'Guardar producto'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: AppColors.violet,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            GlassContainer(
              accentColor: AppColors.violet,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Datos del producto',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _nombreCtrl,
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: _validarNombre,
                    textCapitalization: TextCapitalization.sentences,
                    decoration: const InputDecoration(
                      labelText: 'Nombre del producto *',
                      prefixIcon: Icon(Icons.label_rounded),
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: _categoria,
                    decoration: const InputDecoration(
                      labelText: 'Categoría *',
                      prefixIcon: Icon(Icons.category_rounded),
                    ),
                    dropdownColor: AppColors.bgElevated,
                    items: [
                      ..._categorias.map(
                        (c) => DropdownMenuItem(value: c, child: Text(c)),
                      ),
                      const DropdownMenuItem(
                        value: _nuevaCategoriaToken,
                        child: Text('➕ Crear categoría…'),
                      ),
                    ],
                    onChanged: (v) async {
                      if (v == _nuevaCategoriaToken) {
                        await _agregarCategoriaPersonalizada();
                        return;
                      }
                      setState(() => _categoria = v);
                    },
                    validator: (v) => v == null || v.isEmpty ? 'Elige una categoría' : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _skuCtrl,
                    style: const TextStyle(color: AppColors.textPrimary),
                    decoration: const InputDecoration(
                      labelText: 'SKU / Código de barras (opcional)',
                      prefixIcon: Icon(Icons.qr_code_rounded),
                    ),
                  ),
                  if (_proveedores.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      value: _proveedorId,
                      decoration: const InputDecoration(
                        labelText: 'Proveedor (opcional)',
                        prefixIcon: Icon(Icons.local_shipping_outlined),
                      ),
                      dropdownColor: AppColors.bgElevated,
                      items: [
                        const DropdownMenuItem(value: null, child: Text('Sin proveedor')),
                        ..._proveedores.map(
                          (p) => DropdownMenuItem(value: p.id, child: Text(p.nombre)),
                        ),
                      ],
                      onChanged: (v) => setState(() => _proveedorId = v),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 14),
            GlassContainer(
              accentColor: AppColors.emerald,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Precios de venta', style: TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text(
                    'Si dejas VES o COP vacíos, el servidor puede calcularlos con la tasa del día.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _precioUsdCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: _validarPrecioUsd,
                    decoration: const InputDecoration(
                      labelText: 'Precio de venta USD *',
                      prefixIcon: Icon(Icons.attach_money_rounded),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _precioVesCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: (v) => _validarOpcionalPositivo(v),
                    decoration: const InputDecoration(
                      labelText: 'Precio de venta VES (opcional)',
                      prefixIcon: Icon(Icons.currency_exchange_rounded),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _precioCopCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: (v) => _validarOpcionalPositivo(v),
                    decoration: const InputDecoration(
                      labelText: 'Precio de venta COP (opcional)',
                      prefixIcon: Icon(Icons.currency_exchange_rounded),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            GlassContainer(
              accentColor: AppColors.amber,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Inventario', style: TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _costoCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: (v) => _validarOpcionalPositivo(v),
                    decoration: const InputDecoration(
                      labelText: 'Costo de compra USD (opcional)',
                      prefixIcon: Icon(Icons.price_change_rounded),
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (!widget.esEdicion)
                    TextFormField(
                      controller: _stockCtrl,
                      keyboardType: TextInputType.number,
                      style: const TextStyle(color: AppColors.textPrimary),
                      validator: _validarStockInicial,
                      decoration: const InputDecoration(
                        labelText: 'Stock inicial *',
                        prefixIcon: Icon(Icons.inventory_rounded),
                        hintText: 'Cantidad en unidades',
                      ),
                    ),
                  if (!widget.esEdicion) const SizedBox(height: 12),
                  TextFormField(
                    controller: _stockMinCtrl,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: AppColors.textPrimary),
                    validator: (v) => _validarOpcionalPositivo(v, entero: true),
                    decoration: const InputDecoration(
                      labelText: 'Punto mínimo de reorden (alerta)',
                      prefixIcon: Icon(Icons.notifications_active_rounded),
                      hintText: 'Ej. 5 — avisa cuando el stock llegue ahí',
                    ),
                  ),
                  if (widget.esEdicion) ...[
                    const SizedBox(height: 12),
                    Text(
                      'Stock actual: ${widget.producto!.stock} uds — usa "Ajustar" en la lista para entradas/salidas.',
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 12, height: 1.4),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
