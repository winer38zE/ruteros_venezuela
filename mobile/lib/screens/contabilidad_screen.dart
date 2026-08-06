import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/contabilidad_service.dart';
import '../theme/app_theme.dart';
import '../widgets/glass_container.dart';

class ContabilidadScreen extends StatefulWidget {
  const ContabilidadScreen({super.key});

  @override
  State<ContabilidadScreen> createState() => _ContabilidadScreenState();
}

class _ContabilidadScreenState extends State<ContabilidadScreen> {
  ResumenContable? _resumen;
  ExportacionExcelInfo? _info;
  bool _cargando = true;
  bool _exportando = false;
  String? _error;

  DateTime? _fechaDesde;
  DateTime? _fechaHasta;

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _fechaFmt = DateFormat('dd/MM/yyyy');

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
      final svc = context.read<AppState>().contabilidad;
      final results = await Future.wait([
        svc.obtenerResumen(),
        svc.infoExportacion(fechaDesde: _fechaDesde, fechaHasta: _fechaHasta),
      ]);
      _resumen = results[0] as ResumenContable;
      _info = results[1] as ExportacionExcelInfo;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _actualizarPreview() async {
    try {
      final info = await context.read<AppState>().contabilidad.infoExportacion(
            fechaDesde: _fechaDesde,
            fechaHasta: _fechaHasta,
          );
      if (mounted) setState(() => _info = info);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al filtrar: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _elegirFecha({required bool esDesde}) async {
    final inicial = esDesde
        ? (_fechaDesde ?? DateTime.now())
        : (_fechaHasta ?? _fechaDesde ?? DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: inicial,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked == null) return;

    setState(() {
      if (esDesde) {
        _fechaDesde = picked;
        if (_fechaHasta != null && picked.isAfter(_fechaHasta!)) {
          _fechaHasta = picked;
        }
      } else {
        _fechaHasta = picked;
        if (_fechaDesde != null && picked.isBefore(_fechaDesde!)) {
          _fechaDesde = picked;
        }
      }
    });
    await _actualizarPreview();
  }

  void _limpiarFechas() {
    setState(() {
      _fechaDesde = null;
      _fechaHasta = null;
    });
    _actualizarPreview();
  }

  Future<void> _exportarExcel() async {
    setState(() => _exportando = true);
    try {
      final bytes = await context.read<AppState>().contabilidad.descargarExcel(
            fechaDesde: _fechaDesde,
            fechaHasta: _fechaHasta,
          );
      final dir = await getApplicationDocumentsDirectory();
      final suffix = _fechaDesde != null || _fechaHasta != null ? '_filtrado' : '';
      final name = 'EDNETPRO_${DateTime.now().millisecondsSinceEpoch}$suffix.xlsx';
      final file = File('${dir.path}/$name');
      await file.writeAsBytes(bytes);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Excel guardado: $name')),
      );

      await OpenFilex.open(file.path);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al exportar: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _exportando = false);
    }
  }

  String get _rangoLabel {
    if (_fechaDesde == null && _fechaHasta == null) return 'Todo el historial';
    if (_fechaDesde != null && _fechaHasta != null) {
      return '${_fechaFmt.format(_fechaDesde!)} — ${_fechaFmt.format(_fechaHasta!)}';
    }
    if (_fechaDesde != null) return 'Desde ${_fechaFmt.format(_fechaDesde!)}';
    return 'Hasta ${_fechaFmt.format(_fechaHasta!)}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Contabilidad'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
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
                      _FiltroFechasCard(
                        rangoLabel: _rangoLabel,
                        fechaDesde: _fechaDesde,
                        fechaHasta: _fechaHasta,
                        fechaFmt: _fechaFmt,
                        onElegirDesde: () => _elegirFecha(esDesde: true),
                        onElegirHasta: () => _elegirFecha(esDesde: false),
                        onLimpiar: _limpiarFechas,
                      ),
                      const SizedBox(height: 16),
                      if (_info != null) _InfoCard(info: _info!, fmt: _fmt),
                      const SizedBox(height: 16),
                      if (_resumen != null) _ResumenCard(resumen: _resumen!, fmt: _fmt),
                      const SizedBox(height: 24),
                      FilledButton.icon(
                        onPressed: _exportando ? null : _exportarExcel,
                        icon: _exportando
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.download),
                        label: Text(
                          _exportando ? 'Generando Excel...' : 'Exportar Excel para Contador',
                          style: const TextStyle(fontSize: 16),
                        ),
                        style: FilledButton.styleFrom(
                          minimumSize: const Size(double.infinity, 52),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Incluye: ${(_info?.hojas ?? []).join(' · ')}\nPeríodo: $_rangoLabel',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
    );
  }
}

class _FiltroFechasCard extends StatelessWidget {
  const _FiltroFechasCard({
    required this.rangoLabel,
    required this.fechaDesde,
    required this.fechaHasta,
    required this.fechaFmt,
    required this.onElegirDesde,
    required this.onElegirHasta,
    required this.onLimpiar,
  });

  final String rangoLabel;
  final DateTime? fechaDesde;
  final DateTime? fechaHasta;
  final DateFormat fechaFmt;
  final VoidCallback onElegirDesde;
  final VoidCallback onElegirHasta;
  final VoidCallback onLimpiar;

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      accentColor: AppColors.neonBlue,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Período del reporte Excel',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(rangoLabel, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onElegirDesde,
                  icon: const Icon(Icons.calendar_today, size: 18),
                  label: Text(
                    fechaDesde != null ? fechaFmt.format(fechaDesde!) : 'Desde',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onElegirHasta,
                  icon: const Icon(Icons.event, size: 18),
                  label: Text(
                    fechaHasta != null ? fechaFmt.format(fechaHasta!) : 'Hasta',
                  ),
                ),
              ),
            ],
          ),
          if (fechaDesde != null || fechaHasta != null)
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: onLimpiar,
                child: const Text('Quitar filtros'),
              ),
            ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.info, required this.fmt});
  final ExportacionExcelInfo info;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      accentColor: AppColors.neonCyan,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(info.empresa, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          Text('País: ${info.pais}${info.rif != null ? ' · RIF: ${info.rif}' : ''}'),
          const Divider(),
          _row('Ventas en período', '${info.totalVentas}'),
          _row('Cobros en período', '${info.totalCobros}'),
          _row('Asientos contables', '${info.totalAsientos}'),
          _row('Valor inventario', fmt.format(info.valorInventarioUsd)),
        ],
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [Text(label), Text(value, style: const TextStyle(fontWeight: FontWeight.w600))],
        ),
      );
}

class _ResumenCard extends StatelessWidget {
  const _ResumenCard({required this.resumen, required this.fmt});
  final ResumenContable resumen;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      accentColor: AppColors.violet,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Resumen Contable (global)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 12),
          _row('Ventas (USD)', fmt.format(resumen.totalVentasUsd)),
          _row('Cobrado (USD)', fmt.format(resumen.totalCobradoUsd)),
          _row('Por cobrar (USD)', fmt.format(resumen.cuentasPorCobrarUsd)),
          _row('IVA estimado (USD)', fmt.format(resumen.ivaEstimadoUsd)),
          _row('Asientos generados', '${resumen.asientosGenerados}'),
        ],
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [Text(label), Text(value, style: const TextStyle(fontWeight: FontWeight.w500))],
        ),
      );
}
