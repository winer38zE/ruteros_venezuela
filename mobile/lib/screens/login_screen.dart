import 'package:dropdown_button2/dropdown_button2.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/pais_region.dart';
import '../providers/app_state.dart';
import '../config/api_config.dart';
import '../services/api_service.dart';
import '../services/tasas_login_cache.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_background.dart';
import '../widgets/glass_container.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _correoCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();

  bool _ocultarPassword = true;
  /// Lector biométrico en el dispositivo (el botón siempre visible si true).
  bool _dispositivoConHuella = false;
  /// Sesión/credenciales ya guardadas para entrar con huella.
  bool _huellaHabilitada = false;
  String? _diagnosticoConexion;
  bool _probandoConexion = false;
  double? _tasaBcv;
  double? _tasaParalelo;
  final _fmtTasa = NumberFormat('#,##0.00', 'es_VE');

  List<PaisRegion> _paises = [];
  String? _paisIdSeleccionado;
  bool _cargandoPaises = true;
  String? _errorPaises;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _cargarPaises();
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
    final paisId = _paisIdSeleccionado;
    final correoHint = _correoCtrl.text.trim();
    final conLector = await auth.biometric.soportaBiometria();
    var habilitada = false;
    ({String correo, String password})? credenciales;
    if (paisId != null && paisId.isNotEmpty) {
      habilitada = await auth.biometric.puedeIngresarConBiometria(
        paisId: paisId,
        correo: correoHint.isNotEmpty ? correoHint : null,
      );
      credenciales = await auth.biometric.leerCredenciales(
        paisId: paisId,
        correo: correoHint.isNotEmpty ? correoHint : null,
      );
    }
    if (!mounted) return;
    setState(() {
      _dispositivoConHuella = conLector;
      _huellaHabilitada = habilitada;
      if (credenciales != null && _correoCtrl.text.isEmpty) {
        _correoCtrl.text = credenciales.correo;
      }
    });
  }

  Future<void> _cargarPaises() async {
    final state = context.read<AppState>();
    setState(() {
      _cargandoPaises = true;
      _errorPaises = null;
    });
    try {
      final lista = await state.paises.listarActivos();
      final guardado = await state.regionSession.leer();
      final paisHuella = await state.auth.biometric.leerPaisLoginId();
      String? seleccion;
      if (guardado != null && lista.any((p) => p.id == guardado.id)) {
        seleccion = guardado.id;
      } else if (paisHuella != null &&
          paisHuella.isNotEmpty &&
          lista.any((p) => p.id == paisHuella)) {
        seleccion = paisHuella;
      }
      if (seleccion == null && lista.length == 1) {
        seleccion = lista.first.id;
      }
      if (!mounted) return;
      setState(() {
        _paises = lista;
        _paisIdSeleccionado = seleccion;
        _cargandoPaises = false;
        if (lista.isEmpty) {
          _errorPaises =
              'No hay países disponibles. Ejecuta seed_paises en el servidor.';
        }
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoPaises = false;
        _errorPaises = e.statusCode == 404
            ? 'Catálogo de países no disponible en la API. '
                'Verifica ${ApiConfig.apiBaseUrl}/paises'
            : e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoPaises = false;
        _errorPaises = e.toString();
      });
    }
  }

  bool get _puedeIniciarSesion =>
      !_cargandoPaises &&
      _errorPaises == null &&
      _paises.isNotEmpty &&
      _paisIdSeleccionado != null &&
      _paisIdSeleccionado!.isNotEmpty;

  bool get _puedeIngresarHuella =>
      _puedeIniciarSesion && _dispositivoConHuella && _huellaHabilitada;

  PaisRegion? get _paisSeleccionado {
    final id = _paisIdSeleccionado;
    if (id == null) return null;
    for (final p in _paises) {
      if (p.id == id) return p;
    }
    return null;
  }

  Future<void> _alElegirPais(String? id) async {
    setState(() => _paisIdSeleccionado = id);
    if (id == null || id.isEmpty) return;
    PaisRegion? elegido;
    for (final p in _paises) {
      if (p.id == id) {
        elegido = p;
        break;
      }
    }
    if (elegido == null || !mounted) return;
    await context.read<AppState>().regionSession.guardar(elegido);
    await _cargarOpcionesBiometria();
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
    final auth = context.read<AppState>().auth;
    final paisId = _paisIdSeleccionado;
    if (paisId == null || paisId.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona tu país antes de usar la huella')),
      );
      return;
    }

    if (!mounted) return;
    final state = context.read<AppState>();
    final ok = await state.loginConBiometria(
      paisIdSeleccionado: paisId,
      correoHint: _correoCtrl.text.trim().isNotEmpty
          ? _correoCtrl.text.trim()
          : null,
    );
    if (!mounted) return;

    if (ok && state.usuario != null) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
      return;
    }

    await _cargarOpcionesBiometria();
    await _cargarTasasLogin();
  }

  Future<void> _ofrecerActivarHuella(
    String correo,
    String password,
    String paisId,
  ) async {
    final auth = context.read<AppState>().auth;
    if (!await auth.biometric.soportaBiometria()) return;
    if (await auth.biometric.tieneCredenciales(
      paisId: paisId,
      correo: correo,
    )) {
      return;
    }
    if (!mounted) return;
    final activar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Huella dactilar'),
        content: Text(
          '¿Deseas habilitar el inicio de sesión con huella para '
          '${_paisSeleccionado?.nombre ?? 'este país'}?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Ahora no')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Activar')),
        ],
      ),
    );
    if (activar == true) {
      await auth.activarAccesoBiometrico(
        paisId: paisId,
        correo: correo,
        password: password,
        paisSimboloMoneda: _paisSeleccionado?.simboloMoneda,
      );
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
    final paisId = _paisIdSeleccionado;
    if (paisId == null || paisId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona tu país antes de ingresar')),
      );
      return;
    }
    if (correo.isEmpty || password.length < 4) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa usuario y contraseña (mínimo 4 caracteres)')),
      );
      return;
    }
    final ok = await context.read<AppState>().login(
          correo,
          password,
          paisId: paisId,
        );
    if (!mounted || !ok) return;
    await _ofrecerActivarHuella(correo, password, paisId);
    await _cargarTasasLogin();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  String _textoTasa(double? valor) {
    if (valor == null) return '—';
    return '${_fmtTasa.format(valor)} Bs';
  }

  Widget _selectorPais() {
    if (_cargandoPaises) {
      return const Padding(
        padding: EdgeInsets.only(bottom: 12),
        child: LinearProgressIndicator(minHeight: 2),
      );
    }
    if (_errorPaises != null) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          children: [
            Text(
              _errorPaises!,
              style: const TextStyle(color: Color(0xFFEF4444)),
              textAlign: TextAlign.center,
            ),
            TextButton(onPressed: _cargarPaises, child: const Text('Reintentar países')),
          ],
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField2<String>(
        value: _paisIdSeleccionado,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'País / región',
          prefixIcon: Icon(Icons.public_rounded),
        ),
        hint: const Text('Elige un país'),
        items: _paises
            .map(
              (p) => DropdownMenuItem<String>(
                value: p.id,
                child: Text(
                  p.etiquetaLista,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            )
            .toList(),
        onChanged: _alElegirPais,
        buttonStyleData: const ButtonStyleData(
          padding: EdgeInsets.only(right: 8),
        ),
        dropdownStyleData: DropdownStyleData(
          maxHeight: 280,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: const Color(0xFF0F172A),
          ),
        ),
        menuItemStyleData: const MenuItemStyleData(
          padding: EdgeInsets.symmetric(horizontal: 12),
        ),
      ),
    );
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
    final puedeIngresarPassword = _puedeIniciarSesion && !state.cargando;
    final puedeIngresarHuella = _puedeIngresarHuella && !state.cargando;

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
                    if (_paisSeleccionado?.esVenezuela ?? false) _panelTasas(),
                    GlassContainer(
                      accentColor: AppColors.neonBlue,
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          _selectorPais(),
                          if (!_cargandoPaises &&
                              _errorPaises == null &&
                              _paisIdSeleccionado == null &&
                              _paises.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: Text(
                                'Selecciona tu país para habilitar el ingreso.',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: AppColors.neonCyan,
                                    ),
                                textAlign: TextAlign.center,
                              ),
                            ),
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
                          if (_dispositivoConHuella) ...[
                            SizedBox(
                              width: double.infinity,
                              height: 56,
                              child: FilledButton.tonalIcon(
                                onPressed: puedeIngresarHuella ? _ingresarConBiometria : null,
                                icon: const Icon(Icons.fingerprint_rounded, size: 28),
                                label: const Text(
                                  'Ingresar con Huella',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ),
                            if (!_huellaHabilitada)
                              Padding(
                                padding: const EdgeInsets.only(top: 8, bottom: 4),
                                child: Text(
                                  'Tras tu primer ingreso con contraseña podrás activar la huella.',
                                  style: Theme.of(context).textTheme.bodySmall,
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            const SizedBox(height: 12),
                          ],
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: puedeIngresarPassword ? _login : null,
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
