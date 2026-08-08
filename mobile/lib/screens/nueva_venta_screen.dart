import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../providers/app_state.dart';
import '../services/catalogo_service.dart';
import '../services/ventas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/score_badge.dart';

class NuevaVentaScreen extends StatefulWidget {
  const NuevaVentaScreen({super.key});

  @override
  State<NuevaVentaScreen> createState() => _NuevaVentaScreenState();
}

class _NuevaVentaScreenState extends State<NuevaVentaScreen> {
  List<Cliente> _clientes = [];
  List<Producto> _productos = [];
  List<Almacen> _almacenes = [];
  TasaCambio? _tasa;

  Cliente? _cliente;
  Almacen? _almacen;
  String _frecuencia = 'semanal';
  String _tipoTasa = 'bcv';
  int _numeroCuotas = 12;
  final List<ItemCarrito> _carrito = [];

  bool _cargando = true;
  bool _guardando = false;
  String? _error;

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _frecuencias = ['contado', 'semanal', 'quincenal', 'mensual'];

  @override
  void initState() {
    super.initState();
    _cargarDatos();
  }

  Future<void> _cargarDatos() async {
    final cat = context.read<AppState>().catalogo;
    try {
      final results = await Future.wait([
        cat.listarClientes(),
        cat.listarProductos(),
        cat.listarAlmacenes(),
        cat.ultimaTasa(),
      ]);
      _clientes = results[0] as List<Cliente>;
      _productos = results[1] as List<Producto>;
      _almacenes = results[2] as List<Almacen>;
      _tasa = results[3] as TasaCambio;
      _cliente = _clientes.isNotEmpty ? _clientes.first : null;
      _almacen = _almacenes.where((a) => a.esPrincipal).firstOrNull ??
          (_almacenes.isNotEmpty ? _almacenes.first : null);
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  double get _total => _carrito.fold(0.0, (s, i) => s + i.subtotal);

  Future<double> _precioParaProducto(Producto p) async {
    final tipo = _cliente?.tipoCliente ?? 'detal';
    try {
      final precios = await context.read<AppState>().catalogo.preciosProducto(p.id);
      final match = precios.where((pr) => pr.tipoCliente == tipo);
      if (match.isNotEmpty) return match.first.precioUsd;
    } catch (_) {}
    return p.precioUsd;
  }

  Future<void> _agregarProducto(Producto p) async {
    final precio = await _precioParaProducto(p);
    final tipo = _cliente?.tipoCliente ?? 'detal';
    final existente = _carrito.indexWhere((i) => i.productoId == p.id);
    setState(() {
      if (existente >= 0) {
        final item = _carrito[existente];
        _carrito[existente] = ItemCarrito(
          productoId: item.productoId,
          nombre: item.nombre,
          cantidad: item.cantidad + 1,
          precioUnitario: item.precioUnitario,
          tipoPrecio: item.tipoPrecio,
        );
      } else {
        _carrito.add(ItemCarrito(
          productoId: p.id,
          nombre: p.nombre,
          cantidad: 1,
          precioUnitario: precio,
          tipoPrecio: tipo,
        ));
      }
    });
  }

  Future<void> _registrarVenta({bool borrador = false}) async {
    if (_cliente == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona un cliente')),
      );
      return;
    }
    if (_frecuencia != 'contado' && _cliente!.bloqueadoCredito) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Crédito Rechazado: Cliente reportado con alto riesgo crediticio. Solo ventas de contado.',
          ),
          backgroundColor: Color(0xFFEF4444),
        ),
      );
      return;
    }
    if (_carrito.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Agrega al menos un producto')),
      );
      return;
    }
    if (_tasa == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No hay tasa de cambio registrada')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      final venta = await context.read<AppState>().ventas.crearVenta(
            clienteId: _cliente!.id,
            totalUsd: _total,
            tasaUsd: _tasa!.usdBs,
            tasaEur: _tasa!.eurBs,
            frecuenciaPago: _frecuencia,
            items: _carrito,
            almacenId: _almacen?.id,
            ventaId: const Uuid().v4(),
            numeroCuotas: _frecuencia == 'contado' ? null : _numeroCuotas,
            tipoTasaUsd: _tipoTasa,
            esBorrador: borrador,
          );
      if (!mounted) return;
      final msg = borrador
          ? 'Borrador guardado (${venta.estado})'
          : 'Venta registrada: ${_fmt.format(_total)}';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      if (!borrador && venta.cuotas.isNotEmpty) {
        await showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: AppColors.bgCard,
            title: const Text('Plan de amortización'),
            content: SizedBox(
              width: double.maxFinite,
              child: ListView(
                shrinkWrap: true,
                children: venta.cuotas
                    .map((c) => ListTile(
                          dense: true,
                          title: Text('Cuota ${c.numeroCuota}'),
                          subtitle: Text(c.fechaVencimiento.substring(0, 10)),
                          trailing: Text('\$${c.montoUsd.toStringAsFixed(2)}'),
                        ))
                    .toList(),
              ),
            ),
            actions: [
              FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
            ],
          ),
        );
      }
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

  InputDecoration _input(String label, {IconData? icon}) => InputDecoration(
        labelText: label,
        prefixIcon: icon != null ? Icon(icon) : null,
      );

  @override
  Widget build(BuildContext context) {
    if (_cargando) {
      return const FuturisticScaffold(
        title: 'Nueva Venta',
        accentColor: AppColors.emerald,
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return FuturisticScaffold(
        title: 'Nueva Venta',
        accentColor: AppColors.emerald,
        body: Center(child: Text(_error!)),
      );
    }

    return FuturisticScaffold(
      title: 'Nueva Venta — Campo',
      accentColor: AppColors.emerald,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (context.watch<AppState>().esVendedor)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OutlinedButton.icon(
                    onPressed: _guardando ? null : () => _registrarVenta(borrador: true),
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('Guardar borrador'),
                  ),
                ),
              FilledButton.icon(
                onPressed: _guardando ? null : () => _registrarVenta(),
                icon: _guardando
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.check_circle_rounded),
                label: Text(
                  _guardando ? 'Registrando...' : 'Registrar Venta ${_fmt.format(_total)}',
                  style: const TextStyle(fontSize: 16),
                ),
                style: FilledButton.styleFrom(
                  minimumSize: const Size(double.infinity, 52),
                  backgroundColor: AppColors.emerald,
                  foregroundColor: AppColors.bgDeep,
                ),
              ),
            ],
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          GlassContainer(
            accentColor: AppColors.emerald,
            child: Column(
              children: [
                DropdownButtonFormField<Cliente>(
                  value: _cliente,
                  decoration: _input('Cliente', icon: Icons.person_outline),
                  dropdownColor: AppColors.bgElevated,
                  items: _clientes
                      .map((c) => DropdownMenuItem(
                            value: c,
                            child: Text('${c.nombre} · Score ${c.scoreCredito}'),
                          ))
                      .toList(),
                  onChanged: (c) => setState(() {
                    _cliente = c;
                    if (c != null && c.bloqueadoCredito && _frecuencia != 'contado') {
                      _frecuencia = 'contado';
                    }
                  }),
                ),
                if (_cliente != null) ...[
                  const SizedBox(height: 8),
                  ScoreBadge(
                    score: _cliente!.scoreCredito,
                    estado: _cliente!.bloqueadoCredito ? 'Malo / Moroso' : 'Score activo',
                    compact: true,
                  ),
                ],
                const SizedBox(height: 12),
                if (_almacenes.isNotEmpty)
                  DropdownButtonFormField<Almacen>(
                    value: _almacen,
                    decoration: _input('Almacén', icon: Icons.warehouse_outlined),
                    dropdownColor: AppColors.bgElevated,
                    items: _almacenes.map((a) => DropdownMenuItem(value: a, child: Text(a.nombre))).toList(),
                    onChanged: (a) => setState(() => _almacen = a),
                  ),
                if (_almacenes.isNotEmpty) const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _frecuencia,
                        decoration: _input('Frecuencia pago'),
                        dropdownColor: AppColors.bgElevated,
                        items: _frecuencias
                            .where((f) => f == 'contado' || !(_cliente?.bloqueadoCredito ?? false))
                            .map((f) => DropdownMenuItem(value: f, child: Text(f)))
                            .toList(),
                        onChanged: (f) => setState(() => _frecuencia = f!),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: InputDecorator(
                        decoration: _input('Tasa USD/Bs', icon: Icons.trending_up),
                        child: Text(_tasa != null ? '${_tasa!.usdBs}' : '—'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _tipoTasa,
                        decoration: _input('Tasa activa'),
                        dropdownColor: AppColors.bgElevated,
                        items: const [
                          DropdownMenuItem(value: 'bcv', child: Text('BCV')),
                          DropdownMenuItem(value: 'paralelo', child: Text('Paralelo')),
                        ],
                        onChanged: (v) => setState(() => _tipoTasa = v ?? 'bcv'),
                      ),
                    ),
                    if (_frecuencia != 'contado') ...[
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextFormField(
                          initialValue: '$_numeroCuotas',
                          keyboardType: TextInputType.number,
                          decoration: _input('N° cuotas'),
                          onChanged: (v) => _numeroCuotas = int.tryParse(v) ?? _numeroCuotas,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          SectionTitle(
            title: 'Carrito',
            trailing: Text('${_carrito.length} productos', style: Theme.of(context).textTheme.bodySmall),
          ),
          if (_carrito.isEmpty)
            GlassContainer(
              accentColor: AppColors.neonBlue,
              child: const Text('Agrega productos desde la lista de abajo'),
            )
          else
            ..._carrito.asMap().entries.map((entry) {
              final i = entry.key;
              final item = entry.value;
              return GlassListTile(
                accentColor: AppColors.emerald,
                title: Text(item.nombre),
                subtitle: Text('${item.tipoPrecio} · \$${item.precioUnitario}/ud'),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.remove_circle_outline, color: AppColors.textMuted),
                      onPressed: () {
                        setState(() {
                          if (item.cantidad > 1) {
                            _carrito[i] = ItemCarrito(
                              productoId: item.productoId,
                              nombre: item.nombre,
                              cantidad: item.cantidad - 1,
                              precioUnitario: item.precioUnitario,
                              tipoPrecio: item.tipoPrecio,
                            );
                          } else {
                            _carrito.removeAt(i);
                          }
                        });
                      },
                    ),
                    Text('${item.cantidad}', style: const TextStyle(fontWeight: FontWeight.w800)),
                    IconButton(
                      icon: const Icon(Icons.add_circle_outline, color: AppColors.emerald),
                      onPressed: () {
                        setState(() {
                          _carrito[i] = ItemCarrito(
                            productoId: item.productoId,
                            nombre: item.nombre,
                            cantidad: item.cantidad + 1,
                            precioUnitario: item.precioUnitario,
                            tipoPrecio: item.tipoPrecio,
                          );
                        });
                      },
                    ),
                  ],
                ),
              );
            }),
          const SizedBox(height: 20),
          const SectionTitle(title: 'Productos disponibles'),
          ..._productos.map(
            (p) => GlassListTile(
              accentColor: AppColors.neonBlue,
              title: Text(p.nombre),
              subtitle: Text('Stock: ${p.stock} · Base: \$${p.precioUsd}'),
              trailing: IconButton(
                icon: const Icon(Icons.add_shopping_cart_rounded, color: AppColors.emerald),
                onPressed: () => _agregarProducto(p),
              ),
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}
