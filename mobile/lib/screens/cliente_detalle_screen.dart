import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/app_state.dart';
import '../services/clientes_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/gps_location_capture.dart';
import '../widgets/asistente_ruta_widget.dart';
import '../widgets/score_badge.dart';
import 'cliente_form_screen.dart';

class ClienteDetalleScreen extends StatefulWidget {
  const ClienteDetalleScreen({super.key, required this.clienteId});

  final String clienteId;

  @override
  State<ClienteDetalleScreen> createState() => _ClienteDetalleScreenState();
}

class _ClienteDetalleScreenState extends State<ClienteDetalleScreen> {
  ClienteDetalle? _cliente;
  BuroCreditoResult? _buro;
  bool _cargando = true;
  String? _error;

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
      final svc = context.read<AppState>().clientes;
      final c = await svc.obtener(widget.clienteId);
      final buro = await svc.consultarBuro(c.identificacion);
      _cliente = c;
      _buro = buro;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _llamar(String? telefono) async {
    if (telefono == null || telefono.isEmpty) return;
    final uri = Uri.parse('tel:$telefono');
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  Future<void> _whatsapp(String? telefono) async {
    if (telefono == null || telefono.isEmpty) return;
    final digits = telefono.replaceAll(RegExp(r'\D'), '');
    final uri = Uri.parse('https://wa.me/$digits');
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Ficha del Cliente',
      accentColor: AppColors.neonCyan,
      actions: [
        if (_cliente != null)
          IconButton(
            icon: const Icon(Icons.edit_rounded),
            onPressed: () async {
              final ok = await Navigator.push<bool>(
                context,
                MaterialPageRoute(builder: (_) => ClienteFormScreen(cliente: _cliente)),
              );
              if (ok == true) _cargar();
            },
          ),
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : _cliente == null
                  ? const EmptyState(icon: Icons.person_off_rounded, message: 'Cliente no encontrado')
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        GlassContainer(
                          accentColor: scoreColor(_cliente!),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(_cliente!.nombre, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20)),
                                    Text('ID: ${_cliente!.identificacion}'),
                                    Text('Tipo: ${_cliente!.tipoCliente}'),
                                  ],
                                ),
                              ),
                              ScoreBadge(score: _cliente!.scoreCredito, estado: _cliente!.estadoCredito),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () => _llamar(_cliente!.telefono),
                                icon: const Icon(Icons.call_rounded),
                                label: const Text('Llamar'),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: FilledButton.icon(
                                onPressed: () => _whatsapp(_cliente!.telefono),
                                icon: const Icon(Icons.chat_rounded),
                                label: const Text('WhatsApp'),
                                style: FilledButton.styleFrom(backgroundColor: AppColors.emerald, foregroundColor: AppColors.bgDeep),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        AsistenteRutaWidget(
                          latResidencia: _cliente!.latitudResidencia,
                          lngResidencia: _cliente!.longitudResidencia,
                          latTrabajo: _cliente!.latitudTrabajo,
                          lngTrabajo: _cliente!.longitudTrabajo,
                        ),
                        const SizedBox(height: 10),
                        BotonesRutaCliente(
                          latResidencia: _cliente!.latitudResidencia,
                          lngResidencia: _cliente!.longitudResidencia,
                          latTrabajo: _cliente!.latitudTrabajo,
                          lngTrabajo: _cliente!.longitudTrabajo,
                          direccionResidencia: _cliente!.direccion,
                          direccionTrabajo: _cliente!.direccionLaboral,
                          clienteId: _cliente!.id,
                          destacados: true,
                        ),
                        const SizedBox(height: 16),
                        const SectionTitle(title: 'Datos de contacto'),
                        _InfoTile('Teléfono', _cliente!.telefono),
                        _InfoTile('Tel. secundario', _cliente!.telefonoSecundario),
                        _InfoTile('Email', _cliente!.email),
                        _InfoTile('Dirección', _cliente!.direccion),
                        _InfoTile('Referencia', _cliente!.puntoReferencia),
                        _InfoTile('Trabajo', _cliente!.empresaTrabajo),
                        _InfoTile('Dir. laboral', _cliente!.direccionLaboral),
                        const SizedBox(height: 16),
                        const SectionTitle(title: 'Referencia personal'),
                        GlassContainer(
                          accentColor: AppColors.violet,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(_cliente!.refFamiliarNombre ?? '—', style: const TextStyle(fontWeight: FontWeight.w700)),
                              Text('${_cliente!.refFamiliarParentesco ?? ""} · ${_cliente!.refFamiliarTelefono ?? ""}'),
                              const SizedBox(height: 10),
                              Row(
                                children: [
                                  TextButton.icon(
                                    onPressed: () => _llamar(_cliente!.refFamiliarTelefono),
                                    icon: const Icon(Icons.call_rounded, size: 18),
                                    label: const Text('Llamar ref.'),
                                  ),
                                  TextButton.icon(
                                    onPressed: () => _whatsapp(_cliente!.refFamiliarTelefono),
                                    icon: const Icon(Icons.chat_rounded, size: 18),
                                    label: const Text('WhatsApp ref.'),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        if (_buro != null && _buro!.historial.isNotEmpty) ...[
                          const SizedBox(height: 16),
                          const SectionTitle(title: 'Buró de crédito (red Ruteros)'),
                          ..._buro!.historial.map(
                            (h) => GlassListTile(
                              accentColor: AppColors.amber,
                              leading: const Icon(Icons.history_rounded, color: AppColors.amber),
                              title: Text(h.mensaje),
                              subtitle: Text(h.fecha.substring(0, 10)),
                            ),
                          ),
                        ],
                        if (_cliente!.bloqueadoCredito)
                          Padding(
                            padding: const EdgeInsets.only(top: 16),
                            child: GlassContainer(
                              accentColor: const Color(0xFFEF4444),
                              child: const Text(
                                'Crédito bloqueado: solo ventas de contado permitidas.',
                                style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w700),
                              ),
                            ),
                          ),
                      ],
                    ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  const _InfoTile(this.label, this.value);
  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    if (value == null || value!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 110, child: Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 13))),
          Expanded(child: Text(value!, style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}
