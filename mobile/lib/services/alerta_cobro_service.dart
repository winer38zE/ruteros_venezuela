import 'package:flutter/foundation.dart';
import 'package:isar/isar.dart';

import '../local/cliente_local.dart';
import '../local/credito_local.dart';
import '../local/isar_db.dart';
import 'api_service.dart';
import 'cobros_service.dart';
import 'notification_service.dart';

/// Revisa cuotas guardadas en el teléfono y avisa al cobrador.
class AlertaCobroService {
  AlertaCobroService(this._api, this._avisos);

  final ApiService _api;
  final NotificationService _avisos;

  static const _diasPorVencer = 2;

  Future<void> revisar() async {
    final isar = isarInstance;
    if (isar == null || !isar.isOpen) return;
    await _avisos.requestPermission();
    await _bajarCartera(isar);
    final alertas = await _evaluarVencimientos(isar);
    await _disparar(isar, alertas);
  }

  Future<void> limpiar() async {
    final isar = isarInstance;
    if (isar != null && isar.isOpen) {
      await isar.writeTxn(() async {
        await isar.creditoLocals.clear();
      });
    }
    await _avisos.cancelarTodas();
  }

  Future<void> _bajarCartera(Isar isar) async {
    if (!_api.hasSession) return;
    try {
      final filas = await CobrosService(_api).panelCobranza();
      final ids = <String>{};
      await isar.writeTxn(() async {
        for (final fila in filas) {
          ids.add(fila.id);
          final previa = await isar.creditoLocals.filter().ventaIdEqualTo(fila.id).findFirst();
          final pagado = fila.estado == 'pagada' || fila.saldoPendienteUsd <= 0.01;
          final credito = CreditoLocal()
            ..ventaId = fila.id
            ..clienteId = fila.clienteId
            ..clienteNombre = fila.clienteNombre
            ..fechaVencimiento = DateTime.tryParse(fila.proximoPago ?? '')?.toUtc()
            ..saldo = fila.saldoPendienteUsd
            ..estado = pagado ? 'pagado' : 'pendiente'
            ..ultimoAviso = previa?.ultimoAviso;
          await isar.creditoLocals.put(credito);
        }
        final guardados = await isar.creditoLocals.where().findAll();
        for (final credito in guardados) {
          if (!ids.contains(credito.ventaId) && credito.estado != 'pagado') {
            credito.estado = 'pagado';
            await isar.creditoLocals.put(credito);
          }
        }
      });
    } catch (e, st) {
      debugPrint('Cartera local sin actualizar. Se usan los vencimientos ya guardados. $e\n$st');
    }
  }

  /// Si la fecha ya pasó y el crédito no está pagado, queda vencido y el cliente moroso.
  Future<List<CreditoLocal>> _evaluarVencimientos(Isar isar) async {
    final hoy = _soloFecha(DateTime.now());
    final limite = hoy.add(const Duration(days: _diasPorVencer));
    final creditos = await isar.creditoLocals.where().findAll();
    final paraAvisar = <CreditoLocal>[];
    final vencidosPorCliente = <String>{};

    await isar.writeTxn(() async {
      for (final credito in creditos) {
        if (_pagado(credito.estado)) {
          if (credito.estado != 'pagado') {
            credito.estado = 'pagado';
            await isar.creditoLocals.put(credito);
          }
          continue;
        }
        final fecha = credito.fechaVencimiento;
        if (fecha == null) continue;
        final dia = _soloFecha(fecha);
        if (dia.isBefore(hoy)) {
          credito.estado = 'vencido';
          await isar.creditoLocals.put(credito);
          final clienteId = credito.clienteId;
          if (clienteId != null && clienteId.isNotEmpty) vencidosPorCliente.add(clienteId);
          paraAvisar.add(credito);
        } else if (!dia.isAfter(limite)) {
          paraAvisar.add(credito);
        }
      }

      final clientes = await isar.clienteLocals.where().findAll();
      for (final cliente in clientes) {
        final id = cliente.servidorId;
        final vencido = id != null && vencidosPorCliente.contains(id);
        if (cliente.creditoVencido == vencido && (!vencido || cliente.esMoroso == true)) {
          continue;
        }
        cliente.creditoVencido = vencido;
        if (vencido) cliente.esMoroso = true;
        await isar.clienteLocals.put(cliente);
      }
    });

    return paraAvisar;
  }

  Future<void> _disparar(Isar isar, List<CreditoLocal> alertas) async {
    final hoy = _soloFecha(DateTime.now());
    for (final credito in alertas) {
      final aviso = credito.ultimoAviso;
      if (aviso != null && _soloFecha(aviso) == hoy) continue;
      final nombre = (credito.clienteNombre ?? '').trim();
      final cliente = nombre.isEmpty ? 'Un cliente' : nombre;
      final vencido = credito.estado == 'vencido';
      final titulo = vencido
          ? '⚠️ Alerta de Cobro: $cliente tiene un crédito vencido'
          : '⚠️ Alerta de Cobro: $cliente vence en los próximos 2 días';
      final cuerpo = vencido
          ? 'Visítalo de prioridad en la ruta de hoy.'
          : 'La cuota está por vencer. Conviene pasarlo en la ruta.';
      final id = _idAviso(credito.ventaId);
      try {
        await _avisos.mostrar(id: id, titulo: titulo, cuerpo: cuerpo);
        await _avisos.programarManana(id: id + 1, titulo: titulo, cuerpo: cuerpo);
      } catch (e, st) {
        debugPrint('Alerta no enviada. $e\n$st');
        continue;
      }
      await isar.writeTxn(() async {
        credito.ultimoAviso = DateTime.now().toUtc();
        await isar.creditoLocals.put(credito);
      });
    }
  }

  bool _pagado(String estado) {
    final valor = estado.toLowerCase();
    return valor == 'pagado' || valor == 'pagada';
  }

  DateTime _soloFecha(DateTime fecha) {
    final local = fecha.toLocal();
    return DateTime(local.year, local.month, local.day);
  }

  int _idAviso(String ventaId) => ventaId.hashCode & 0x3fffffff;
}
