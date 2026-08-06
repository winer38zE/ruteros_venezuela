import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/inventario_service.dart';

class InventarioScreen extends StatefulWidget {
  const InventarioScreen({super.key});

  @override
  State<InventarioScreen> createState() => _InventarioScreenState();
}

class _InventarioScreenState extends State<InventarioScreen> {
  List<StockProducto> _stock = [];
  List<InventarioValoradoItem> _valorado = [];
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final svc = context.read<AppState>().inventario;
      final results = await Future.wait([
        svc.listarStock(),
        svc.inventarioValorado(),
      ]);
      _stock = results[0] as List<StockProducto>;
      _valorado = results[1] as List<InventarioValoradoItem>;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalValor = _valorado.fold<double>(0, (s, i) => s + i.valorTotalUsd);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventario'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar)],
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Card(
                        color: const Color(0xFFD6E4F0),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Valor total inventario',
                                  style: TextStyle(fontWeight: FontWeight.bold)),
                              Text(_fmt.format(totalValor),
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const Text('Stock por producto',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 8),
                      ..._stock.map(
                        (s) => Card(
                          child: ListTile(
                            title: Text(s.productoNombre),
                            trailing: Chip(
                              label: Text('${s.stockTotalGlobal} uds'),
                              backgroundColor: s.stockTotalGlobal > 0
                                  ? Colors.green.shade100
                                  : Colors.red.shade100,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const Text('Inventario valorado',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 8),
                      ..._valorado.map(
                        (v) => Card(
                          child: ListTile(
                            title: Text(v.nombre),
                            subtitle: Text('Stock: ${v.stockTotal} uds'),
                            trailing: Text(_fmt.format(v.valorTotalUsd)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}
