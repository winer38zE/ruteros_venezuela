import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/admin_catalog_service.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_background.dart';
import '../widgets/glass_container.dart';

class AdminPaisesReglasScreen extends StatefulWidget {
  const AdminPaisesReglasScreen({super.key});

  @override
  State<AdminPaisesReglasScreen> createState() => _AdminPaisesReglasScreenState();
}

class _AdminPaisesReglasScreenState extends State<AdminPaisesReglasScreen> {
  final _year = 2026;
  List<CountryAdmin> _paises = [];
  List<PayrollRuleAdmin> _reglas = [];
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<AdminCatalogService> _svc() async {
    final api = context.read<AppState>().api;
    return AdminCatalogService(api);
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final svc = await _svc();
      final paises = await svc.listarPaises();
      final reglas = await svc.listarReglas(year: _year);
      if (!mounted) return;
      setState(() {
        _paises = paises;
        _reglas = reglas;
        _cargando = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _cargando = false;
      });
    }
  }

  Future<void> _duplicarAnio() async {
    final svc = await _svc();
    try {
      await svc.duplicarReglasAnio(desdeYear: _year, haciaYear: _year + 1);
      if (!mounted) return;
      final next = _year + 1;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Borrador $next creado desde $_year')),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  String _nombrePais(String paisId) {
    for (final p in _paises) {
      if (p.id == paisId) return p.nombre;
    }
    return paisId;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Países y reglas 2026'),
        backgroundColor: Colors.transparent,
      ),
      body: FuturisticBackground(
        child: SafeArea(
          child: _cargando
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(child: Text(_error!, style: const TextStyle(color: Colors.white70)))
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          GlassContainer(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Catálogo de países',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                ..._paises.map(
                                  (p) => ListTile(
                                    dense: true,
                                    title: Text(
                                      '${p.bandera ?? ''} ${p.nombre} (${p.codigoIso})',
                                      style: const TextStyle(color: Colors.white),
                                    ),
                                    subtitle: Text(
                                      'Monedas pago: ${p.paymentCurrencies.join(', ')}',
                                      style: const TextStyle(color: Colors.white54),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  'Reglas de sueldo $_year',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                              ),
                              TextButton(
                                onPressed: _duplicarAnio,
                                child: Text('Duplicar a ${_year + 1}'),
                              ),
                            ],
                          ),
                          ..._reglas.map((r) {
                            final sinVerificar = !r.verified;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: GlassContainer(
                                child: ListTile(
                                  title: Text(
                                    '${_nombrePais(r.paisId)} · ${r.monedaSalario}',
                                    style: const TextStyle(color: Colors.white),
                                  ),
                                  subtitle: Text(
                                    'Mínimo: ${r.salarioMinimo} ${r.monedaSalario}'
                                    '${r.borrador ? ' · borrador' : ''}'
                                    '${sinVerificar ? '\n⚠ Regla sin verificar' : ''}',
                                    style: TextStyle(
                                      color: sinVerificar ? AppColors.amber : Colors.white54,
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
        ),
      ),
    );
  }
}
