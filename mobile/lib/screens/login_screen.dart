import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../config/api_config.dart';
import '../services/api_service.dart';
import '../services/tasas_login_cache.dart';
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

  bool _ocultarPassword = true;
  bool _puedeHuella = false;
  String? _diagnosticoConexion;
  bool _probandoConexion = false;
  double? _tasaBcv;
  double? _tasaParalelo;
  final _fmtTasa = NumberFormat('#,##0.00', 'es_VE');

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _cargarOpcionesBiometria();
      _cargarTasasLogin();
    });
  }

  @override
  void dispose() {
    _correoCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarOpcionesBiometria() async {
    final auth = context.read<AppState>().auth;
    final credenciales = await auth.biometric.leerCredenciales();
    final puede = await auth.biometric.puedeIngresarConBiometria();
    if (!mounted) return;
    setState(() {
      _puedeHuella = puede;
      if (credenciales != null && _correoCtrl.text.isEmpty) {
        _correoCtrl.text = credenciales.correo;
      }
    });
  }

  Future<void> _cargarTasasLogin() async {
    final cache = await TasasLoginCache.leer();
    if (!mounted) return;
    setState(() {
      _tasaBcv = cache.bcv;
      _tasaParalelo = cache.paralelo;
    });
  }

  Future<void> _ingresarConBiometria() async {
    await context.read<AppState>().loginConBiometria();
    if (!mounted) return;
    await _cargarOpcionesBiometria();
    await _cargarTasasLogin();
  }

  Future<void> _ofrecerActivarHuella(String correo, String password) async {
    final auth = context.read<AppState>().auth;
    if (!await auth.biometric.soportaBiometria()) return;
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
      await auth.activarAccesoBiometrico(correo: correo, password: password);
    } else {
      await auth.biometric.borrarTodoAccesoBiometrico();
    }
    await _cargarOpcionesBiometria();
  }

  Future<void> _probarConexion() async {
    setState(() {
      _probandoConexion = true;
      _diagnosticoConexion = null;
    });
    final api = context.read<AppState>().api;
    try {
      final data = await api.fetchHealthReady();
      if (!mounted) return;
      setState(() {
        _diagnosticoConexion =
            'Listo: ${data['status'] ?? 'ready'} · PB init=${data['pocketbase_initialized']} · '
            'latencia=${data['ultima_latencia_ms'] ?? '?'} ms';
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _diagnosticoConexion = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _diagnosticoConexion = e.toString();
      });
    } finally {
      if (mounted) setState(() => _probandoConexion = false);
    }
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
    await _cargarTasasLogin();
  }

  String _textoTasa(double? valor) {
    if (valor == null) return '—';
    return '${_fmtTasa.format(valor)} Bs';
  }

  Widget _panelTasas() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: GlassContainer(
        accentColor: AppColors.neonCyan,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          children: [
            Text(
              'Tasa de cambio (referencia)',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('USD BCV (oficial)', style: Theme.of(context).textTheme.bodySmall),
                      Text(
                        _textoTasa(_tasaBcv),
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: AppColors.neonCyan,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('USD paralelo', style: Theme.of(context).textTheme.bodySmall),
                      Text(
                        _textoTasa(_tasaParalelo),
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: AppColors.neonBlue,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (_tasaBcv == null && _tasaParalelo == null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  'Tras el primer ingreso se actualizarán aquí.',
                  style: Theme.of(context).textTheme.bodySmall,
                  textAlign: TextAlign.center,
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

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
                    GestureDetector(
                      onLongPress: _probandoConexion ? null : _probarConexion,
                      child: Text(
                        ApiConfig.apiBaseUrl,
                        style: Theme.of(context).textTheme.bodySmall,
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 4),
                    TextButton(
                      onPressed: _probandoConexion ? null : _probarConexion,
                      child: Text(
                        _probandoConexion ? 'Probando conexión…' : 'Probar conexión',
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ),
                    if (_diagnosticoConexion != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text(
                          _diagnosticoConexion!,
                          style: Theme.of(context).textTheme.bodySmall,
                          textAlign: TextAlign.center,
                        ),
                      ),
                    const SizedBox(height: 16),
                    _panelTasas(),
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
                              padding: const EdgeInsets.only(top: 12, bottom: 12),
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
                          if (_puedeHuella) ...[
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
