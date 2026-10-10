import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:isar/isar.dart';
import 'package:uuid/uuid.dart';

import '../local/cliente_local.dart';
import '../local/isar_db.dart';
import 'api_service.dart';

/// Sube clientes pendientes y baja `es_moroso` y `score` calculados en el servidor.
class SyncService {
  SyncService(this._api);

  final ApiService _api;
  final Connectivity _conectividad = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _redSub;
  bool _enCurso = false;

  static const _lote = 200;
  static final _uuid = Uuid();

  void escucharRed() {
    _redSub ??= _conectividad.onConnectivityChanged.listen((results) {
      if (_hayResultado(results)) {
        sincronizar();
      }
    });
  }

  Future<void> dejarDeEscuchar() async {
    await _redSub?.cancel();
    _redSub = null;
  }

  Future<bool> hayRed() async {
    try {
      return _hayResultado(await _conectividad.checkConnectivity());
    } catch (_) {
      return true;
    }
  }

  bool _hayResultado(List<ConnectivityResult> results) {
    return results.any((r) => r != ConnectivityResult.none);
  }

  /// Guarda un alta nueva cuando el servidor no responde. No inventa score ni mora.
  Future<bool> encolarNuevo(Map<String, dynamic> body) async {
    final isar = isarInstance;
    if (isar == null || !isar.isOpen) return false;
    final limpio = Map<String, dynamic>.from(body)
      ..remove('score')
      ..remove('score_credito')
      ..remove('es_moroso')
      ..remove('estado_morosidad');
    final local = ClienteLocal()
      ..nombre = limpio['nombre_completo']?.toString()
      ..cedula = limpio['identificacion']?.toString()
      ..telefono = limpio['telefono']?.toString()
      ..direccion = limpio['direccion']?.toString()
      ..esMoroso = false
      ..score = null
      ..sincronizado = false
      ..clave = _uuid.v4()
      ..payloadJson = jsonEncode(limpio)
      ..errorSync = null;
    await isar.writeTxn(() async {
      await isar.clienteLocals.put(local);
    });
    return true;
  }

  Future<void> limpiarLocal() async {
    final isar = isarInstance;
    if (isar == null || !isar.isOpen) return;
    await isar.writeTxn(() async {
      await isar.clienteLocals.clear();
    });
  }

  Stream<List<ClienteLocal>> observarClientes() {
    final isar = isarInstance;
    if (isar == null || !isar.isOpen) {
      return const Stream.empty();
    }
    return isar.clienteLocals.where().watch(fireImmediately: true);
  }

  /// [manual] reintenta también los que el servidor ya rechazó.
  Future<void> sincronizar({bool manual = false}) async {
    if (_enCurso) return;
    final isar = isarInstance;
    if (isar == null || !isar.isOpen) {
      if (manual) {
        throw ApiException(0, 'La base local no está disponible.');
      }
      return;
    }
    if (!_api.hasSession) return;
    if (!await hayRed()) {
      if (manual) {
        throw ApiException(0, 'Sin conexión. Los clientes siguen guardados en el teléfono.');
      }
      return;
    }

    _enCurso = true;
    try {
      final pendientes = await isar.clienteLocals.filter().sincronizadoEqualTo(false).findAll();
      final aEnviar = manual
          ? pendientes
          : pendientes.where((c) => c.errorSync == null || c.errorSync!.isEmpty).toList();
      if (aEnviar.isEmpty) {
        final data = await _api.post(
          '/clientes/sincronizar',
          {'clientes': <Map<String, dynamic>>[]},
          timeout: const Duration(seconds: 60),
        );
        await _aplicarRespuesta(isar, data);
        return;
      }
      for (var i = 0; i < aEnviar.length; i += _lote) {
        final fin = i + _lote > aEnviar.length ? aEnviar.length : i + _lote;
        final data = await _api.post(
          '/clientes/sincronizar',
          {'clientes': aEnviar.sublist(i, fin).map(_item).toList()},
          timeout: const Duration(seconds: 60),
        );
        await _aplicarRespuesta(isar, data);
      }
    } catch (e, st) {
      debugPrint('Sync de clientes falló. $e\n$st');
      if (manual) rethrow;
    } finally {
      _enCurso = false;
    }
  }

  Map<String, dynamic> _item(ClienteLocal cliente) {
    Map<String, dynamic> body = {};
    final crudo = cliente.payloadJson;
    if (crudo != null && crudo.isNotEmpty) {
      final decoded = jsonDecode(crudo);
      if (decoded is Map) {
        body = Map<String, dynamic>.from(decoded);
      }
    }
    body.remove('score');
    body.remove('score_credito');
    body.remove('es_moroso');
    body.remove('estado_morosidad');
    body['local_id'] = cliente.clave;
    if (cliente.servidorId != null && cliente.servidorId!.isNotEmpty) {
      body['backend_id'] = cliente.servidorId;
    }
    body['nombre_completo'] ??= cliente.nombre;
    body['identificacion'] ??= cliente.cedula;
    return body;
  }

  Future<void> _aplicarRespuesta(Isar isar, dynamic data) async {
    if (data is! Map) return;
    final mapa = Map<String, dynamic>.from(data);
    final resultados = (mapa['resultados'] as List?) ?? const [];
    final clientes = (mapa['clientes'] as List?) ?? const [];

    await isar.writeTxn(() async {
      for (final crudo in resultados) {
        if (crudo is! Map) continue;
        final r = Map<String, dynamic>.from(crudo);
        final localId = r['local_id']?.toString() ?? '';
        if (localId.isEmpty) continue;
        final pendiente = await isar.clienteLocals.filter().claveEqualTo(localId).findFirst();
        if (pendiente == null) continue;
        final accion = r['accion']?.toString() ?? '';
        if (accion == 'creado' || accion == 'existente' || accion == 'actualizado') {
          await isar.clienteLocals.delete(pendiente.id);
          continue;
        }
        pendiente.errorSync = r['detalle']?.toString() ?? 'No se pudo sincronizar';
        pendiente.esMoroso = r['es_moroso'] == true;
        final score = r['score'];
        if (score is num) pendiente.score = score.toInt();
        await isar.clienteLocals.put(pendiente);
      }

      for (final crudo in clientes) {
        if (crudo is! Map) continue;
        final j = Map<String, dynamic>.from(crudo);
        final servidorId = j['id']?.toString() ?? '';
        if (servidorId.isEmpty) continue;
        final estado = (j['estado_morosidad'] ?? 'al_dia').toString();
        final scoreRaw = j['score_credito'] ?? j['score'];
        final fila = ClienteLocal()
          ..nombre = j['nombre']?.toString()
          ..cedula = j['identificacion']?.toString()
          ..telefono = j['telefono']?.toString()
          ..direccion = j['direccion']?.toString()
          ..esMoroso = j['es_moroso'] == true || estado == 'moroso'
          ..score = scoreRaw is num ? scoreRaw.toInt() : int.tryParse('$scoreRaw')
          ..servidorId = servidorId
          ..sincronizado = true
          ..clave = servidorId
          ..payloadJson = null
          ..errorSync = null;
        await isar.clienteLocals.put(fila);
      }
    });
  }
}
