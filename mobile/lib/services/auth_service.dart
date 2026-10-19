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
    bool persistirCredenciales = true,
  }) async {
    final usuarioNorm = correo.trim();
    final data = await _api.post('/auth/login', {
      'username': usuarioNorm,
      'password': password,
      'pais_id': paisId,
    });
    final user = Usuario.fromJson(data);
    final jwt = (data['access_token'] as String?)?.trim();
    await _api.saveSession(
      token: (jwt != null && jwt.isNotEmpty) ? jwt : user.id,
      usuarioId: user.id,
      usuarioJson: jsonEncode(user.toJson()),
    );

    if (user.pais != null) {
      await _regionSession.guardar(user.pais!);
    }

    if (persistirCredenciales) {
      await _persistirAccesoSeguro(
        correo: usuarioNorm,
        password: password,
      );
    }

    if (guardarBiometria) {
      await activarAccesoBiometrico(
        correo: usuarioNorm,
        password: password,
      );
    }
    return user;
  }

  /// Credenciales base (huella) + copia opcional de sesión API.
  Future<void> _persistirAccesoSeguro({
    required String correo,
    required String password,
  }) async {
    await _biometric.guardarCredenciales(
      correo: correo,
      password: password,
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
  }) async {
    await _persistirAccesoSeguro(
      correo: correo,
      password: password,
    );
  }

  /// True si hay credenciales base para re-ingresar con huella.
  Future<bool> tieneDatosBiometricosGuardados() async {
    return _biometric.tieneCredenciales();
  }

  /// Huella válida → credenciales del almacén + [paisIdSeleccionado] del dropdown → login API.
  Future<Usuario?> loginConBiometria({String? paisIdSeleccionado}) async {
    if (!await _biometric.tieneCredenciales()) {
      throw BiometricStorageEmptyException();
    }

    final ok = await _biometric.autenticar();
    if (!ok) return null;

    final credenciales = await _biometric.leerCredenciales();
    if (credenciales == null) {
      throw BiometricStorageEmptyException();
    }

    final paisId = paisIdSeleccionado?.trim();
    if (paisId == null || paisId.isEmpty) {
      throw StateError('Selecciona tu país antes de usar la huella.');
    }
    try {
      return await login(
        credenciales.correo,
        credenciales.password,
        paisId: paisId,
        persistirCredenciales: false,
      );
    } on ApiException catch (e) {
      // No borrar flutter_secure_storage: credenciales siguen válidas para otro país.
      if (e.statusCode == 502 || e.statusCode == 503 || e.statusCode == 504) {
        throw ApiException(
          e.statusCode,
          'Servidor no disponible (${e.statusCode}). Pulsa Reintentar.',
        );
      }
      rethrow;
    }
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
