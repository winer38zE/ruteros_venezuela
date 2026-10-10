import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../screens/datos_bancarios_screen.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';
import 'glass_container.dart';

class DatosBancariosCard extends StatefulWidget {
  const DatosBancariosCard({super.key});

  @override
  State<DatosBancariosCard> createState() => _DatosBancariosCardState();
}

class _DatosBancariosCardState extends State<DatosBancariosCard> {
  DatosBancarios? _datos;
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
      final datos = await context.read<AppState>().empresas.datosBancarios();
      if (!mounted) return;
      setState(() => _datos = datos);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _copiar(String etiqueta, String valor) async {
    await Clipboard.setData(ClipboardData(text: valor));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('$etiqueta copiado')),
    );
  }

  Future<void> _copiarTodo() async {
    final datos = _datos;
    if (datos == null) return;
    final lineas = <String>[
      if ((datos.banco ?? '').trim().isNotEmpty) 'Banco: ${datos.banco}',
      if ((datos.tipoCuenta ?? '').trim().isNotEmpty) 'Tipo de cuenta: ${datos.tipoCuenta}',
      if ((datos.numeroCuenta ?? '').trim().isNotEmpty) 'Número: ${datos.numeroCuenta}',
      if ((datos.cedulaNit ?? '').trim().isNotEmpty) 'Cédula/NIT: ${datos.cedulaNit}',
    ];
    if (lineas.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: lineas.join('\n')));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Datos bancarios copiados')),
    );
  }

  Future<void> _abrirConfiguracion() async {
    final guardado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const DatosBancariosScreen()),
    );
    if (guardado == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final puedeEditar = context.watch<AppState>().puedeOperaciones;
    return GlassContainer(
      accentColor: AppColors.neonBlue,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Datos para la transferencia',
            style: TextStyle(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 4),
          const Text(
            'El cliente puede copiar estos datos y pagar desde su banco.',
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
          const SizedBox(height: 8),
          if (_cargando)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: LinearProgressIndicator(),
            )
          else if (_error != null)
            Text(_error!, style: const TextStyle(color: Color(0xFFEF4444)))
          else if (_datos == null || !_datos!.configurado)
            Text(
              puedeEditar
                  ? 'Aún no hay cuenta configurada. Registra banco, tipo, número y cédula o NIT.'
                  : 'La empresa aún no configuró la cuenta de transferencia.',
              style: const TextStyle(fontWeight: FontWeight.w600),
            )
          else ...[
            _fila('Banco', _datos!.banco),
            _fila('Tipo de cuenta', _datos!.tipoCuenta),
            _fila('Número', _datos!.numeroCuenta),
            _fila('Cédula/NIT', _datos!.cedulaNit),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _copiarTodo,
                icon: const Icon(Icons.copy_all_rounded),
                label: const Text('Copiar todo'),
              ),
            ),
          ],
          if (puedeEditar)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _abrirConfiguracion,
                icon: const Icon(Icons.account_balance_rounded),
                label: Text(_datos?.configurado == true ? 'Editar datos' : 'Configurar cuenta'),
              ),
            ),
        ],
      ),
    );
  }

  Widget _fila(String etiqueta, String? valor) {
    final texto = (valor ?? '').trim();
    return ListTile(
      contentPadding: EdgeInsets.zero,
      dense: true,
      title: Text(etiqueta, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
      subtitle: Text(
        texto.isEmpty ? 'Sin configurar' : texto,
        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
      ),
      trailing: texto.isEmpty
          ? null
          : IconButton(
              tooltip: 'Copiar',
              onPressed: () => _copiar(etiqueta, texto),
              icon: const Icon(Icons.copy_rounded),
            ),
    );
  }
}

class FaseTransferencia extends StatelessWidget {
  const FaseTransferencia({
    super.key,
    required this.esCredito,
    required this.referenciaCtrl,
    required this.comprobanteNombre,
    required this.onElegirFoto,
    this.onQuitarFoto,
    this.detalleCredito,
  });

  final bool esCredito;
  final String? detalleCredito;
  final TextEditingController referenciaCtrl;
  final String? comprobanteNombre;
  final VoidCallback onElegirFoto;
  final VoidCallback? onQuitarFoto;

  @override
  Widget build(BuildContext context) {
    final metodo = esCredito ? 'Venta a crédito' : 'Venta de contado';
    final detalle = esCredito
        ? 'La venta queda a crédito${detalleCredito == null || detalleCredito!.isEmpty ? '' : ' ($detalleCredito)'}. '
            'El cliente usa estos datos para pagar las cuotas. El cobro se confirma al registrar el abono.'
        : 'La venta de contado se cobra ahora. Vendedor o cobrador: Pagada (Por Verificar). Dueño o administrador: Pagada.';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.neonBlue.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.neonBlue.withValues(alpha: 0.45)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Fase 2 · Transferencia bancaria',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(metodo, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              const SizedBox(height: 4),
              Text(detalle, style: const TextStyle(fontSize: 13)),
            ],
          ),
        ),
        const SizedBox(height: 12),
        const DatosBancariosCard(),
        const SizedBox(height: 12),
        CamposComprobanteTransferencia(
          referenciaCtrl: referenciaCtrl,
          comprobanteNombre: comprobanteNombre,
          onElegirFoto: onElegirFoto,
          onQuitarFoto: onQuitarFoto,
        ),
      ],
    );
  }
}

class CamposComprobanteTransferencia extends StatelessWidget {
  const CamposComprobanteTransferencia({
    super.key,
    required this.referenciaCtrl,
    required this.comprobanteNombre,
    required this.onElegirFoto,
    this.onQuitarFoto,
  });

  final TextEditingController referenciaCtrl;
  final String? comprobanteNombre;
  final VoidCallback onElegirFoto;
  final VoidCallback? onQuitarFoto;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: referenciaCtrl,
          decoration: const InputDecoration(
            labelText: 'Referencia / número de comprobante',
            prefixIcon: Icon(Icons.tag_rounded),
          ),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: onElegirFoto,
          icon: const Icon(Icons.photo_camera_outlined),
          label: Text(
            comprobanteNombre == null ? 'Adjuntar foto del comprobante' : 'Cambiar foto',
          ),
        ),
        if (comprobanteNombre != null) ...[
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.image_outlined, size: 18, color: AppColors.emerald),
              const SizedBox(width: 8),
              Expanded(child: Text(comprobanteNombre!)),
              if (onQuitarFoto != null)
                IconButton(
                  tooltip: 'Quitar foto',
                  onPressed: onQuitarFoto,
                  icon: const Icon(Icons.close_rounded),
                ),
            ],
          ),
        ],
      ],
    );
  }
}
