import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/regional_copy.dart';
import '../providers/app_state.dart';
import '../services/onboarding_prefs.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import 'cliente_form_screen.dart';
import 'nueva_venta_screen.dart';
import 'nuevo_cobro_screen.dart';

class FirstUseTutorialScreen extends StatelessWidget {
  const FirstUseTutorialScreen({super.key, this.soloLectura = false});

  /// Si es true, no marca el tutorial como completado al salir (repetición desde Ayuda).
  final bool soloLectura;

  Future<void> _ir(BuildContext context, Widget screen) async {
    await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => screen),
    );
  }

  Future<void> _cerrar(BuildContext context) async {
    if (!soloLectura) {
      await OnboardingPrefs.marcarTutorialCompletado();
    }
    if (context.mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final copy = RegionalCopy.fromEsVenezuela(context.read<AppState>().esVenezuela);

    return FuturisticScaffold(
      title: 'Primeros pasos',
      accentColor: AppColors.neonBlue,
      actions: [
        IconButton(
          icon: const Icon(Icons.close_rounded),
          onPressed: () => _cerrar(context),
        ),
      ],
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          Text(
            'En tres pasos tendrás tu operación básica lista.',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Puedes repetir esta guía cuando quieras desde Ayuda.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 20),
          _PasoCard(
            paso: 1,
            icon: Icons.person_add_rounded,
            color: AppColors.neonCyan,
            titulo: 'Crear un cliente',
            detalle: copy.emptyClientesDetalle,
            boton: 'Registrar cliente',
            onTap: () => _ir(context, const ClienteFormScreen()),
          ),
          const SizedBox(height: 12),
          _PasoCard(
            paso: 2,
            icon: Icons.add_shopping_cart_rounded,
            color: AppColors.emerald,
            titulo: 'Registrar una venta',
            detalle: copy.emptyVentasDetalle,
            boton: 'Nueva venta',
            onTap: () => _ir(context, const NuevaVentaScreen()),
          ),
          const SizedBox(height: 12),
          _PasoCard(
            paso: 3,
            icon: Icons.payments_rounded,
            color: AppColors.violet,
            titulo: 'Registrar un abono',
            detalle: copy.emptyCobrosDetalle,
            boton: 'Nuevo cobro',
            onTap: () => _ir(context, const NuevoCobroScreen()),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => _cerrar(context),
              child: Text(soloLectura ? 'Cerrar' : 'Entendido, ir al inicio'),
            ),
          ),
        ],
      ),
    );
  }
}

class _PasoCard extends StatelessWidget {
  const _PasoCard({
    required this.paso,
    required this.icon,
    required this.color,
    required this.titulo,
    required this.detalle,
    required this.boton,
    required this.onTap,
  });

  final int paso;
  final IconData icon;
  final Color color;
  final String titulo;
  final String detalle;
  final String boton;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      accentColor: color,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 16,
                backgroundColor: color.withValues(alpha: 0.2),
                child: Text(
                  '$paso',
                  style: TextStyle(color: color, fontWeight: FontWeight.w800),
                ),
              ),
              const SizedBox(width: 10),
              Icon(icon, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  titulo,
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(detalle, style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.tonal(
              onPressed: onTap,
              style: FilledButton.styleFrom(
                backgroundColor: color.withValues(alpha: 0.18),
                foregroundColor: color,
              ),
              child: Text(boton),
            ),
          ),
        ],
      ),
    );
  }
}
