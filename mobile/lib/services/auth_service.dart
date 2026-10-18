import 'dart:convert';
import '../models/pais_region.dart';
import '../services/api_service.dart';
import 'biometric_service.dart';
import 'region_session_service.dart';

class Usuario {
  final String id;
  final String nombre;
  final String username;
  final String rol;
  final String empresaId;
  final String? paisId;
  final PaisRegion? pais;

  /// Alias para compatibilidad con utilidades de región.
  PaisRegion? get paisRegion => pais;

  Usuario({
    required this.id,
    required this.nombre,
    required this.username,
    required this.rol,
    required this.empresaId,
    this.paisId,
    this.pais,
  });

  factory Usuario.fromJson(Map<String, dynamic> j) {
    PaisRegion? pais;
    final rawPais = j['pais'];
    if (rawPais is Map<String, dynamic>) {
      pais = PaisRegion.fromJson(rawPais);
    }
    return Usuario(
      id: j['id'],
      nombre: j['nombre'],
      username: j['username'],
      rol: j['rol'],
      empresaId: j['empresa_id'],
      paisId: j['pais_id'] as String?,
      pais: pais,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'username': username,
        'rol': rol,
        'empresa_id': empresaId,
        if (paisId != null) 'pais_id': paisId,
        if (pais != null) 'pais': pais!.toJson(),
      };

  bool get esDueno => rol == 'DUEÑO' || rol.toLowerCase() == 'owner';
  bool get esAdministrador => rol == 'ADMINISTRADOR';
  bool get puedeOperaciones => esDueno || esAdministrador;

  /// RBAC de la app: dueño con acceso total, el resto es panel de empleado.
  String get rolAcceso => esDueno ? 'owner' : 'employee';
  bool get esOwner => rolAcceso == 'owner';
}

class AuthService {
  AuthService(
    this._api, {
    BiometricService? biometric,
    RegionSessionService? regionSession,
  })  : _biometric = biometric ?? BiometricService(),
        _regionSession = regionSession ?? RegionSessionService();

  final ApiService _api;
  final BiometricService _biometric;
  final RegionSessionService _regionSession;

  BiometricService get biometric => _biometric;
  RegionSessionService get regionSession => _regionSession;

  Future<Usuario> login(
    String correo,
    String password, {
    required String paisId,
    bool guardarBiometria = false,
  }) async {
    final usuarioNorm = correo.trim();
    final data = await _api.post('/auth/login', {
      'username': usuarioNorm,
      'password': password,
      'pais_id': paisId,
    });
    final user = Usuario.fromJson(data);
    await _api.saveSession(
      token: user.id,
      usuarioId: user.id,
      usuarioJson: jsonEncode(user.toJson()),
    );

    if (user.pais != null) {
      await _regionSession.guardar(user.pais!);
    }

    final simbolo = user.pais?.simboloMoneda;
    await _persistirAccesoSeguro(
      correo: usuarioNorm,
      password: password,
      paisId: paisId,
      simboloMoneda: simbolo,
    );

    if (guardarBiometria) {
      await activarAccesoBiometrico(
        correo: usuarioNorm,
        password: password,
        paisId: paisId,
        simboloMoneda: simbolo,
      );
    }
    return user;
  }

  /// Credenciales y sesión en flutter_secure_storage (base para huella).
  Future<void> _persistirAccesoSeguro({
    required String correo,
    required String password,
    required String paisId,
    String? simboloMoneda,
  }) async {
    await _biometric.guardarCredenciales(
      correo: correo,
      password: password,
      paisId: paisId,
      simboloMoneda: simboloMoneda,
    );
    if (_api.token != null &&
        _api.usuarioId != null &&
        _api.usuarioJson != null) {
      await _biometric.guardarSesion(
        token: _api.token!,
        usuarioId: _api.usuarioId!,
        usuarioJson: _api.usuarioJson!,
      );
    }
  }

  /// Guarda credenciales + token de sesión cifrados (tras confirmar huella).
  Future<void> activarAccesoBiometrico({
    required String correo,
    required String password,
    String? paisId,
    String? simboloMoneda,
  }) async {
    final pid = paisId ?? await _biometric.leerPaisLoginId();
    if (pid == null || pid.isEmpty) {
      throw StateError('Falta el país de la sesión para activar la huella.');
    }
    final simbolo =
        simboloMoneda ?? await _biometric.leerPaisSimboloMoneda();
    await _persistirAccesoSeguro(
      correo: correo,
      password: password,
      paisId: pid,
      simboloMoneda: simbolo,
    );
  }

  Future<Usuario?> _restaurarSesionDesdeAlmacenSeguro() async {
    final sesion = await _biometric.leerSesion();
    if (sesion == null) return null;
    await _api.saveSession(
      token: sesion.token,
      usuarioId: sesion.usuarioId,
      usuarioJson: sesion.usuarioJson,
    );
    try {
      final user = Usuario.fromJson(jsonDecode(sesion.usuarioJson));
      if (user.pais != null) {
        await _regionSession.guardar(user.pais!);
      }
      return user;
    } catch (_) {
      await _biometric.borrarSesionSegura();
      return null;
    }
  }

  /// True si hay credenciales o sesión cifrada para re-ingresar con huella.
  Future<bool> tieneDatosBiometricosGuardados() async {
    return (await _biometric.tieneSesionSegura()) ||
        (await _biometric.tieneCredenciales());
  }

  /// Huella válida → lee almacén seguro → sesión o login en API.
  Future<Usuario?> loginConBiometria() async {
    if (!await tieneDatosBiometricosGuardados()) {
      throw BiometricStorageEmptyException();
    }

    final ok = await _biometric.autenticar();
    if (!ok) return null;

    final restaurado = await _restaurarSesionDesdeAlmacenSeguro();
    if (restaurado != null) {
      await _sincronizarRegionDesdeAlmacenSeguro(restaurado);
      return restaurado;
    }

    final credenciales = await _biometric.leerCredenciales();
    if (credenciales == null) {
      throw BiometricStorageEmptyException();
    }
    final paisId = await _biometric.leerPaisLoginId();
    if (paisId == null || paisId.isEmpty) {
      throw BiometricStorageEmptyException();
    }
    try {
      final user = await login(
        credenciales.correo,
        credenciales.password,
        paisId: paisId,
      );
      await _sincronizarRegionDesdeAlmacenSeguro(user);
      return user;
    } on ApiException catch (e) {
      if (e.statusCode == 401 || e.statusCode == 403 || e.statusCode == 429) {
        await _invalidarSesionLocal();
      }
      if (e.statusCode == 502 || e.statusCode == 503 || e.statusCode == 504) {
        throw ApiException(
          e.statusCode,
          'Servidor no disponible (${e.statusCode}). Pulsa Reintentar.',
        );
      }
      rethrow;
    }
  }

  /// Asegura moneda/región cuando la sesión cifrada no trae `pais` completo.
  Future<void> _sincronizarRegionDesdeAlmacenSeguro(Usuario user) async {
    if (user.pais != null) {
      await _regionSession.guardar(user.pais!);
      return;
    }
    final pid = await _biometric.leerPaisLoginId();
    final simbolo = await _biometric.leerPaisSimboloMoneda();
    if (pid == null || pid.isEmpty) return;
    await _regionSession.guardar(
      PaisRegion(
        id: pid,
        nombre: user.pais?.nombre ?? '',
        codigoIso: user.pais?.codigoIso ?? '',
        monedaPrincipal: user.pais?.monedaPrincipal ?? '',
        simboloMoneda: simbolo ?? user.pais?.simboloMoneda ?? 'Bs.',
      ),
    );
  }

  Future<void> _invalidarSesionLocal() async {
    await _biometric.borrarTodoAccesoBiometrico();
    await _api.clearSession();
    await _regionSession.limpiar();
  }

  Future<Usuario?> restoreSession() async {
    await _api.loadSession();
    if (!_api.hasSession || _api.usuarioJson == null) return null;
    try {
      final user = Usuario.fromJson(jsonDecode(_api.usuarioJson!));
      _api.setUsuarioId(user.id);
      if (user.pais != null) {
        await _regionSession.guardar(user.pais!);
      }
      return user;
    } catch (_) {
      await _api.clearSession();
      return null;
    }
  }

  Future<void> logout({bool borrarAccesoBiometrico = false}) async {
    if (borrarAccesoBiometrico) {
      await _biometric.borrarTodoAccesoBiometrico();
    }
    await _regionSession.limpiar();
    await _api.clearSession();
  }
}

/// Almacén seguro vacío: hace falta un login manual previo.
class BiometricStorageEmptyException implements Exception {
  @override
  String toString() =>
      'Por favor, inicia sesión con tu usuario y contraseña por primera vez para activar la huella';
}
