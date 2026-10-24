import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/inventario_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import 'ajuste_inventario_screen.dart';
import '../utils/producto_precios_region.dart';
import 'producto_form_screen.dart';

class InventarioScreen extends StatefulWidget {
  const InventarioScreen({super.key});

  @override
  State<InventarioScreen> createState() => _InventarioScreenState();
}

class _InventarioScreenState extends State<InventarioScreen> {
  List<ProductoInventario> _items = [];
  List<InventarioValoradoItem> _valorado = [];
  bool _cargando = true;
  String? _error;
  String _busqueda = '';
  String? _categoriaFiltro;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _limpiarFiltros() {
    _searchCtrl.clear();
    _busqueda = '';
    _categoriaFiltro = null;
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final svc = context.read<AppState>().inventario;
      _items = await svc.listarProductosConStock();
      try {
        _valorado = await svc.inventarioValorado();
      } catch (_) {
        _valorado = [];
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  List<String> get _categorias {
    final cats = _items
        .map((i) => i.producto.categoria)
        .whereType<String>()
        .where((c) => c.isNotEmpty)
        .toSet()
        .toList()
      ..sort();
    return cats;
  }

  List<ProductoInventario> get _filtrados {
    final q = _busqueda.trim().toLowerCase();
    return _items.where((item) {
      final p = item.producto;
      if (_categoriaFiltro != null && p.categoria != _categoriaFiltro) return false;
      if (q.isEmpty) return true;
      return p.nombre.toLowerCase().contains(q) ||
          (p.sku?.toLowerCase().contains(q) ?? false) ||
          (p.categoria?.toLowerCase().contains(q) ?? false);
    }).toList();
  }

  Future<void> _abrirFormulario([ProductoInventario? item]) async {
    final esNuevo = item == null;
    final ok = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => ProductoFormScreen(producto: item?.producto),
      ),
    );
    if (ok == true && mounted) {
      if (esNuevo) _limpiarFiltros();
      await _cargar();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(esNuevo ? 'Producto guardado con éxito' : 'Producto actualizado'),
          backgroundColor: AppColors.emerald,
        ),
      );
    }
  }

  Future<void> _abrirAjuste(ProductoInventario item) async {
    final ok = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => AjusteInventarioScreen(producto: item)),
    );
    if (ok == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final esDueno = state.puedeOperaciones;
    final preciosCfg = ProductoPreciosRegionConfig.from(
      state.region ?? state.usuario?.pais,
      esVenezuela: state.esVenezuela,
    );
    final totalValor = _valorado.fold<double>(0, (s, i) => s + i.valorTotalUsd);
    final bajoStock = _items.where((i) => i.bajoStock).length;
    final filtrados = _filtrados;

    return FuturisticScaffold(
      title: 'Gestión de Inventario',
      accentColor: AppColors.violet,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: esDueno
          ? NeonFab(
              label: 'Nuevo producto',
              icon: Icons.add_rounded,
              color: AppColors.violet,
              onPressed: () => _abrirFormulario(),
            )
          : null,
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  color: AppColors.violet,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      GlassContainer(
                        accentColor: AppColors.violet,
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Valor inventario', style: Theme.of(context).textTheme.bodySmall),
                                  Text(
                                    _fmt.format(totalValor),
                                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: AppColors.violet),
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text('${_items.length} productos', style: Theme.of(context).textTheme.bodySmall),
                                if (bajoStock > 0)
                                  Text(
                                    '$bajoStock bajo stock',
                                    style: const TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w700, fontSize: 12),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _searchCtrl,
                        onChanged: (v) => setState(() => _busqueda = v),
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: InputDecoration(
                          hintText: 'Buscar por nombre, SKU o categoría…',
                          prefixIcon: const Icon(Icons.search_rounded),
                          suffixIcon: _busqueda.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear_rounded),
                                  onPressed: () {
                                    _searchCtrl.clear();
                                    setState(() => _busqueda = '');
                                  },
                                )
                              : null,
                        ),
                      ),
                      if (_categorias.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        SizedBox(
                          height: 38,
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              Padding(
                                padding: const EdgeInsets.only(right: 8),
                                child: FilterChip(
                                  label: const Text('Todas'),
                                  selected: _categoriaFiltro == null,
                                  onSelected: (_) => setState(() => _categoriaFiltro = null),
                                ),
                              ),
                              ..._categorias.map(
                                (c) => Padding(
                                  padding: const EdgeInsets.only(right: 8),
                                  child: FilterChip(
                                    label: Text(c),
                                    selected: _categoriaFiltro == c,
                                    onSelected: (_) => setState(() => _categoriaFiltro = c),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      const SectionTitle(title: 'Productos'),
                      if (_items.isEmpty)
                        EmptyState(
                          icon: Icons.inventory_2_outlined,
                          message: esDueno
                              ? 'Aún no hay productos. Toca + para crear el primero.'
                              : 'No hay productos en tu inventario.',
                        )
                      else if (filtrados.isEmpty)
                        EmptyState(
                          icon: Icons.search_off_rounded,
                          message: 'Ningún producto coincide con tu búsqueda o filtro.',
                          actionLabel: 'Limpiar filtros',
                          onAction: () => setState(_limpiarFiltros),
                        )
                      else
                        ...filtrados.map((item) {
                          final p = item.producto;
                          final color = item.bajoStock ? const Color(0xFFEF4444) : AppColors.emerald;
                          return GlassListTile(
                            accentColor: color,
                            onTap: esDueno ? () => _abrirFormulario(item) : null,
                            leading: Icon(
                              item.bajoStock ? Icons.warning_amber_rounded : Icons.inventory_2_rounded,
                              color: color,
                            ),
                            title: Text(p.nombre),
                            subtitle: Text(
                              [
                                if (p.sku != null && p.sku!.isNotEmpty) 'SKU: ${p.sku}',
                                if (p.categoria != null && p.categoria!.isNotEmpty) p.categoria,
                                'Precio: ${preciosCfg.resumenLista(precioUsd: p.precioUsd, precioVes: p.precioVes, precioCop: p.precioCop, fmt: (n) => _fmt.format(n))}',
                              ].join(' · '),
                            ),
                            trailing: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                StatusBadge(label: '${item.stockTotal} uds', color: color),
                                if (esDueno)
                                  TextButton(
                                    onPressed: () => _abrirAjuste(item),
                                    child: const Text('Ajustar', style: TextStyle(fontSize: 11)),
                                  ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }
}
