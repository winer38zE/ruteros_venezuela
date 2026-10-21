import 'dart:convert';
import 'package:flutter/foundation.dart';
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
    String? paisSimboloMoneda,
  }) async {
    final usuarioNorm = correo.trim();
    final body = {
      'username': usuarioNorm,
      'password': '***',
      'pais_id': paisId,
    };
    if (kDebugMode) {
      debugPrint('[LOGIN] POST /auth/login body=$body');
    }
    final dynamic raw;
    try {
      raw = await _api.post('/auth/login', {
        'username': usuarioNorm,
        'password': password,
        'pais_id': paisId,
      });
    } on ApiException {
      rethrow;
    }
    final data = raw as Map<String, dynamic>;
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
        paisId: paisId,
        correo: usuarioNorm,
        password: password,
        paisSimboloMoneda: paisSimboloMoneda,
      );
    }

    if (guardarBiometria) {
      await activarAccesoBiometrico(
        paisId: paisId,
        correo: usuarioNorm,
        password: password,
        paisSimboloMoneda: paisSimboloMoneda,
      );
    }
    return user;
  }

  Future<void> _persistirAccesoSeguro({
    required String paisId,
    required String correo,
    required String password,
    String? paisSimboloMoneda,
  }) async {
    await _biometric.guardarCredenciales(
      paisId: paisId,
      correo: correo,
      password: password,
      paisSimboloMoneda: paisSimboloMoneda,
    );
    if (_api.token != null &&
        _api.usuarioId != null &&
        _api.usuarioJson != null) {
      await _biometric.guardarSesion(
        paisId: paisId,
        correo: correo,
        token: _api.token!,
        usuarioId: _api.usuarioId!,
        usuarioJson: _api.usuarioJson!,
      );
    }
  }

  /// Guarda credenciales cifradas para [paisId] + [correo] (contraseña en secure storage).
  /// Migración a token de dispositivo: pendiente en backend; hoy se guarda la contraseña.
  Future<void> activarAccesoBiometrico({
    required String paisId,
    required String correo,
    required String password,
    String? paisSimboloMoneda,
  }) async {
    await _persistirAccesoSeguro(
      paisId: paisId,
      correo: correo,
      password: password,
      paisSimboloMoneda: paisSimboloMoneda,
    );
  }

  Future<bool> tieneDatosBiometricosGuardados({
    required String paisId,
    String? correo,
  }) async {
    return _biometric.tieneCredenciales(paisId: paisId, correo: correo);
  }

  Future<Usuario?> loginConBiometria({
    required String paisIdSeleccionado,
    String? correoHint,
  }) async {
    final paisId = paisIdSeleccionado.trim();
    if (paisId.isEmpty) {
      throw StateError('Selecciona tu país antes de usar la huella.');
    }

    if (!await _biometric.tieneCredenciales(
      paisId: paisId,
      correo: correoHint,
    )) {
      throw BiometricStorageEmptyException();
    }

    final resultado = await _biometric.autenticarDetallado();
    switch (resultado) {
      case BiometricAuthResult.success:
        break;
      case BiometricAuthResult.canceled:
        return null;
      case BiometricAuthResult.notEnrolled:
        throw BiometricUserFacingException(
          'No hay huellas registradas en este teléfono. Configúralas en Ajustes o usa contraseña.',
        );
      case BiometricAuthResult.notAvailable:
        throw BiometricUserFacingException(
          'Biometría no disponible en este dispositivo. Usa contraseña.',
        );
      case BiometricAuthResult.lockedOut:
        throw BiometricUserFacingException(
          'Demasiados intentos fallidos. Espera un momento o usa contraseña.',
        );
      case BiometricAuthResult.permanentlyLockedOut:
        throw BiometricUserFacingException(
          'Biometría bloqueada. Desbloquea el teléfono con PIN/patrón e intenta de nuevo, o usa contraseña.',
        );
      case BiometricAuthResult.failed:
        return null;
    }

    final credenciales = await _biometric.leerCredenciales(
      paisId: paisId,
      correo: correoHint,
    );
    if (credenciales == null) {
      throw BiometricStorageEmptyException();
    }

    try {
      return await login(
        credenciales.correo,
        credenciales.password,
        paisId: paisId,
        persistirCredenciales: false,
      );
    } on ApiException catch (e) {
      if (e.statusCode == 401 || e.statusCode == 403) {
        throw BiometricUserFacingException(
          'Tu sesión guardada ya no es válida para este país. Ingresa con contraseña.',
        );
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

  Future<Usuario?> restoreSession() async {
    await _api.loadSession();
    if (!_api.hasSession || _api.usuarioJson == null) return null;
    try {
      final user = Usuario.fromJson(jsonDecode(_api.usuarioJson!));
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

class BiometricStorageEmptyException implements Exception {
  @override
  String toString() =>
      'Tras tu primer ingreso con contraseña podrás activar la huella para este país.';
}

class BiometricUserFacingException implements Exception {
  BiometricUserFacingException(this.message);
  final String message;
  @override
  String toString() => message;
}
