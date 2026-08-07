import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/productos_service.dart';
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
  final _nombreCtrl = TextEditingController();
  final _skuCtrl = TextEditingController();
  final _precioUsdCtrl = TextEditingController();
  final _precioVesCtrl = TextEditingController();
  final _precioCopCtrl = TextEditingController();
  final _costoCtrl = TextEditingController();
  final _stockCtrl = TextEditingController();
  final _stockMinCtrl = TextEditingController();

  String? _categoria;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    final p = widget.producto;
    if (p != null) {
      _nombreCtrl.text = p.nombre;
      _skuCtrl.text = p.sku ?? '';
      _precioUsdCtrl.text = p.precioUsd.toString();
      if (p.precioVes != null) _precioVesCtrl.text = p.precioVes.toString();
      if (p.precioCop != null) _precioCopCtrl.text = p.precioCop.toString();
      _costoCtrl.text = p.costoUsd.toString();
      _stockCtrl.text = p.stock.toString();
      _stockMinCtrl.text = p.stockMinimo.toString();
      _categoria = p.categoria;
    } else {
      _categoria = ProductosService.categorias.first;
    }
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

  Future<void> _guardar() async {
    final nombre = _nombreCtrl.text.trim();
    final precioUsd = _parseOpt(_precioUsdCtrl.text);
    final costo = _parseOpt(_costoCtrl.text) ?? 0;
    final stockMin = int.tryParse(_stockMinCtrl.text) ?? 0;

    if (nombre.isEmpty || precioUsd == null || precioUsd <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nombre y precio USD son obligatorios')),
      );
      return;
    }

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
        final stockInicial = int.tryParse(_stockCtrl.text) ?? 0;
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
        );
      }
      if (!mounted) return;
      Navigator.pop(context, true);
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
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
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
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassContainer(
            accentColor: AppColors.violet,
            child: Column(
              children: [
                TextField(
                  controller: _nombreCtrl,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Nombre del producto',
                    prefixIcon: Icon(Icons.label_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _skuCtrl,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Código de barras / SKU',
                    prefixIcon: Icon(Icons.qr_code_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _categoria,
                  decoration: const InputDecoration(
                    labelText: 'Categoría',
                    prefixIcon: Icon(Icons.category_rounded),
                  ),
                  dropdownColor: AppColors.bgElevated,
                  items: ProductosService.categorias
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) => setState(() => _categoria = v),
                ),
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
                const SizedBox(height: 12),
                TextField(
                  controller: _precioUsdCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Precio USD',
                    prefixIcon: Icon(Icons.attach_money_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _precioVesCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Precio VES (opcional)',
                    prefixIcon: Icon(Icons.currency_exchange_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _precioCopCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Precio COP (opcional)',
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
              children: [
                TextField(
                  controller: _costoCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Costo del producto (USD)',
                    prefixIcon: Icon(Icons.price_change_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                if (!widget.esEdicion)
                  TextField(
                    controller: _stockCtrl,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: AppColors.textPrimary),
                    decoration: const InputDecoration(
                      labelText: 'Stock inicial',
                      prefixIcon: Icon(Icons.inventory_rounded),
                    ),
                  ),
                if (!widget.esEdicion) const SizedBox(height: 12),
                TextField(
                  controller: _stockMinCtrl,
                  keyboardType: TextInputType.number,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Punto mínimo de reorden',
                    prefixIcon: Icon(Icons.notifications_active_rounded),
                    hintText: 'Alerta cuando el stock llegue a este nivel',
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
    );
  }
}
