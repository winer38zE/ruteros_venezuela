import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../l10n/regional_copy.dart';
import '../providers/app_state.dart';
import '../services/ventas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/enviar_recibo_button.dart';
import 'nueva_venta_screen.dart';

class VentasListScreen extends StatefulWidget {
  const VentasListScreen({super.key});

  @override
  State<VentasListScreen> createState() => _VentasListScreenState();
}

class _VentasListScreenState extends State<VentasListScreen> {
  List<Venta> _ventas = [];
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _busqueda = TextEditingController();

  @override
  void dispose() {
    _busqueda.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  String _etiquetaVenta(Venta venta) {
    final tipo = venta.frecuenciaPago == 'contado' ? 'Contado' : 'Crédito';
    final metodo = venta.metodoPago == 'pago_movil'
        ? 'Pago móvil'
        : venta.metodoPago == 'transferencia'
            ? 'Transferencia'
            : 'Efectivo';
    return '$tipo · $metodo';
  }

  Future<void> _verificar(Venta venta) async {
    try {
      await context.read<AppState>().ventas.verificarPago(venta.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pago confirmado. La venta quedó Pagada.')),
      );
      await _cargar();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
      );
    }
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      _ventas = await context.read<AppState>().ventas.misVentas(q: _busqueda.text);
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _nuevaVenta() async {
    final ok = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const NuevaVentaScreen()),
    );
    if (ok == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final copy = RegionalCopy.fromEsVenezuela(context.watch<AppState>().esVenezuela);
    return FuturisticScaffold(
      title: 'Mis Ventas',
      accentColor: AppColors.emerald,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: NeonFab(
        label: 'Nueva Venta',
        icon: Icons.add_shopping_cart_rounded,
        color: AppColors.emerald,
        onPressed: _nuevaVenta,
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : _ventas.isEmpty
                  ? EmptyState(
                      icon: Icons.point_of_sale_rounded,
                      message: copy.emptyVentasTitulo,
                      detail: copy.emptyVentasDetalle,
                      actionLabel: 'Registrar venta',
                      onAction: _nuevaVenta,
                    )
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        children: [
                          SectionTitle(
                            title: 'Historial de ventas',
                            trailing: Text(
                              '${_ventas.length} registros',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                          TextField(
                            controller: _busqueda,
                            decoration: InputDecoration(
                              hintText: 'Buscar por nombre del cliente',
                              prefixIcon: const Icon(Icons.search_rounded),
                              suffixIcon: IconButton(
                                icon: const Icon(Icons.arrow_forward_rounded),
                                onPressed: _cargar,
                              ),
                            ),
                            onSubmitted: (_) => _cargar(),
                          ),
                          const SizedBox(height: 12),
                          ..._ventas.map((v) {
                            final fecha = (v.fecha != null && v.fecha!.length >= 10)
                                ? v.fecha!.substring(0, 10)
                                : 'sin fecha';
                            final telefono = (v.clienteTelefono ?? '').trim();
                            return GlassListTile(
                              accentColor: AppColors.emerald,
                              leading: Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: AppColors.emerald.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppColors.emerald.withValues(alpha: 0.35)),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  '${v.detalles.length}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.emerald,
                                  ),
                                ),
                              ),
                              title: Text(v.clienteCompleto),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(telefono.isEmpty ? 'Sin teléfono' : telefono),
                                  const SizedBox(height: 4),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 4,
                                    crossAxisAlignment: WrapCrossAlignment.center,
                                    children: [
                                      StatusBadge.estado(v.estado),
                                      Text(_etiquetaVenta(v)),
                                      Text(fecha),
                                      Text(_fmt.format(v.totalUsd)),
                                      Text('Saldo ${_fmt.format(v.saldoPendienteUsd)}'),
                                    ],
                                  ),
                                  if (v.productosResumen.isNotEmpty && v.productosResumen != '—')
                                    Text(v.productosResumen),
                                ],
                              ),
                              children: [
                                if (v.detalles.isEmpty)
                                  const Padding(
                                    padding: EdgeInsets.all(12),
                                    child: Text('Venta sin detalle de productos'),
                                  )
                                else
                                  ...v.detalles.map(
                                    (d) => Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            '${d.productoNombre ?? 'Producto'} · ${d.cantidad} uds × \$${d.precioUnitarioUsd}',
                                          ),
                                          Text(
                                            _fmt.format(d.subtotal),
                                            style: const TextStyle(fontWeight: FontWeight.w600),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                if ((v.referenciaPago ?? '').isNotEmpty)
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
                                    child: Text('Referencia: ${v.referenciaPago}'),
                                  ),
                                if (v.tieneComprobante)
                                  const Padding(
                                    padding: EdgeInsets.fromLTRB(14, 4, 14, 0),
                                    child: Text('Comprobante de transferencia adjunto'),
                                  ),
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      EnviarReciboButton(
                                        email: v.clienteEmail,
                                        telefono: v.clienteTelefono,
                                        onEnviar: () => context.read<AppState>().ventas.enviarRecibo(v.id),
                                        onWhatsapp: (v.clienteEmail ?? '').contains('@')
                                            ? null
                                            : () => context.read<AppState>().ventas.enviarReciboWhatsapp(v.id),
                                      ),
                                      if (v.estado == 'por_verificar' &&
                                          context.watch<AppState>().puedeOperaciones) ...[
                                        const SizedBox(height: 8),
                                        FilledButton.icon(
                                          onPressed: () => _verificar(v),
                                          icon: const Icon(Icons.verified_rounded),
                                          label: const Text('Confirmar pago'),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            );
                          }),
                        ],
                      ),
                    ),
    );
  }
}
