import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/finanzas_service.dart';
import '../services/proveedores_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class RegistrarMovimientoScreen extends StatefulWidget {
  const RegistrarMovimientoScreen({super.key, this.soloGasto = true});

  /// Si es true, solo muestra categorías de egreso (gastos/proveedores).
  final bool soloGasto;

  @override
  State<RegistrarMovimientoScreen> createState() => _RegistrarMovimientoScreenState();
}

class _RegistrarMovimientoScreenState extends State<RegistrarMovimientoScreen> {
  String _tipo = 'salida';
  String _categoria = 'gasto_moto';
  String _moneda = 'usd';
  String? _metodoPago = 'efectivo';
  String? _proveedorId;
  String? _comprobanteBase64;
  String? _comprobanteNombre;

  final _montoCtrl = TextEditingController();
  final _tasaCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _nuevoProveedorCtrl = TextEditingController();

  List<Proveedor> _proveedores = [];
  bool _cargandoProveedores = true;
  bool _guardando = false;
  bool _mostrarNuevoProveedor = false;

  @override
  void initState() {
    super.initState();
    if (widget.soloGasto) _tipo = 'salida';
    _cargarProveedores();
  }

  @override
  void dispose() {
    _montoCtrl.dispose();
    _tasaCtrl.dispose();
    _descCtrl.dispose();
    _nuevoProveedorCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarProveedores() async {
    try {
      _proveedores = await context.read<AppState>().proveedores.listar();
    } catch (_) {
      _proveedores = [];
    } finally {
      if (mounted) setState(() => _cargandoProveedores = false);
    }
  }

  List<(String, String)> get _categorias {
    if (widget.soloGasto) return FinanzasService.categoriasGasto;
    return _tipo == 'entrada' ? FinanzasService.categoriasEntrada : FinanzasService.categoriasSalida;
  }

  bool get _requiereProveedor => _categoria == 'pago_proveedor';
  bool get _requiereTasa => _moneda != 'usd';

  Future<void> _elegirComprobante() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery, maxWidth: 1600, imageQuality: 75);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() {
      _comprobanteBase64 = base64Encode(bytes);
      _comprobanteNombre = file.name;
    });
  }

  Future<void> _crearProveedorRapido() async {
    final nombre = _nuevoProveedorCtrl.text.trim();
    if (nombre.isEmpty) return;
    try {
      final p = await context.read<AppState>().proveedores.crear(nombre: nombre);
      setState(() {
        _proveedores = [..._proveedores, p];
        _proveedorId = p.id;
        _mostrarNuevoProveedor = false;
        _nuevoProveedorCtrl.clear();
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    }
  }

  Future<void> _guardar() async {
    final monto = double.tryParse(_montoCtrl.text.replaceAll(',', '.'));
    if (monto == null || monto <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un monto válido')),
      );
      return;
    }
    if (_descCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa una descripción')),
      );
      return;
    }
    if (_requiereProveedor && _proveedorId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona o crea un proveedor')),
      );
      return;
    }

    double? tasa;
    if (_requiereTasa) {
      tasa = double.tryParse(_tasaCtrl.text.replaceAll(',', '.'));
      if (tasa == null || tasa <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ingresa la tasa de cambio aplicada')),
        );
        return;
      }
    }

    setState(() => _guardando = true);
    try {
      final fin = context.read<AppState>().finanzas;
      if (_tipo == 'salida' || widget.soloGasto) {
        await fin.registrarGasto(
          categoria: _categoria,
          monto: monto,
          moneda: _moneda,
          descripcion: _descCtrl.text.trim(),
          metodoPago: _metodoPago,
          tasaAplicada: tasa,
          proveedorId: _proveedorId,
          comprobanteBase64: _comprobanteBase64,
        );
      } else {
        await fin.registrarMovimiento(
          tipo: _tipo,
          categoria: _categoria,
          montoUsd: monto,
          descripcion: _descCtrl.text.trim(),
          moneda: _moneda,
          metodoPago: _metodoPago,
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
    final titulo = widget.soloGasto ? 'Registrar Gasto' : 'Registrar Movimiento';

    return FuturisticScaffold(
      title: titulo,
      accentColor: AppColors.amber,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.save_rounded),
            label: Text(_guardando ? 'Guardando...' : 'Registrar egreso'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: AppColors.amber,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (!widget.soloGasto) ...[
            Row(
              children: [
                Expanded(
                  child: _TipoChip(
                    label: 'Entrada',
                    icon: Icons.arrow_downward_rounded,
                    color: AppColors.emerald,
                    selected: _tipo == 'entrada',
                    onTap: () => setState(() {
                      _tipo = 'entrada';
                      _categoria = FinanzasService.categoriasEntrada.first.$1;
                    }),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _TipoChip(
                    label: 'Salida',
                    icon: Icons.arrow_upward_rounded,
                    color: AppColors.amber,
                    selected: _tipo == 'salida',
                    onTap: () => setState(() {
                      _tipo = 'salida';
                      _categoria = FinanzasService.categoriasGasto.first.$1;
                    }),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
          ],
          GlassContainer(
            accentColor: AppColors.amber,
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: _categoria,
                  decoration: const InputDecoration(
                    labelText: 'Categoría de gasto',
                    prefixIcon: Icon(Icons.category_rounded),
                  ),
                  dropdownColor: AppColors.bgElevated,
                  items: _categorias.map((c) => DropdownMenuItem(value: c.$1, child: Text(c.$2))).toList(),
                  onChanged: (v) => setState(() {
                    _categoria = v!;
                    if (!_requiereProveedor) _proveedorId = null;
                  }),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: _montoCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: const InputDecoration(
                          labelText: 'Monto',
                          prefixIcon: Icon(Icons.attach_money_rounded),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _moneda,
                        decoration: const InputDecoration(labelText: 'Moneda'),
                        dropdownColor: AppColors.bgElevated,
                        items: FinanzasService.monedas
                            .map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2)))
                            .toList(),
                        onChanged: (v) => setState(() => _moneda = v!),
                      ),
                    ),
                  ],
                ),
                if (_requiereTasa) ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: _tasaCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: const TextStyle(color: AppColors.textPrimary),
                    decoration: InputDecoration(
                      labelText: _moneda == 'ves' ? 'Tasa USD → VES' : 'Tasa USD → COP',
                      prefixIcon: const Icon(Icons.currency_exchange_rounded),
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _metodoPago,
                  decoration: const InputDecoration(
                    labelText: 'Método de pago de salida',
                    prefixIcon: Icon(Icons.payment_rounded),
                  ),
                  dropdownColor: AppColors.bgElevated,
                  items: FinanzasService.metodosPago
                      .map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2)))
                      .toList(),
                  onChanged: (v) => setState(() => _metodoPago = v),
                ),
                if (_requiereProveedor) ...[
                  const SizedBox(height: 12),
                  if (_cargandoProveedores)
                    const LinearProgressIndicator()
                  else if (!_mostrarNuevoProveedor)
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _proveedorId,
                            decoration: const InputDecoration(
                              labelText: 'Proveedor',
                              prefixIcon: Icon(Icons.store_rounded),
                            ),
                            dropdownColor: AppColors.bgElevated,
                            items: _proveedores
                                .map((p) => DropdownMenuItem(value: p.id, child: Text(p.nombre)))
                                .toList(),
                            onChanged: (v) => setState(() => _proveedorId = v),
                          ),
                        ),
                        IconButton(
                          onPressed: () => setState(() => _mostrarNuevoProveedor = true),
                          icon: const Icon(Icons.add_business_rounded),
                          tooltip: 'Nuevo proveedor',
                        ),
                      ],
                    )
                  else
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _nuevoProveedorCtrl,
                            style: const TextStyle(color: AppColors.textPrimary),
                            decoration: const InputDecoration(
                              labelText: 'Nombre del proveedor',
                              prefixIcon: Icon(Icons.store_rounded),
                            ),
                          ),
                        ),
                        IconButton(onPressed: _crearProveedorRapido, icon: const Icon(Icons.check_rounded)),
                        IconButton(
                          onPressed: () => setState(() => _mostrarNuevoProveedor = false),
                          icon: const Icon(Icons.close_rounded),
                        ),
                      ],
                    ),
                ],
                const SizedBox(height: 12),
                TextField(
                  controller: _descCtrl,
                  maxLines: 2,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Descripción',
                    prefixIcon: Icon(Icons.notes_rounded),
                    hintText: 'Ej: Factura repuestos moto ruta norte',
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: _elegirComprobante,
                  icon: const Icon(Icons.photo_camera_rounded),
                  label: Text(_comprobanteNombre ?? 'Adjuntar comprobante (opcional)'),
                ),
                if (_comprobanteNombre != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle_rounded, color: AppColors.emerald, size: 18),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            _comprobanteNombre!,
                            style: const TextStyle(fontSize: 12, color: AppColors.emerald),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        TextButton(
                          onPressed: () => setState(() {
                            _comprobanteBase64 = null;
                            _comprobanteNombre = null;
                          }),
                          child: const Text('Quitar'),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TipoChip extends StatelessWidget {
  const _TipoChip({
    required this.label,
    required this.icon,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: selected ? color.withValues(alpha: 0.15) : AppColors.bgElevated,
            border: Border.all(color: selected ? color : AppColors.glassBorder, width: selected ? 1.5 : 1),
          ),
          child: Column(
            children: [
              Icon(icon, color: selected ? color : AppColors.textMuted),
              const SizedBox(height: 6),
              Text(label, style: TextStyle(fontWeight: FontWeight.w700, color: selected ? color : AppColors.textMuted)),
            ],
          ),
        ),
      ),
    );
  }
}
