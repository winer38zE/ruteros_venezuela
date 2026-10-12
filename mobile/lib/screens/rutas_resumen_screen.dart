import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/rutas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class RutasResumenScreen extends StatefulWidget {
  const RutasResumenScreen({super.key});

  @override
  State<RutasResumenScreen> createState() => _RutasResumenScreenState();
}

class _RutasResumenScreenState extends State<RutasResumenScreen> {
  RutasResumenResult? _resumen;
  bool _cargando = true;
  bool _enviando = false;
  String? _error;
  String _dia = RutasService.diaActual();

  static const _diasLabel = {
    'LUNES': 'Lunes', 'MARTES': 'Martes', 'MIERCOLES': 'Miércoles',
    'JUEVES': 'Jueves', 'VIERNES': 'Viernes', 'SABADO': 'Sábado', 'DOMINGO': 'Domingo',
  };

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
      _resumen = await context.read<AppState>().rutas.resumen(
            fecha: RutasService.fechaActual(),
            dia: _dia,
          );
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _enviarWhatsapp() async {
    final telefono = await showDialog<String>(
      context: context,
      builder: (ctx) => const _DialogoWhatsapp(),
    );
    if (telefono == null || telefono.trim().isEmpty || !mounted) return;

    setState(() => _enviando = true);
    try {
      final mensaje = await context.read<AppState>().rutas.enviarResumenWhatsapp(
            telefono: telefono.trim(),
            dia: _dia,
            fecha: RutasService.fechaActual(),
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(mensaje)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
      );
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Resumen de Rutas',
      accentColor: AppColors.violet,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator(color: AppColors.violet))
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error!, textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        FilledButton(onPressed: _cargar, child: const Text('Reintentar')),
                      ],
                    ),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _cargar,
                  color: AppColors.violet,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      GlassContainer(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${_diasLabel[_resumen!.dia] ?? _resumen!.dia} · ${_resumen!.fecha}',
                              style: const TextStyle(
                                color: AppColors.textPrimary,
                                fontWeight: FontWeight.w700,
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${_resumen!.vendedores.length} cobradores/vendedores con ruta activa',
                              style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: FilledButton.icon(
                                onPressed: _enviando ? null : _enviarWhatsapp,
                                icon: _enviando
                                    ? const SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                      )
                                    : const Icon(Icons.chat_rounded),
                                label: Text(_enviando ? 'Enviando…' : 'Enviar reporte por WhatsApp'),
                                style: FilledButton.styleFrom(
                                  backgroundColor: const Color(0xFF25D366),
                                  foregroundColor: Colors.white,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (_resumen!.vendedores.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(32),
                          child: Center(
                            child: Text(
                              'No hay rutas configuradas para este día',
                              style: TextStyle(color: AppColors.textMuted),
                            ),
                          ),
                        )
                      else
                        ..._resumen!.vendedores.map(_buildTarjetaVendedor),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTarjetaVendedor(ResumenVendedorRuta v) {
    final pct = v.porcentajeAvance;
    Color barColor;
    if (pct >= 80) {
      barColor = AppColors.emerald;
    } else if (pct >= 40) {
      barColor = AppColors.amber;
    } else {
      barColor = AppColors.neonCyan;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassContainer(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.violet.withValues(alpha: 0.2),
                  child: Text(
                    v.vendedorNombre.isNotEmpty ? v.vendedorNombre[0].toUpperCase() : '?',
                    style: const TextStyle(color: AppColors.violet, fontWeight: FontWeight.w800),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        v.vendedorNombre,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        '${v.visitados}/${v.totalClientes} visitados',
                        style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Text(
                  '${pct.toStringAsFixed(0)}%',
                  style: TextStyle(color: barColor, fontWeight: FontWeight.w800, fontSize: 18),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: v.totalClientes > 0 ? v.visitados / v.totalClientes : 0,
                minHeight: 8,
                backgroundColor: AppColors.glassBorder,
                color: barColor,
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                _chipStat('Pendientes', v.pendientes, AppColors.neonCyan),
                const SizedBox(width: 8),
                _chipStat('Visitados', v.visitados, AppColors.emerald),
                if (v.noEncontrados > 0) ...[
                  const SizedBox(width: 8),
                  _chipStat('No enc.', v.noEncontrados, Colors.orange),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _chipStat(String label, int valor, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(
        '$label: $valor',
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _DialogoWhatsapp extends StatefulWidget {
  const _DialogoWhatsapp();

  @override
  State<_DialogoWhatsapp> createState() => _DialogoWhatsappState();
}

class _DialogoWhatsappState extends State<_DialogoWhatsapp> {
  final _telefonoCtrl = TextEditingController();

  @override
  void dispose() {
    _telefonoCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Enviar reporte por WhatsApp'),
      content: TextField(
        controller: _telefonoCtrl,
        keyboardType: TextInputType.phone,
        autofocus: true,
        decoration: const InputDecoration(
          labelText: 'Teléfono del dueño o cliente',
          hintText: '58412XXXXXXX',
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton(
          onPressed: () {
            final tel = _telefonoCtrl.text.trim();
            if (tel.length < 8) return;
            Navigator.pop(context, tel);
          },
          child: const Text('Enviar'),
        ),
      ],
    );
  }
}
