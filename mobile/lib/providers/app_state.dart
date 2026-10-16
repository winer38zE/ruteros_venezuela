import 'dart:async';

import 'package:flutter/foundation.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/contabilidad_service.dart';
import '../services/inventario_service.dart';
import '../services/catalogo_service.dart';
import '../services/ventas_service.dart';
import '../services/cobros_service.dart';
import '../services/cartera_critica_service.dart';
import '../services/finanzas_service.dart';
import '../services/usuarios_service.dart';
import '../services/proveedores_service.dart';
import '../services/clientes_service.dart';
import '../services/tasas_service.dart';
import '../services/rutas_service.dart';
import '../services/empresa_service.dart';
import '../services/whatsapp_service.dart';
import '../services/sync_service.dart';
import '../services/alerta_cobro_service.dart';
import '../services/notification_service.dart';

class AppState extends ChangeNotifier {
  AppState() {
    auth = AuthService(api);
    contabilidad = ContabilidadService(api);
    inventario = InventarioService(api);
    productos = ProductosService(api);
    catalogo = CatalogoService(api);
    ventas = VentasService(api);
    cobros = CobrosService(api);
    carteraCritica = CarteraCriticaService(api);
    finanzas = FinanzasService(api);
    usuarios = UsuariosService(api);
    proveedores = ProveedoresService(api);
    clientes = ClientesService(api);
    tasas = TasasService(api);
    rutas = RutasService(api);
    empresas = EmpresaService(api);
    whatsapp = WhatsappService(api);
    sync = SyncService(api);
    alertas = AlertaCobroService(api, NotificationService.instance);
    sync.alTerminar = alertas.revisar;
    unawaited(sync.escucharRed());
    _inicializar();
  }

  final ApiService api = ApiService();
  late final AuthService auth;
  late final ContabilidadService contabilidad;
  late final InventarioService inventario;
  late final ProductosService productos;
  late final CatalogoService catalogo;
  late final VentasService ventas;
  late final CobrosService cobros;
  late final CarteraCriticaService carteraCritica;
  late final FinanzasService finanzas;
  late final UsuariosService usuarios;
  late final ProveedoresService proveedores;
  late final ClientesService clientes;
  late final TasasService tasas;
  late final RutasService rutas;
  late final EmpresaService empresas;
  late final WhatsappService whatsapp;
  late final SyncService sync;
  late final AlertaCobroService alertas;

  Usuario? usuario;
  bool inicializado = false;
  bool cargando = false;
  String? error;

  bool get esVendedor => usuario?.rol == 'VENDEDOR';
  bool get esCobrador => usuario?.rol == 'COBRADOR';
  bool get esAdministrador => usuario?.rol == 'ADMINISTRADOR';
  bool get esDueno => usuario?.esDueno ?? false;
  bool get puedeOperaciones => esDueno || esAdministrador;
  bool get puedeVender => esVendedor || puedeOperaciones;
  bool get puedeCobrar => esCobrador || puedeOperaciones;
  bool get puedeConfigurar => esDueno;
  String get rolAcceso => usuario?.rolAcceso ?? 'employee';
  bool get esOwner => usuario?.esOwner ?? false;

  Future<void> _inicializar() async {
    try {
      usuario = await auth.restoreSession();
      if (usuario != null) _arrancarSync();
    } catch (_) {
      usuario = null;
    } finally {
      inicializado = true;
      notifyListeners();
    }
  }

  Future<bool> login(
    String correo,
    String password, {
    bool guardarBiometria = false,
  }) async {
    cargando = true;
    error = null;
    notifyListeners();
    try {
      usuario = await auth.login(
        correo,
        password,
        guardarBiometria: guardarBiometria,
      );
      if (usuario != null) _arrancarSync();
      return usuario != null;
    } catch (e) {
      error = e is ApiException ? e.message : e.toString();
      usuario = null;
      return false;
    } finally {
      cargando = false;
      notifyListeners();
    }
  }

  Future<void> loginConBiometria() async {
    cargando = true;
    error = null;
    notifyListeners();
    try {
      final user = await auth.loginConBiometria();
      if (user == null) {
        error = 'No hay credenciales guardadas para huella dactilar.';
        usuario = null;
        return;
      }
      usuario = user;
      _arrancarSync();
    } catch (e) {
      error = e is ApiException ? e.message : e.toString();
      usuario = null;
      if (e is ApiException &&
          (e.statusCode == 401 || e.statusCode == 403 || e.statusCode == 429)) {
        error = 'Sesión expirada. Ingresa con contraseña.';
      }
    } finally {
      cargando = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await sync.dejarDeEscuchar();
    await alertas.limpiar();
    await sync.limpiarLocal();
    await auth.logout();
    usuario = null;
    notifyListeners();
  }

  void _arrancarSync() {
    sync.escucharRed();
    unawaited(sync.sincronizar());
  }
}
