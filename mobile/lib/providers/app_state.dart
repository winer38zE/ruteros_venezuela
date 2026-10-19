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
import '../services/tasas_login_cache.dart';
import '../services/rutas_service.dart';
import '../services/empresa_service.dart';
import '../services/whatsapp_service.dart';
import '../services/sync_service.dart';
import '../services/alerta_cobro_service.dart';
import '../services/notification_service.dart';
import '../services/paises_service.dart';
import '../services/perfil_service.dart';
import '../services/region_session_service.dart';
import '../models/pais_region.dart';

class AppState extends ChangeNotifier {
  AppState() {
    auth = AuthService(api, regionSession: regionSession);
    paises = PaisesService(api);
    perfil = PerfilService(api);
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
  late final PaisesService paises;
  late final PerfilService perfil;
  final RegionSessionService regionSession = RegionSessionService();
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
  PaisRegion? region;
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

  /// País de la sesión (login o región persistida).
  bool get esVenezuela {
    final pais = region ?? usuario?.pais;
    return pais?.esVenezuela ?? false;
  }

  Future<void> _inicializar() async {
    try {
      region = await regionSession.leer();
      usuario = await auth.restoreSession();
      region ??= usuario?.pais;
      if (usuario != null) _arrancarSync();
    } catch (_) {
      usuario = null;
    } finally {
      inicializado = true;
      notifyListeners();
    }
  }

  String get simboloMoneda => region?.simboloMoneda ?? 'Bs.';
  String get monedaPrincipal => region?.monedaPrincipal ?? 'VES';

  /// Símbolo persistido en login (secure storage) si la región aún no cargó.
  Future<String> simboloMonedaPersistido() async {
    if (region != null && region!.simboloMoneda.isNotEmpty) {
      return region!.simboloMoneda;
    }
    final guardado = await auth.biometric.leerPaisSimboloMoneda();
    return guardado ?? simboloMoneda;
  }

  Future<bool> login(
    String correo,
    String password, {
    required String paisId,
    bool guardarBiometria = false,
  }) async {
    cargando = true;
    error = null;
    notifyListeners();
    try {
      usuario = await auth.login(
        correo,
        password,
        paisId: paisId,
        guardarBiometria: guardarBiometria,
      );
      if (usuario != null) {
        region = usuario!.pais ?? region;
        if (region != null) {
          await regionSession.guardar(region!);
        }
        _arrancarSync();
        unawaited(_actualizarCacheTasasLogin());
      }
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

  Future<bool> loginConBiometria({String? paisIdSeleccionado}) async {
    cargando = true;
    error = null;
    notifyListeners();
    try {
      final user = await auth.loginConBiometria(
        paisIdSeleccionado: paisIdSeleccionado,
      );
      if (user == null) {
        error = 'Huella no reconocida. Intenta de nuevo o usa contraseña.';
        usuario = null;
        return false;
      }
      usuario = user;
      region = user.pais ?? await regionSession.leer();
      _arrancarSync();
      unawaited(_actualizarCacheTasasLogin());
      return true;
    } on BiometricStorageEmptyException catch (e) {
      error = e.toString();
      usuario = null;
      return false;
    } on StateError catch (e) {
      error = e.message;
      usuario = null;
      return false;
    } catch (e) {
      error = e is ApiException ? e.message : e.toString();
      usuario = null;
      return false;
    } finally {
      cargando = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await sync.dejarDeEscuchar();
    await alertas.limpiar();
    await sync.limpiarLocal();
    await auth.logout(borrarAccesoBiometrico: true);
    usuario = null;
    region = null;
    notifyListeners();
  }

  void _arrancarSync() {
    sync.escucharRed();
    unawaited(sync.sincronizar());
  }

  Future<void> _actualizarCacheTasasLogin() async {
    try {
      final t = await tasas.ultima();
      await TasasLoginCache.guardar(
        usdBcvBs: t.usdBcvBs,
        usdParaleloBs: t.usdParaleloBs,
      );
    } catch (_) {}
  }
}
