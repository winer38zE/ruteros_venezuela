import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/perfil_service.dart';
import '../theme/app_theme.dart';
import '../utils/region_bancaria.dart';
import '../widgets/cuenta_bancaria_form_dialog.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

/// Cuenta del empleado (vendedor/cobrador) para recibir nómina.
class CuentaBancariaEmpleadoScreen extends StatefulWidget {
  const CuentaBancariaEmpleadoScreen({super.key});

  @override
  State<CuentaBancariaEmpleadoScreen> createState() =>
      _CuentaBancariaEmpleadoScreenState();
}

class _CuentaBancariaEmpleadoScreenState extends State<CuentaBancariaEmpleadoScreen> {
  bool _cargando = true;
  CuentaBancariaEmpleado? _cuenta;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final c = await context.read<AppState>().perfil.obtenerCuentaBancaria();
      if (mounted) setState(() => _cuenta = c);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _editar() async {
    final state = context.read<AppState>();
    final config = await configuracionBancariaSesion(
      paises: state.paises,
      region: state.region,
      paisUsuario: state.usuario?.pais,
      paisId: state.usuario?.paisId,
    );
    if (!mounted) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => CuentaBancariaFormDialog(
        config: config,
        titulo: 'Mi cuenta para nómina',
        onGuardar: (data) async {
          await state.perfil.guardarCuentaBancaria(
            banco: data.banco,
            tipoCuenta: data.tipoCuenta,
            titular: data.titular,
            documentoIdentidad: data.documentoIdentidad,
            canal: data.canal,
            numeroCuenta: data.numeroCuenta,
            telefonoPagoMovil: data.telefonoPagoMovil,
          );
        },
      ),
    );
    if (ok == true) _cargar();
  }

  Widget _buildDetalleCuenta(CuentaBancariaEmpleado cuenta) {
    final telefono = cuenta.telefonoPagoMovil?.trim();
    final usaTelefono = telefono != null && telefono.isNotEmpty;

    return GlassContainer(
      accentColor: AppColors.emerald,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${cuenta.banco} · ${cuenta.canal}',
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
          ),
          const SizedBox(height: 8),
          if (usaTelefono)
            Text('Teléfono: ${cuenta.telefonoPagoMovil ?? "Sin asignar"}')
          else
            Text('Cuenta: ${cuenta.numeroCuenta ?? "No definida"}'),
          Text('Titular: ${cuenta.titular.isNotEmpty ? cuenta.titular : "Sin asignar"}'),
          Text(
            'Documento: ${cuenta.documentoIdentidad.isNotEmpty ? cuenta.documentoIdentidad : "Sin asignar"}',
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cuenta = _cuenta;

    return FuturisticScaffold(
      title: 'Mi cuenta bancaria',
      accentColor: AppColors.emerald,
      actions: [
        if (!_cargando)
          IconButton(onPressed: _editar, icon: const Icon(Icons.edit_rounded)),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (cuenta == null)
                  const EmptyState(
                    icon: Icons.account_balance_wallet_outlined,
                    message:
                        'Registra tu cuenta con los bancos de tu país para recibir pagos.',
                  )
                else
                  _buildDetalleCuenta(cuenta),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _cargando ? null : _editar,
                  icon: const Icon(Icons.add_card_rounded),
                  label: Text(cuenta == null ? 'Registrar cuenta' : 'Actualizar cuenta'),
                ),
              ],
            ),
    );
  }
}
