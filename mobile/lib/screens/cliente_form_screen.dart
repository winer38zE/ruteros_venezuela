import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/clientes_service.dart';
import '../services/rutas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/score_badge.dart';
import '../widgets/gps_location_capture.dart';

class ClienteFormScreen extends StatefulWidget {
  const ClienteFormScreen({super.key, this.cliente});

  final ClienteDetalle? cliente;

  bool get esEdicion => cliente != null;

  @override
  State<ClienteFormScreen> createState() => _ClienteFormScreenState();
}

class _ClienteFormScreenState extends State<ClienteFormScreen> {
  final _nombreCtrl = TextEditingController();
  final _identCtrl = TextEditingController();
  final _telCtrl = TextEditingController();
  final _tel2Ctrl = TextEditingController();
  final _dirCtrl = TextEditingController();
  final _refDirCtrl = TextEditingController();
  final _empresaCtrl = TextEditingController();
  final _dirLabCtrl = TextEditingController();
  final _refNombreCtrl = TextEditingController();
  final _refTelCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _ordenCtrl = TextEditingController();

  String _tipoCliente = 'detal';
  String _diaRuta = RutasService.etiquetaDiaActual();
  String? _parentesco;
  bool _guardando = false;
  bool _verificando = false;
  String? _buroMsg;
  int? _scorePreview;
  double? _latRes;
  double? _lngRes;
  double? _latTrab;
  double? _lngTrab;

  @override
  void initState() {
    super.initState();
    final c = widget.cliente;
    if (c != null) {
      _nombreCtrl.text = c.nombre;
      _identCtrl.text = c.identificacion;
      _telCtrl.text = c.telefono ?? '';
      _tel2Ctrl.text = c.telefonoSecundario ?? '';
      _dirCtrl.text = c.direccion ?? '';
      _refDirCtrl.text = c.puntoReferencia ?? '';
      _empresaCtrl.text = c.empresaTrabajo ?? '';
      _dirLabCtrl.text = c.direccionLaboral ?? '';
      _refNombreCtrl.text = c.refFamiliarNombre ?? '';
      _parentesco = c.refFamiliarParentesco;
      _refTelCtrl.text = c.refFamiliarTelefono ?? '';
      _emailCtrl.text = c.email ?? '';
      _tipoCliente = c.tipoCliente;
      final diaGuardado = c.diaRuta;
      if (diaGuardado != null && diaGuardado.isNotEmpty) {
        final etiqueta = RutasService.etiquetaDia(diaGuardado);
        if (RutasService.diasEtiqueta.contains(etiqueta)) {
          _diaRuta = etiqueta;
        }
      }
      _scorePreview = c.scoreCredito;
      _latRes = c.latitudResidencia;
      _lngRes = c.longitudResidencia;
      _latTrab = c.latitudTrabajo;
      _lngTrab = c.longitudTrabajo;
      if (c.ordenRuta != null) _ordenCtrl.text = '${c.ordenRuta}';
    } else {
      _parentesco = ClientesService.parentescos.first;
    }
  }

  @override
  void dispose() {
    for (final c in [
      _nombreCtrl, _identCtrl, _telCtrl, _tel2Ctrl, _dirCtrl, _refDirCtrl,
      _empresaCtrl, _dirLabCtrl, _refNombreCtrl, _refTelCtrl, _emailCtrl, _ordenCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _verificarIdentificacion() async {
    if (_identCtrl.text.trim().length < 5) return;
    setState(() {
      _verificando = true;
      _buroMsg = null;
    });
    try {
      final auto = await context.read<AppState>().clientes.verificarIdentificacion(_identCtrl.text.trim());
      if (auto.enRed) {
        if (auto.nombreCompleto != null) _nombreCtrl.text = auto.nombreCompleto!;
        if (auto.telefono != null) _telCtrl.text = auto.telefono!;
        if (auto.telefonoSecundario != null) _tel2Ctrl.text = auto.telefonoSecundario!;
        if (auto.direccion != null) _dirCtrl.text = auto.direccion!;
        if (auto.puntoReferencia != null) _refDirCtrl.text = auto.puntoReferencia!;
        if (auto.empresaTrabajo != null) _empresaCtrl.text = auto.empresaTrabajo!;
        if (auto.direccionLaboral != null) _dirLabCtrl.text = auto.direccionLaboral!;
        if (auto.refFamiliarNombre != null) _refNombreCtrl.text = auto.refFamiliarNombre!;
        if (auto.refFamiliarParentesco != null) _parentesco = auto.refFamiliarParentesco;
        if (auto.refFamiliarTelefono != null) _refTelCtrl.text = auto.refFamiliarTelefono!;
        if (auto.email != null) _emailCtrl.text = auto.email!;
        _scorePreview = auto.scoreGlobal;
        _buroMsg = 'Cliente verificado en la red Ruteros · ${auto.estadoCredito ?? ""}';
      } else {
        _buroMsg = 'Identificación nueva en la red — score inicial 70';
        _scorePreview = 70;
      }
    } catch (e) {
      _buroMsg = '$e';
    } finally {
      if (mounted) setState(() => _verificando = false);
    }
  }

  Map<String, dynamic> _body() => {
        'nombre_completo': _nombreCtrl.text.trim(),
        'identificacion': _identCtrl.text.trim(),
        'telefono': _telCtrl.text.trim(),
        'telefono_secundario': _tel2Ctrl.text.trim().isEmpty ? null : _tel2Ctrl.text.trim(),
        'direccion': _dirCtrl.text.trim().isEmpty ? null : _dirCtrl.text.trim(),
        'punto_referencia': _refDirCtrl.text.trim().isEmpty ? null : _refDirCtrl.text.trim(),
        'latitud_residencia': _latRes,
        'longitud_residencia': _lngRes,
        'empresa_trabajo': _empresaCtrl.text.trim().isEmpty ? null : _empresaCtrl.text.trim(),
        'direccion_laboral': _dirLabCtrl.text.trim().isEmpty ? null : _dirLabCtrl.text.trim(),
        'latitud_trabajo': _latTrab,
        'longitud_trabajo': _lngTrab,
        'ref_familiar_nombre': _refNombreCtrl.text.trim().isEmpty ? null : _refNombreCtrl.text.trim(),
        'ref_familiar_parentesco': _parentesco,
        'ref_familiar_telefono': _refTelCtrl.text.trim().isEmpty ? null : _refTelCtrl.text.trim(),
        'email': _emailCtrl.text.trim().isEmpty ? null : _emailCtrl.text.trim(),
        'tipo_cliente': _tipoCliente,
        'dia_ruta': _diaRuta,
        if (_ordenIngresado() != null) 'orden_ruta': _ordenIngresado(),
      };

  int? _ordenIngresado() {
    final n = int.tryParse(_ordenCtrl.text.trim());
    if (n == null || n < 1) return null;
    return n;
  }

  Future<void> _guardar() async {
    if (_nombreCtrl.text.trim().isEmpty || _identCtrl.text.trim().length < 5) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nombre e identificación (mín. 5 caracteres) son obligatorios')),
      );
      return;
    }
    if (_telCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El teléfono es obligatorio')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      final svc = context.read<AppState>().clientes;
      if (widget.esEdicion) {
        await svc.actualizar(widget.cliente!.id, _body());
      } else {
        await svc.crear(_body());
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
    return FuturisticScaffold(
      title: widget.esEdicion ? 'Editar Cliente' : 'Nuevo Cliente',
      accentColor: AppColors.neonCyan,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.save_rounded),
            label: Text(_guardando ? 'Guardando…' : 'Guardar cliente'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: AppColors.neonCyan,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_scorePreview != null)
            Center(
              child: ScoreBadge(
                score: _scorePreview!,
                estado: widget.cliente?.estadoCredito ?? 'Verificado',
              ),
            ),
          if (_buroMsg != null) ...[
            const SizedBox(height: 8),
            Text(_buroMsg!, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
          ],
          const SizedBox(height: 16),
          const SectionTitle(title: 'Datos personales'),
          GlassContainer(
            accentColor: AppColors.neonCyan,
            child: Column(
              children: [
                TextField(
                  controller: _nombreCtrl,
                  decoration: const InputDecoration(labelText: 'Nombre completo', prefixIcon: Icon(Icons.badge_rounded)),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _identCtrl,
                        enabled: !widget.esEdicion,
                        decoration: const InputDecoration(
                          labelText: 'CC / Cédula / DNI',
                          prefixIcon: Icon(Icons.credit_card_rounded),
                        ),
                        onSubmitted: (_) => _verificarIdentificacion(),
                      ),
                    ),
                    IconButton(
                      onPressed: _verificando ? null : _verificarIdentificacion,
                      icon: _verificando
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.verified_user_rounded),
                      tooltip: 'Verificar en buró',
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _telCtrl,
                  enabled: true,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Teléfono *',
                    hintText: 'Obligatorio',
                    prefixIcon: Icon(Icons.phone_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _tel2Ctrl,
                  enabled: true,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Teléfono secundario',
                    prefixIcon: Icon(Icons.phone_android_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _emailCtrl,
                  enabled: true,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Correo Electrónico',
                    hintText: 'Para recibos digitales',
                    prefixIcon: Icon(Icons.email_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _tipoCliente,
                  decoration: const InputDecoration(labelText: 'Tipo de cliente'),
                  dropdownColor: AppColors.bgElevated,
                  items: const [
                    DropdownMenuItem(value: 'detal', child: Text('Detal')),
                    DropdownMenuItem(value: 'mayorista', child: Text('Mayorista')),
                  ],
                  onChanged: (v) => setState(() => _tipoCliente = v!),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const SectionTitle(title: 'Ruta semanal'),
          GlassContainer(
            accentColor: AppColors.neonCyan,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  value: _diaRuta,
                  decoration: const InputDecoration(
                    labelText: 'Día de ruta',
                    prefixIcon: Icon(Icons.calendar_today_rounded),
                  ),
                  dropdownColor: AppColors.bgElevated,
                  items: RutasService.diasEtiqueta
                      .map((d) => DropdownMenuItem(value: d, child: Text(d)))
                      .toList(),
                  onChanged: (v) {
                    if (v != null) setState(() => _diaRuta = v);
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _ordenCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Orden de visita',
                    hintText: '1, 2, 3…',
                    prefixIcon: Icon(Icons.format_list_numbered_rounded),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Cambiar el día o la parada conserva el historial de crédito, compras y pagos.',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const SectionTitle(title: 'Ubicación y trabajo'),
          GlassContainer(
            accentColor: AppColors.neonBlue,
            child: Column(
              children: [
                TextField(
                  controller: _dirCtrl,
                  enabled: true,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Dirección de Domicilio',
                    prefixIcon: Icon(Icons.home_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                GpsLocationCapture(
                  etiqueta: 'Domicilio',
                  latitud: _latRes,
                  longitud: _lngRes,
                  color: AppColors.neonBlue,
                  onCoordsChanged: (c) => setState(() {
                    _latRes = c.latitud;
                    _lngRes = c.longitud;
                  }),
                ),
                const SizedBox(height: 12),
                TextField(controller: _refDirCtrl, decoration: const InputDecoration(labelText: 'Punto de referencia', prefixIcon: Icon(Icons.place_rounded))),
                const SizedBox(height: 12),
                TextField(controller: _empresaCtrl, decoration: const InputDecoration(labelText: 'Empresa / Trabajo actual', prefixIcon: Icon(Icons.business_rounded))),
                const SizedBox(height: 12),
                TextField(
                  controller: _dirLabCtrl,
                  enabled: true,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Dirección de Trabajo',
                    prefixIcon: Icon(Icons.location_city_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                GpsLocationCapture(
                  etiqueta: 'Trabajo',
                  latitud: _latTrab,
                  longitud: _lngTrab,
                  color: AppColors.amber,
                  onCoordsChanged: (c) => setState(() {
                    _latTrab = c.latitud;
                    _lngTrab = c.longitud;
                  }),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const SectionTitle(title: 'Referencia familiar / personal'),
          GlassContainer(
            accentColor: AppColors.violet,
            child: Column(
              children: [
                TextField(controller: _refNombreCtrl, decoration: const InputDecoration(labelText: 'Nombre completo', prefixIcon: Icon(Icons.person_outline_rounded))),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _parentesco,
                  decoration: const InputDecoration(labelText: 'Parentesco'),
                  dropdownColor: AppColors.bgElevated,
                  items: ClientesService.parentescos.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                  onChanged: (v) => setState(() => _parentesco = v),
                ),
                const SizedBox(height: 12),
                TextField(controller: _refTelCtrl, decoration: const InputDecoration(labelText: 'Teléfono de contacto', prefixIcon: Icon(Icons.contact_phone_rounded))),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
