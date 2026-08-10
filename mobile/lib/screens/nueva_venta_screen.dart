import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../providers/app_state.dart';
import '../services/catalogo_service.dart';
import '../services/tasas_service.dart';
import '../services/ventas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/score_badge.dart';
import '../widgets/gps_location_capture.dart';

class NuevaVentaScreen extends StatefulWidget {
  const NuevaVentaScreen({super.key});

  @override
  State<NuevaVentaScreen> createState() => _NuevaVentaScreenState();
}

class _NuevaVentaScreenState extends State<NuevaVentaScreen> {
  List<Cliente> _clientes = [];
  List<Producto> _productos = [];
  List<Almacen> _almacenes = [];
  TasaCambioDetalle? _tasa;

  Cliente? _cliente;
  Producto? _productoSel;
  Almacen? _almacen;
  bool _usarClienteExistente = true;
  bool _esCredito = true;
  String _frecuencia = 'semanal';
  String _tipoTasa = 'bcv';
  bool _usarMontoManual = false;
  final List<ItemCarrito> _carrito = [];

  final _nombreCtrl = TextEditingController();
  final _cedulaCtrl = TextEditingController();
  final _telCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _dirCtrl = TextEditingController();
  final _dirLabCtrl = TextEditingController();
  final _cantidadCtrl = TextEditingController(text: '1');
  final _montoManualCtrl = TextEditingController();
  final _cuotasCtrl = TextEditingController(text: '12');
  double? _latRes;
  double? _lngRes;
  double? _latTrab;
  double? _lngTrab;

  bool _cargando = true;
  bool _guardando = false;
  String? _error;

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _frecuenciasCredito = ['semanal', 'quincenal', 'mensual'];

  @override
  void initState() {
    super.initState();
    _cargarDatos();
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _cedulaCtrl.dispose();
    _telCtrl.dispose();
    _emailCtrl.dispose();
    _dirCtrl.dispose();
    _dirLabCtrl.dispose();
    _cantidadCtrl.dispose();
    _montoManualCtrl.dispose();
    _cuotasCtrl.dispose();
    super.dispose();
  }

  Future<TasaCambioDetalle?> _cargarTasa(AppState state) async {
    try {
      return await state.tasas.ultima();
    } catch (_) {
      return null;
    }
  }

  Future<void> _cargarDatos() async {
    final state = context.read<AppState>();
    try {
      final results = await Future.wait([
        state.catalogo.listarClientes(),
        state.catalogo.listarProductos(),
        state.catalogo.listarAlmacenes(),
        _cargarTasa(state),
      ]);
      _clientes = results[0] as List<Cliente>;
      _productos = results[1] as List<Producto>;
      _almacenes = results[2] as List<Almacen>;
      _tasa = results[3] as TasaCambioDetalle?;
      _cliente = _clientes.isNotEmpty ? _clientes.first : null;
      _usarClienteExistente = _clientes.isNotEmpty;
      _productoSel = _productos.isNotEmpty ? _productos.first : null;
      _almacen = _almacenes.where((a) => a.esPrincipal).firstOrNull ??
          (_almacenes.isNotEmpty ? _almacenes.first : null);
      if (_cliente != null) {
        _llenarDatosCliente(
          nombre: _cliente!.nombre,
          identificacion: _cliente!.identificacion,
        );
      }
      _montoManualCtrl.text = '0.00';
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  double get _totalCarrito => _carrito.fold(0.0, (s, i) => s + i.subtotal);

  double get _total {
    if (_usarMontoManual) {
      return double.tryParse(_montoManualCtrl.text.replaceAll(',', '.')) ?? 0;
    }
    return _totalCarrito;
  }

  double get _tasaUsdAplicada {
    if (_tasa == null) return 0;
    return _tipoTasa == 'paralelo' ? _tasa!.usdParaleloBs : _tasa!.usdBcvBs;
  }

  int get _numeroCuotas => int.tryParse(_cuotasCtrl.text) ?? 12;

  void _llenarDatosCliente({
    required String nombre,
    required String identificacion,
    String? telefono,
    String? email,
    String? direccion,
    String? direccionLaboral,
    double? latRes,
    double? lngRes,
    double? latTrab,
    double? lngTrab,
  }) {
    _nombreCtrl.text = nombre;
    _cedulaCtrl.text = identificacion;
    _telCtrl.text = telefono ?? '';
    _emailCtrl.text = email ?? '';
    _dirCtrl.text = direccion ?? '';
    _dirLabCtrl.text = direccionLaboral ?? '';
    _latRes = latRes;
    _lngRes = lngRes;
    _latTrab = latTrab;
    _lngTrab = lngTrab;
  }

  Future<void> _onClienteExistenteChanged(Cliente? c) async {
    setState(() {
      _cliente = c;
      if (c != null) {
        _llenarDatosCliente(nombre: c.nombre, identificacion: c.identificacion);
        if (c.bloqueadoCredito) _esCredito = false;
      }
    });
    if (c == null) return;
    try {
      final detalle = await context.read<AppState>().clientes.obtener(c.id);
      if (!mounted) return;
      setState(() {
        _llenarDatosCliente(
          nombre: detalle.nombre,
          identificacion: detalle.identificacion,
          telefono: detalle.telefono,
          email: detalle.email,
          direccion: detalle.direccion,
          direccionLaboral: detalle.direccionLaboral,
          latRes: detalle.latitudResidencia,
          lngRes: detalle.longitudResidencia,
          latTrab: detalle.latitudTrabajo,
          lngTrab: detalle.longitudTrabajo,
        );
      });
    } catch (_) {}
  }

  Future<double> _precioParaProducto(Producto p) async {
    final tipo = _cliente?.tipoCliente ?? 'detal';
    try {
      final precios = await context.read<AppState>().catalogo.preciosProducto(p.id);
      final match = precios.where((pr) => pr.tipoCliente == tipo);
      if (match.isNotEmpty) return match.first.precioUsd;
    } catch (_) {}
    return p.precioUsd;
  }

  Future<void> _agregarProductoAlCarrito() async {
    final p = _productoSel;
    if (p == null) return;
    final cantidad = int.tryParse(_cantidadCtrl.text) ?? 1;
    if (cantidad <= 0) return;
    final precio = await _precioParaProducto(p);
    final tipo = _cliente?.tipoCliente ?? 'detal';
    final existente = _carrito.indexWhere((i) => i.productoId == p.id);
    setState(() {
      if (existente >= 0) {
        final item = _carrito[existente];
        _carrito[existente] = ItemCarrito(
          productoId: item.productoId,
          nombre: item.nombre,
          cantidad: item.cantidad + cantidad,
          precioUnitario: item.precioUnitario,
          tipoPrecio: item.tipoPrecio,
        );
      } else {
        _carrito.add(ItemCarrito(
          productoId: p.id,
          nombre: p.nombre,
          cantidad: cantidad,
          precioUnitario: precio,
          tipoPrecio: tipo,
        ));
      }
      _usarMontoManual = false;
      _montoManualCtrl.text = _totalCarrito.toStringAsFixed(2);
    });
  }

  Future<String> _resolverClienteId() async {
    if (_usarClienteExistente && _cliente != null) return _cliente!.id;

    final nombre = _nombreCtrl.text.trim();
    final cedula = _cedulaCtrl.text.trim();
    final telefono = _telCtrl.text.trim();
    if (nombre.isEmpty || cedula.length < 5) {
      throw Exception('Ingresa nombre y cédula/DNI del cliente (mín. 5 caracteres)');
    }
    if (telefono.isEmpty) {
      throw Exception('El teléfono del cliente es obligatorio');
    }

    final existente = _clientes.where((c) => c.identificacion == cedula).firstOrNull;
    if (existente != null) return existente.id;

    final creado = await context.read<AppState>().clientes.crear({
      'nombre_completo': nombre,
      'identificacion': cedula,
      'telefono': telefono,
      if (_emailCtrl.text.trim().isNotEmpty) 'email': _emailCtrl.text.trim(),
      if (_dirCtrl.text.trim().isNotEmpty) 'direccion': _dirCtrl.text.trim(),
      if (_dirLabCtrl.text.trim().isNotEmpty) 'direccion_laboral': _dirLabCtrl.text.trim(),
      if (_latRes != null) 'latitud_residencia': _latRes,
      if (_lngRes != null) 'longitud_residencia': _lngRes,
      if (_latTrab != null) 'latitud_trabajo': _latTrab,
      if (_lngTrab != null) 'longitud_trabajo': _lngTrab,
    });
    return creado.id;
  }

  Future<void> _registrarVenta({bool borrador = false}) async {
    if (_esCredito && (_cliente?.bloqueadoCredito ?? false)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Crédito rechazado: cliente con alto riesgo. Solo ventas de contado.'),
          backgroundColor: Color(0xFFEF4444),
        ),
      );
      return;
    }
    if (_total <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un monto total o agrega productos al carrito')),
      );
      return;
    }
    if (!_usarClienteExistente && _telCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El teléfono del cliente es obligatorio')),
      );
      return;
    }
    if (!_usarMontoManual && _carrito.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Agrega al menos un producto o activa monto manual')),
      );
      return;
    }
    if (_tasa == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No hay tasa de cambio registrada. Registra tasas primero.')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      final clienteId = await _resolverClienteId();
      final frecuencia = _esCredito ? _frecuencia : 'contado';
      final items = _carrito.isNotEmpty
          ? _carrito
          : [
              if (_productoSel != null)
                ItemCarrito(
                  productoId: _productoSel!.id,
                  nombre: _productoSel!.nombre,
                  cantidad: int.tryParse(_cantidadCtrl.text) ?? 1,
                  precioUnitario: _total / (int.tryParse(_cantidadCtrl.text) ?? 1),
                  tipoPrecio: _cliente?.tipoCliente ?? 'detal',
                ),
            ];

      final venta = await context.read<AppState>().ventas.crearVenta(
            clienteId: clienteId,
            totalUsd: _total,
            tasaUsd: _tasaUsdAplicada,
            tasaEur: _tasa!.eurBs,
            frecuenciaPago: frecuencia,
            items: items,
            almacenId: _almacen?.id,
            ventaId: const Uuid().v4(),
            numeroCuotas: _esCredito ? _numeroCuotas : null,
            tipoTasaUsd: _tipoTasa,
            esBorrador: borrador,
            latitudResidencia: _latRes,
            longitudResidencia: _lngRes,
            latitudTrabajo: _latTrab,
            longitudTrabajo: _lngTrab,
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
                          title: Text('${c.etiquetaPeriodo} · ${c.estadoDisplay}'),
                          subtitle: Text(
                            '${c.fechaVencimiento.substring(0, 10)} · '
                            'Pendiente: \$${c.montoPendienteUsd.toStringAsFixed(2)}',
                          ),
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

  InputDecoration _input(String label, {IconData? icon, String? helper}) => InputDecoration(
        labelText: label,
        prefixIcon: icon != null ? Icon(icon) : null,
        helperText: helper,
        filled: true,
        fillColor: AppColors.bgElevated.withValues(alpha: 0.5),
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
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_error!, style: const TextStyle(color: Colors.orange)),
            ),
          GlassContainer(
            accentColor: AppColors.emerald,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tipo de venta', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                SegmentedButton<bool>(
                  segments: const [
                    ButtonSegment(value: false, label: Text('Contado'), icon: Icon(Icons.payments_outlined)),
                    ButtonSegment(value: true, label: Text('Crédito'), icon: Icon(Icons.credit_score_outlined)),
                  ],
                  selected: {_esCredito},
                  onSelectionChanged: (s) {
                    setState(() {
                      _esCredito = s.first;
                      if (!_esCredito) _frecuencia = 'contado';
                    });
                  },
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _usarClienteExistente ? 'Cliente registrado' : 'Cliente nuevo',
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    Switch(
                      value: _usarClienteExistente,
                      onChanged: (v) => setState(() => _usarClienteExistente = v),
                    ),
                  ],
                ),
                if (_usarClienteExistente && _clientes.isNotEmpty)
                  DropdownButtonFormField<Cliente>(
                    value: _cliente,
                    decoration: _input('Seleccionar cliente', icon: Icons.person_outline),
                    dropdownColor: AppColors.bgElevated,
                    items: _clientes
                        .map((c) => DropdownMenuItem(
                              value: c,
                              child: Text('${c.nombre} · ${c.identificacion}'),
                            ))
                        .toList(),
                    onChanged: _onClienteExistenteChanged,
                  ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _nombreCtrl,
                  enabled: true,
                  readOnly: false,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Nombre del cliente', icon: Icons.badge_outlined),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _cedulaCtrl,
                  enabled: true,
                  readOnly: false,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Cédula / DNI', icon: Icons.fingerprint),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _telCtrl,
                  enabled: true,
                  keyboardType: TextInputType.phone,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Teléfono *', icon: Icons.phone_rounded, helper: 'Obligatorio'),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _emailCtrl,
                  enabled: true,
                  keyboardType: TextInputType.emailAddress,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Correo Electrónico', icon: Icons.email_rounded, helper: 'Para recibos digitales'),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _dirCtrl,
                  enabled: true,
                  maxLines: 2,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Dirección de Domicilio', icon: Icons.home_outlined),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _dirLabCtrl,
                  enabled: true,
                  maxLines: 2,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _input('Dirección de Trabajo', icon: Icons.business_outlined),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                GpsLocationCapture(
                  etiqueta: 'Domicilio del cliente',
                  latitud: _latRes,
                  longitud: _lngRes,
                  color: AppColors.emerald,
                  onCoordsChanged: (c) => setState(() {
                    _latRes = c.latitud;
                    _lngRes = c.longitud;
                  }),
                ),
                const SizedBox(height: 8),
                GpsLocationCapture(
                  etiqueta: 'Trabajo del cliente',
                  latitud: _latTrab,
                  longitud: _lngTrab,
                  color: AppColors.amber,
                  onCoordsChanged: (c) => setState(() {
                    _latTrab = c.latitud;
                    _lngTrab = c.longitud;
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
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassContainer(
            accentColor: AppColors.neonBlue,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Producto y monto', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 12),
                if (_productos.isNotEmpty)
                  DropdownButtonFormField<Producto>(
                    value: _productoSel,
                    decoration: _input('Producto', icon: Icons.inventory_2_outlined),
                    dropdownColor: AppColors.bgElevated,
                    items: _productos
                        .map((p) => DropdownMenuItem(
                              value: p,
                              child: Text('${p.nombre} · \$${p.precioUsd}'),
                            ))
                        .toList(),
                    onChanged: (p) => setState(() => _productoSel = p),
                  ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _cantidadCtrl,
                        enabled: true,
                        keyboardType: TextInputType.number,
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: _input('Cantidad', icon: Icons.numbers),
                      ),
                    ),
                    const SizedBox(width: 12),
                    FilledButton.icon(
                      onPressed: _agregarProductoAlCarrito,
                      icon: const Icon(Icons.add_shopping_cart),
                      label: const Text('Agregar'),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.neonBlue,
                        foregroundColor: AppColors.bgDeep,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Monto total manual',
                        style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                      ),
                    ),
                    Switch(
                      value: _usarMontoManual,
                      onChanged: (v) => setState(() => _usarMontoManual = v),
                    ),
                  ],
                ),
                TextFormField(
                  controller: _montoManualCtrl,
                  enabled: _usarMontoManual,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w700),
                  decoration: _input(
                    'Monto total (USD)',
                    icon: Icons.attach_money,
                    helper: _usarMontoManual ? 'Ingresa el total de la venta manualmente' : 'Calculado del carrito: ${_fmt.format(_totalCarrito)}',
                  ),
                  onChanged: (_) => setState(() {}),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassContainer(
            accentColor: AppColors.amber,
            child: Column(
              children: [
                if (_esCredito) ...[
                  DropdownButtonFormField<String>(
                    value: _frecuencia,
                    decoration: _input('Frecuencia de pago'),
                    dropdownColor: AppColors.bgElevated,
                    items: _frecuenciasCredito
                        .map((f) => DropdownMenuItem(
                              value: f,
                              child: Text(f[0].toUpperCase() + f.substring(1)),
                            ))
                        .toList(),
                    onChanged: (f) => setState(() => _frecuencia = f ?? 'semanal'),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _cuotasCtrl,
                    enabled: true,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: AppColors.textPrimary),
                    decoration: _input('N° de cuotas', icon: Icons.calendar_month_outlined),
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: 12),
                ],
                if (_almacenes.isNotEmpty) ...[
                  DropdownButtonFormField<Almacen>(
                    value: _almacen,
                    decoration: _input('Almacén', icon: Icons.warehouse_outlined),
                    dropdownColor: AppColors.bgElevated,
                    items: _almacenes.map((a) => DropdownMenuItem(value: a, child: Text(a.nombre))).toList(),
                    onChanged: (a) => setState(() => _almacen = a),
                  ),
                  const SizedBox(height: 12),
                ],
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
                    const SizedBox(width: 12),
                    Expanded(
                      child: InputDecorator(
                        decoration: _input('Tasa USD/Bs', icon: Icons.trending_up),
                        child: Text(
                          _tasa != null ? _tasaUsdAplicada.toStringAsFixed(2) : '—',
                          style: const TextStyle(
                            color: AppColors.emerald,
                            fontWeight: FontWeight.w700,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ),
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
              child: const Text('Agrega productos con el botón de arriba o usa monto manual'),
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
                          _montoManualCtrl.text = _totalCarrito.toStringAsFixed(2);
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
                          _montoManualCtrl.text = _totalCarrito.toStringAsFixed(2);
                        });
                      },
                    ),
                  ],
                ),
              );
            }),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}
