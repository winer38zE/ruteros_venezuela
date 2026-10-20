import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/regional_copy.dart';
import '../providers/app_state.dart';
import '../services/onboarding_prefs.dart';
import '../theme/app_theme.dart';
import '../utils/launch_whatsapp.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import 'first_use_tutorial_screen.dart';

class _FaqItem {
  const _FaqItem({required this.pregunta, required this.respuesta});

  final String pregunta;
  final String respuesta;
}

class HelpScreen extends StatelessWidget {
  const HelpScreen({super.key});

  List<_FaqItem> _faqs(RegionalCopy copy) => [
        _FaqItem(
          pregunta: '¿Puedo usar la app sin internet?',
          respuesta:
              'Sí. Puedes registrar clientes y operaciones offline. Cuando vuelva la conexión, los datos se sincronizan con el servidor.',
        ),
        _FaqItem(
          pregunta: '¿Cómo registro ${copy.ventasCreditoCorto}?',
          respuesta:
              'Ve a Ventas → Nueva venta, elige al cliente y marca la venta como crédito. El saldo queda asociado al cliente.',
        ),
        _FaqItem(
          pregunta: '¿Cómo cobro en la ruta?',
          respuesta:
              'En Cobros → Nuevo cobro selecciona la venta pendiente, indica monto y moneda de pago, y guarda el abono.',
        ),
        _FaqItem(
          pregunta: '¿Qué monedas soporta?',
          respuesta:
              'La moneda principal depende del país elegido al iniciar sesión. También puedes registrar pagos en otras monedas según la configuración de tu empresa.',
        ),
        _FaqItem(
          pregunta: '¿Cómo cambio de país?',
          respuesta:
              'Cierra sesión y vuelve a entrar seleccionando otro país en la pantalla de login. Tus credenciales de huella quedan ligadas al país que guardaste.',
        ),
      ];

  Future<void> _repetirTutorial(BuildContext context) async {
    await OnboardingPrefs.reiniciarTutorial();
    if (!context.mounted) return;
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => const FirstUseTutorialScreen(soloLectura: true),
      ),
    );
  }

  Future<void> _contactar(BuildContext context) async {
    final state = context.read<AppState>();
    final pais = state.region?.nombre ?? state.usuario?.pais?.nombre;
    final ok = await abrirWhatsappSoporte(paisNombre: pais);
    if (!context.mounted) return;
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo abrir WhatsApp. Verifica que esté instalado.'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final copy = RegionalCopy.fromEsVenezuela(context.watch<AppState>().esVenezuela);
    final faqs = _faqs(copy);

    return FuturisticScaffold(
      title: 'Ayuda',
      accentColor: AppColors.neonBlue,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          GlassContainer(
            accentColor: AppColors.neonCyan,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '¿Necesitas una mano?',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17),
                ),
                const SizedBox(height: 6),
                Text(
                  'Revisa las preguntas frecuentes o escríbenos por WhatsApp.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: () => _contactar(context),
                        icon: const Icon(Icons.chat_rounded),
                        label: const Text('Contactar por WhatsApp'),
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFF25D366),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => _repetirTutorial(context),
                    icon: const Icon(Icons.school_rounded),
                    label: const Text('Repetir guía de primer uso'),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          const SectionTitle(title: 'Preguntas frecuentes'),
          const SizedBox(height: 8),
          ...faqs.map(
            (f) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: GlassContainer(
                accentColor: AppColors.neonBlue,
                padding: EdgeInsets.zero,
                child: Theme(
                  data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                  child: ExpansionTile(
                    title: Text(
                      f.pregunta,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text(f.respuesta),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
