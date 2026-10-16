import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../config/api_config.dart';
import '../services/biometric_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_background.dart';
import '../widgets/glass_container.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _correoCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _bio = BiometricService();

  bool _ocultarPassword = true;
  bool _tieneSesionGuardada = false;
  bool _biometriaDisponible = false;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _cargarOpcionesBiometria());
  }

  @override
  void dispose() {
    _correoCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarOpcionesBiometria() async {
    final credenciales = await _bio.leerCredenciales();
    final soporta = await _bio.soportaBiometria();
    if (!mounted) return;
    setState(() {
      _tieneSesionGuardada = credenciales != null;
      _biometriaDisponible = soporta;
      if (credenciales != null && _correoCtrl.text.isEmpty) {
        _correoCtrl.text = credenciales.correo;
      }
    });
  }

  Future<void> _ingresarConBiometria() async {
    await context.read<AppState>().loginConBiometria();
  }

  Future<void> _ofrecerActivarHuella(String correo, String password) async {
    if (!await _bio.soportaBiometria()) return;
    if (!mounted) return;
    final activar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Huella dactilar'),
        content: const Text(
          '¿Activar ingreso con huella dactilar para este usuario en este dispositivo?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Ahora no')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Activar')),
        ],
      ),
    );
    if (activar == true) {
      await _bio.guardarCredenciales(correo: correo, password: password);
    } else {
      await _bio.borrarCredenciales();
    }
    await _cargarOpcionesBiometria();
  }

  Future<void> _login() async {
    final correo = _correoCtrl.text.trim();
    final password = _passwordCtrl.text;
    if (correo.isEmpty || password.length < 4) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa usuario y contraseña (mínimo 4 caracteres)')),
      );
      return;
    }
    final ok = await context.read<AppState>().login(correo, password);
    if (!mounted || !ok) return;
    await _ofrecerActivarHuella(correo, password);
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final mostrarHuella = _tieneSesionGuardada && _biometriaDisponible;

    return Scaffold(
      body: FuturisticBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.neonCyan.withValues(alpha: 0.1),
                        border: Border.all(color: AppColors.neonCyan.withValues(alpha: 0.4)),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.neonCyan.withValues(alpha: 0.25),
                            blurRadius: 32,
                            spreadRadius: -4,
                          ),
                        ],
                      ),
                      child: const Icon(Icons.hub, size: 56, color: AppColors.neonCyan),
                    ),
                    const SizedBox(height: 24),
                    ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [AppColors.neonCyan, AppColors.neonBlue],
                      ).createShader(bounds),
                      child: Text(
                        'ED NET PRO',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              color: Colors.white,
                              fontSize: 32,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2,
                            ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text('Sistema Ruteros Multimoneda'),
                    const SizedBox(height: 8),
                    Text(
                      ApiConfig.apiBaseUrl,
                      style: Theme.of(context).textTheme.bodySmall,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    GlassContainer(
                      accentColor: AppColors.neonBlue,
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          TextField(
                            controller: _correoCtrl,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            style: const TextStyle(color: AppColors.textPrimary),
                            decoration: const InputDecoration(
                              labelText: 'Correo o usuario',
                              prefixIcon: Icon(Icons.alternate_email_rounded),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _passwordCtrl,
                            obscureText: _ocultarPassword,
                            style: const TextStyle(color: AppColors.textPrimary),
                            decoration: InputDecoration(
                              labelText: 'Contraseña',
                              prefixIcon: const Icon(Icons.lock_outline_rounded),
                              suffixIcon: IconButton(
                                onPressed: () => setState(() => _ocultarPassword = !_ocultarPassword),
                                icon: Icon(
                                  _ocultarPassword ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                ),
                              ),
                            ),
                            onSubmitted: (_) => _login(),
                          ),
                          if (state.error != null)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: Text(
                                state.error!,
                                style: const TextStyle(color: Color(0xFFEF4444)),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: state.cargando ? null : _login,
                              icon: state.cargando
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    )
                                  : const Icon(Icons.login_rounded),
                              label: Text(state.cargando ? 'Conectando...' : 'Ingresar con contraseña'),
                            ),
                          ),
                          if (mostrarHuella) ...[
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: OutlinedButton.icon(
                                onPressed: state.cargando ? null : _ingresarConBiometria,
                                icon: const Icon(Icons.fingerprint_rounded),
                                label: const Text('Ingresar con huella dactilar'),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
