import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

/// Avisos locales del cobrador. Si el teléfono no tiene el canal, la app sigue.
class NotificationService {
  NotificationService._();

  static final NotificationService instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  bool disponible = false;
  bool _permisoPedido = false;
  bool _zonasListas = false;

  static const _canal = AndroidNotificationDetails(
    'alertas_cobro',
    'Alertas de cobro',
    channelDescription: 'Créditos vencidos y próximos a vencer en la ruta',
    importance: Importance.high,
    priority: Priority.high,
  );

  Future<void> iniciar() async {
    if (!_plataformaMovil) return;
    try {
      _prepararZonas();
      const android = AndroidInitializationSettings('@mipmap/ic_launcher');
      const ios = DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      );
      await _plugin.initialize(const InitializationSettings(android: android, iOS: ios));
      disponible = true;
    } catch (e, st) {
      debugPrint('Notificaciones no disponibles. La app sigue. $e\n$st');
      disponible = false;
    }
  }

  bool get _plataformaMovil {
    if (kIsWeb) return false;
    return Platform.isAndroid || Platform.isIOS;
  }

  void _prepararZonas() {
    if (_zonasListas) return;
    tzdata.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('America/Bogota'));
    _zonasListas = true;
  }

  /// Pide el permiso en el momento, antes de programar alertas.
  Future<bool> requestPermission() async {
    if (!disponible || _permisoPedido) return disponible;
    _permisoPedido = true;
    try {
      final android = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
      if (android != null) {
        final avisos = await android.requestNotificationsPermission();
        try {
          await android.requestExactAlarmsPermission();
        } catch (e) {
          debugPrint('Alarma exacta no concedida. $e');
        }
        return avisos ?? false;
      }
      final ios = _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();
      if (ios != null) {
        return await ios.requestPermissions(alert: true, badge: true, sound: true) ?? false;
      }
    } catch (e, st) {
      debugPrint('No se pudo pedir permiso de notificación. $e\n$st');
    }
    return false;
  }

  Future<void> mostrar({
    required int id,
    required String titulo,
    required String cuerpo,
  }) async {
    if (!disponible) return;
    const detalles = NotificationDetails(
      android: _canal,
      iOS: DarwinNotificationDetails(),
    );
    await _plugin.show(id, titulo, cuerpo, detalles);
  }

  /// Respaldo a las 8:00 de Cúcuta del día siguiente, por si el teléfono se reinicia.
  Future<void> programarManana({
    required int id,
    required String titulo,
    required String cuerpo,
  }) async {
    if (!disponible) return;
    try {
      _prepararZonas();
      final cuando = _ochoDeManana();
      await _plugin.zonedSchedule(
        id,
        titulo,
        cuerpo,
        cuando,
        const NotificationDetails(
          android: _canal,
          iOS: DarwinNotificationDetails(),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
      );
    } catch (e, st) {
      debugPrint('No se pudo programar la alerta. $e\n$st');
    }
  }

  tz.TZDateTime _ochoDeManana() {
    final zona = tz.getLocation('America/Bogota');
    final ahora = tz.TZDateTime.now(zona);
    final manana = ahora.add(const Duration(days: 1));
    return tz.TZDateTime(zona, manana.year, manana.month, manana.day, 8);
  }

  Future<void> cancelarTodas() async {
    if (!disponible) return;
    try {
      await _plugin.cancelAll();
    } catch (e) {
      debugPrint('No se pudieron cancelar las alertas. $e');
    }
  }
}
