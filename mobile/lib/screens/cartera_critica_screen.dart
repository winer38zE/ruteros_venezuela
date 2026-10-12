import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../providers/app_state.dart';
import '../services/cartera_critica_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

/// Carpeta de clientes con crédito o factura a más de 21 días.
///
/// El filtro vive en el backend. Esta pantalla solo muestra el resultado,
/// deja anotar el motivo de la mora y el criterio con el que se va a tratar.
class CarteraCriticaScreen extends StatefulWidget {
  const CarteraCriticaScreen({super.key});

  @override
  State<CarteraCriticaScreen> createState() => _CarteraCriticaScreenState();
}

class _CarteraCriticaScreenState extends State<CarteraCriticaScreen> {
  static const _rojo = Color(0xFFEF4444);

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _fmtFecha = DateFormat('dd/MM/yyyy HH:mm');
  final _busqueda = TextEditingController();

  List<ClienteCritico> _clientes = [];
  List<ConteoMotivo> _conteos = const [];
  CatalogoCartera _catalogo = CatalogoCartera.local();
  String _filtroMotivo = 'todos';
  String _filtroEstado = 'todos';
  bool _cargando = true;
  String? _error;

  static const _motivosFiltro = [
    ('todos', 'Todos'),
    ('desempleo', 'Desempleo'),
    ('alquiler', 'Alquiler'),
    ('moroso_real', 'Moroso real'),
    ('problema_familiar', 'Familiar'),
    ('otro', 'Otro'),
    ('sin_motivo', 'Sin motivo'),
  ];

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _busqueda.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    final servicio = context.read<AppState>().carteraCritica;
    try {
      final resultados = await Future.wait([
        servicio.listar(),
        servicio.catalogo().catchError((_) => CatalogoCartera.local()),
      ]);
      final pagina = resultados[0] as CarteraCriticaPagina;
      _clientes = pagina.clientes;
      _conteos = pagina.conteos;
      _catalogo = resultados[1] as CatalogoCartera;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  List<ClienteCritico> get _visibles {
    final q = _busqueda.text.trim().toLowerCase();
    return _clientes.where((c) {
      final coincideMotivo = _filtroMotivo == 'todos' || c.grupoMotivo == _filtroMotivo;
      final coincideEstado = switch (_filtroEstado) {
        'sin_nota' => c.estadoConsideracion == null,
        'todos' => true,
        _ => c.estadoConsideracion == _filtroEstado,
      };
      final coincideNombre = q.isEmpty ||
          c.clienteNombre.toLowerCase().contains(q) ||
          (c.clienteTelefono ?? '').toLowerCase().contains(q);
      return coincideMotivo && coincideEstado && coincideNombre;
    }).toList();
  }

  Future<void> _llamar(String? telefono) async {
    if (telefono == null || telefono.isEmpty) return;
    final uri = Uri.parse('tel:$telefono');
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  Future<void> _abrirNotas(ClienteCritico cliente) async {
    final guardo = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => _NotasSeguimientoSheet(
        cliente: cliente,
        catalogo: _catalogo,
        fmtFecha: _fmtFecha,
      ),
    );
    if (guardo == true) await _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final visibles = _visibles;
    final saldo = visibles.fold<double>(0, (s, c) => s + c.saldoPendienteUsd);

    return FuturisticScaffold(
      title: 'Mora +3 semanas',
      accentColor: _rojo,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(_error!, textAlign: TextAlign.center),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
                    children: [
                      Text(
                        'Solo créditos o facturas con más de ${_catalogo.diasAtrasoMinimo} días. '
                        'El resto sigue en el panel de cobranza.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const SizedBox(height: 12),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            for (final motivo in _motivosFiltro)
                              _chipMotivo(motivo.$1, motivo.$2),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _resumen('Clientes', '${visibles.length}', _rojo),
                          const SizedBox(width: 8),
                          _resumen('Saldo', _fmt.format(saldo), AppColors.amber),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _busqueda,
                        onChanged: (_) => setState(() {}),
                        decoration: const InputDecoration(
                          hintText: 'Buscar cliente o teléfono',
                          prefixIcon: Icon(Icons.search_rounded),
                        ),
                      ),
                      const SizedBox(height: 10),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _chipFiltro('Cualquier trato', 'todos'),
                            _chipFiltro('Sin nota', 'sin_nota'),
                            for (final estado in _catalogo.estados)
                              _chipFiltro(estado.etiqueta, estado.codigo),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      if (_clientes.isEmpty)
                        const EmptyState(
                          icon: Icons.folder_open_rounded,
                          message: 'Ningún cliente supera las 3 semanas de atraso',
                        )
                      else if (visibles.isEmpty)
                        const EmptyState(
                          icon: Icons.filter_alt_off_rounded,
                          message: 'Ningún cliente coincide con el filtro',
                        )
                      else
                        ...visibles.map(_tarjeta),
                    ],
                  ),
                ),
    );
  }

  Widget _resumen(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 2),
            Text(value, style: TextStyle(fontWeight: FontWeight.w800, color: color)),
          ],
        ),
      ),
    );
  }

  int _totalMotivo(String codigo) {
    for (final conteo in _conteos) {
      if (conteo.codigo == codigo) return conteo.total;
    }
    if (codigo == 'todos') return _clientes.length;
    return _clientes.where((c) => c.grupoMotivo == codigo).length;
  }

  Widget _chipMotivo(String codigo, String etiqueta) {
    final activo = _filtroMotivo == codigo;
    final total = _totalMotivo(codigo);
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text('$etiqueta ($total)'),
        selected: activo,
        onSelected: (_) => setState(() => _filtroMotivo = codigo),
        selectedColor: _rojo.withValues(alpha: 0.28),
        labelStyle: TextStyle(
          color: activo ? Colors.white : AppColors.textMuted,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
        side: BorderSide(
          color: activo ? _rojo.withValues(alpha: 0.7) : AppColors.glassBorder,
        ),
      ),
    );
  }

  Widget _chipFiltro(String label, String codigo) {
    final activo = _filtroEstado == codigo;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: activo,
        onSelected: (_) => setState(() => _filtroEstado = codigo),
        selectedColor: _rojo.withValues(alpha: 0.25),
        checkmarkColor: _rojo,
        labelStyle: TextStyle(
          color: activo ? Colors.white : AppColors.textMuted,
          fontWeight: activo ? FontWeight.w700 : FontWeight.w500,
        ),
      ),
    );
  }

  Future<void> _abrirAcuerdo(ClienteCritico cliente) async {
    final guardo = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => _AcuerdoGraciaSheet(cliente: cliente, fmt: _fmt),
    );
    if (guardo == true) await _cargar();
  }

  Widget _tarjeta(ClienteCritico cliente) {
    final enGracia = cliente.enPlazoDeGracia;
    final acento = enGracia
        ? AppColors.emerald
        : cliente.esCasoCritico
            ? _rojo
            : cliente.cabeConsideracion
                ? AppColors.emerald
                : AppColors.amber;
    final tratamiento = enGracia
        ? 'Plazo de gracia'
        : (cliente.estadoEtiqueta ?? 'Sin criterio asignado');
    final puedeAcuerdo = context.watch<AppState>().puedeOperaciones;

    return GlassContainer(
      margin: const EdgeInsets.only(bottom: 14),
      accentColor: acento,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _diasBadge(cliente),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      cliente.clienteNombre,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                    ),
                    if (cliente.clienteTelefono != null && cliente.clienteTelefono!.isNotEmpty)
                      Text(cliente.clienteTelefono!, style: Theme.of(context).textTheme.bodySmall),
                    Text(
                      '${cliente.creditos.length} crédito(s) · ${_fmt.format(cliente.saldoPendienteUsd)}',
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                    ),
                  ],
                ),
              ),
              if (cliente.clienteTelefono != null && cliente.clienteTelefono!.isNotEmpty)
                IconButton(
                  tooltip: 'Llamar',
                  onPressed: () => _llamar(cliente.clienteTelefono),
                  icon: const Icon(Icons.call_rounded, color: AppColors.emerald),
                ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _etiquetaEditable(
                icon: Icons.sell_outlined,
                texto: cliente.motivoEtiqueta ?? 'Registrar motivo',
                color: cliente.motivo == 'negativa_pago' ? _rojo : AppColors.amber,
                onTap: () => _abrirNotas(cliente),
              ),
              _etiquetaEditable(
                icon: Icons.gavel_rounded,
                texto: tratamiento,
                color: acento,
                onTap: () => _abrirNotas(cliente),
              ),
            ],
          ),
          if (enGracia && cliente.acuerdo != null) ...[
            const SizedBox(height: 10),
            Text(
              'Alerta estricta suspendida hasta ${_fechaCorta(cliente.acuerdo!.fechaLimite)}. '
              'Acuerdo de ${_fmt.format(cliente.acuerdo!.montoAcordadoUsd)} '
              'en ${cliente.acuerdo!.cuotasPactadas} cuota(s).',
              style: const TextStyle(color: AppColors.emerald, fontWeight: FontWeight.w600, height: 1.3),
            ),
          ],
          if (cliente.ultimaObservacion != null && cliente.ultimaObservacion!.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(
              cliente.ultimaObservacion!,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.textMuted, height: 1.3),
            ),
          ],
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _abrirNotas(cliente),
              icon: const Icon(Icons.edit_note_rounded),
              label: const Text('Notas de seguimiento'),
              style: OutlinedButton.styleFrom(
                foregroundColor: acento,
                side: BorderSide(color: acento.withValues(alpha: 0.6)),
              ),
            ),
          ),
          if (puedeAcuerdo) ...[
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () => _abrirAcuerdo(cliente),
                icon: const Icon(Icons.handshake_rounded),
                label: const Text(
                  'Otorgar Acuerdo Flexible / Plazo de Gracia',
                  textAlign: TextAlign.center,
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.emerald,
                  foregroundColor: AppColors.bgDeep,
                  visualDensity: VisualDensity.compact,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _fechaCorta(String iso) {
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return DateFormat('dd/MM/yyyy').format(parsed.toLocal());
  }

  Widget _diasBadge(ClienteCritico cliente) {
    if (cliente.enPlazoDeGracia) {
      return Container(
        width: 72,
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        decoration: BoxDecoration(
          color: AppColors.emerald.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.emerald.withValues(alpha: 0.5)),
        ),
        child: const Column(
          children: [
            Icon(Icons.verified_rounded, color: AppColors.emerald, size: 18),
            SizedBox(height: 2),
            Text(
              'Gracia',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.emerald, fontSize: 11, fontWeight: FontWeight.w800),
            ),
          ],
        ),
      );
    }
    return Container(
      width: 72,
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: _rojo.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _rojo.withValues(alpha: 0.45)),
      ),
      child: Column(
        children: [
          Text(
            '${cliente.diasAtraso}',
            style: const TextStyle(
              color: _rojo,
              fontWeight: FontWeight.w900,
              fontSize: 22,
              height: 1,
            ),
          ),
          const Text(
            'días',
            style: TextStyle(color: _rojo, fontSize: 11, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  Widget _etiquetaEditable({
    required IconData icon,
    required String texto,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withValues(alpha: 0.45)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 14, color: color),
              const SizedBox(width: 6),
              Text(
                texto,
                style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 12),
              ),
              const SizedBox(width: 4),
              Icon(Icons.edit_rounded, size: 12, color: color.withValues(alpha: 0.8)),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotasSeguimientoSheet extends StatefulWidget {
  const _NotasSeguimientoSheet({
    required this.cliente,
    required this.catalogo,
    required this.fmtFecha,
  });

  final ClienteCritico cliente;
  final CatalogoCartera catalogo;
  final DateFormat fmtFecha;

  @override
  State<_NotasSeguimientoSheet> createState() => _NotasSeguimientoSheetState();
}

class _NotasSeguimientoSheetState extends State<_NotasSeguimientoSheet> {
  final _observacion = TextEditingController();
  List<NotaSeguimiento> _notas = [];
  bool _cargando = true;
  bool _guardando = false;
  String? _error;
  late final List<OpcionCartera> _motivos;
  late final List<OpcionCartera> _estados;
  late String _motivo;
  late String _estado;

  @override
  void initState() {
    super.initState();
    _motivos = widget.catalogo.motivos.isEmpty
        ? CatalogoCartera.local().motivos
        : widget.catalogo.motivos;
    _estados = widget.catalogo.estados.isEmpty
        ? CatalogoCartera.local().estados
        : widget.catalogo.estados;
    final motivoActual = widget.cliente.motivo;
    final estadoActual = widget.cliente.estadoConsideracion;
    _motivo = _motivos.any((m) => m.codigo == motivoActual)
        ? motivoActual!
        : _motivos.first.codigo;
    _estado = _estados.any((e) => e.codigo == estadoActual)
        ? estadoActual!
        : _estados.first.codigo;
    _cargar();
  }

  @override
  void dispose() {
    _observacion.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      _notas = await context.read<AppState>().carteraCritica.notas(widget.cliente.clienteId);
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _guardar() async {
    final texto = _observacion.text.trim();
    if (texto.length < 3) {
      setState(() => _error = 'Escribe por qué no ha pagado, con al menos una frase corta.');
      return;
    }
    setState(() {
      _guardando = true;
      _error = null;
    });
    try {
      await context.read<AppState>().carteraCritica.guardarNota(
            clienteId: widget.cliente.clienteId,
            motivo: _motivo,
            estadoConsideracion: _estado,
            observacion: texto,
          );
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _guardando = false;
          _error = e.toString();
        });
      }
    }
  }

  String _fecha(String iso) {
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return widget.fmtFecha.format(parsed.toLocal());
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    final considera = _motivo == 'desempleado_temporal' ||
        _motivo == 'problema_familiar' ||
        _motivo == 'alquiler_pendiente';

    return Padding(
      padding: EdgeInsets.fromLTRB(16, 12, 16, 16 + bottom),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.textMuted.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            const SizedBox(height: 14),
            Text(
              widget.cliente.clienteNombre,
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
            ),
            Text(
              '${widget.cliente.diasAtraso} días de atraso',
              style: const TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            Text(
              considera
                  ? 'Este motivo admite consideración: desempleo, familia o alquiler.'
                  : 'Motivo de firmeza. Revísalo antes de pasar a cobro estricto.',
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _motivo,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Motivo de no pago'),
              dropdownColor: AppColors.bgElevated,
              items: [
                for (final op in _motivos)
                  DropdownMenuItem(value: op.codigo, child: Text(op.etiqueta)),
              ],
              onChanged: _guardando ? null : (v) => setState(() => _motivo = v ?? _motivo),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: _estado,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Cómo tratar este caso'),
              dropdownColor: AppColors.bgElevated,
              items: [
                for (final op in _estados)
                  DropdownMenuItem(value: op.codigo, child: Text(op.etiqueta)),
              ],
              onChanged: _guardando ? null : (v) => setState(() => _estado = v ?? _estado),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _observacion,
              minLines: 3,
              maxLines: 5,
              maxLength: 2000,
              decoration: const InputDecoration(
                labelText: 'Observación',
                hintText: 'Qué pasó, qué se acordó y cuándo volver a hablar',
                alignLabelWithHint: true,
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 4),
              Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))),
            ],
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _guardando ? null : _guardar,
                icon: _guardando
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_rounded),
                label: const Text('Guardar nota'),
              ),
            ),
            const SizedBox(height: 18),
            const Text('Historial', style: TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            if (_cargando)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_notas.isEmpty)
              const Text(
                'Todavía no hay notas para este cliente.',
                style: TextStyle(color: AppColors.textMuted),
              )
            else
              ..._notas.map(_nota),
          ],
        ),
      ),
    );
  }

  Widget _nota(NotaSeguimiento nota) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.bgElevated.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.glassBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _fecha(nota.fecha),
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
          ),
          Text(
            '${nota.usuarioNombre} · ${nota.motivoEtiqueta}',
            style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(nota.estadoEtiqueta, style: const TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(nota.observacion),
        ],
      ),
    );
  }
}

class _AcuerdoGraciaSheet extends StatefulWidget {
  const _AcuerdoGraciaSheet({required this.cliente, required this.fmt});

  final ClienteCritico cliente;
  final NumberFormat fmt;

  @override
  State<_AcuerdoGraciaSheet> createState() => _AcuerdoGraciaSheetState();
}

class _AcuerdoGraciaSheetState extends State<_AcuerdoGraciaSheet> {
  late final TextEditingController _monto;
  late final TextEditingController _cuotas;
  final _nota = TextEditingController();
  late DateTime _fecha;
  bool _guardando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _monto = TextEditingController(
      text: widget.cliente.saldoPendienteUsd.toStringAsFixed(2),
    );
    _cuotas = TextEditingController(text: '1');
    final hoy = DateTime.now();
    _fecha = DateTime(hoy.year, hoy.month, hoy.day).add(const Duration(days: 7));
  }

  @override
  void dispose() {
    _monto.dispose();
    _cuotas.dispose();
    _nota.dispose();
    super.dispose();
  }

  Future<void> _elegirFecha() async {
    final hoy = DateTime.now();
    final inicio = DateTime(hoy.year, hoy.month, hoy.day);
    final elegida = await showDatePicker(
      context: context,
      initialDate: _fecha.isBefore(inicio) ? inicio : _fecha,
      firstDate: inicio,
      lastDate: inicio.add(const Duration(days: 730)),
    );
    if (elegida != null) {
      setState(() => _fecha = DateTime(elegida.year, elegida.month, elegida.day));
    }
  }

  Future<void> _guardar() async {
    final monto = double.tryParse(_monto.text.replaceAll(',', '.'));
    final cuotas = int.tryParse(_cuotas.text.trim());
    final nota = _nota.text.trim();
    if (monto == null || monto <= 0) {
      setState(() => _error = 'Indica el monto acordado.');
      return;
    }
    if (cuotas == null || cuotas < 1) {
      setState(() => _error = 'Las cuotas pactadas deben ser al menos 1.');
      return;
    }
    if (nota.length < 3) {
      setState(() => _error = 'Escribe la nota de consideración.');
      return;
    }
    setState(() {
      _guardando = true;
      _error = null;
    });
    try {
      await context.read<AppState>().carteraCritica.otorgarAcuerdo(
            clienteId: widget.cliente.clienteId,
            montoAcordadoUsd: monto,
            fechaLimite: _fecha,
            cuotasPactadas: cuotas,
            notaConsideracion: nota,
          );
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _guardando = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    final fechaTxt = DateFormat('dd/MM/yyyy').format(_fecha);
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 12, 16, 16 + bottom),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.textMuted.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            const SizedBox(height: 14),
            Text(
              widget.cliente.clienteNombre,
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
            ),
            const SizedBox(height: 4),
            const Text(
              'El vencimiento original de las cuotas no cambia. '
              'Mientras llegue esta fecha, se suspende la alerta estricta.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12, height: 1.35),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _monto,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Monto acordado (USD)',
                helperText: 'Saldo actual ${widget.fmt.format(widget.cliente.saldoPendienteUsd)}',
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _cuotas,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Cuotas pactadas'),
            ),
            const SizedBox(height: 10),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Nueva fecha límite'),
              subtitle: Text(fechaTxt, style: const TextStyle(fontWeight: FontWeight.w800)),
              trailing: const Icon(Icons.event_rounded, color: AppColors.emerald),
              onTap: _guardando ? null : _elegirFecha,
            ),
            TextField(
              controller: _nota,
              minLines: 3,
              maxLines: 5,
              maxLength: 2000,
              decoration: const InputDecoration(
                labelText: 'Nota de consideración',
                hintText: 'Por qué se otorga el plazo y qué se espera del cliente',
                alignLabelWithHint: true,
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 4),
              Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))),
            ],
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _guardando ? null : _guardar,
                icon: _guardando
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.handshake_rounded),
                label: const Text('Guardar plazo de gracia'),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.emerald,
                  foregroundColor: AppColors.bgDeep,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
