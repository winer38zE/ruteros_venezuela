import 'package:flutter/foundation.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/contabilidad_service.dart';
import '../services/inventario_service.dart';
import '../services/catalogo_service.dart';
import '../services/ventas_service.dart';
import '../services/cobros_service.dart';
import '../services/finanzas_service.dart';

class AppState extends ChangeNotifier {
  AppState() {
    auth = AuthService(api);
    contabilidad = ContabilidadService(api);
    inventario = InventarioService(api);
    catalogo = CatalogoService(api);
    ventas = VentasService(api);
    cobros = CobrosService(api);
    finanzas = FinanzasService(api);
    _inicializar();
  }

  final ApiService api = ApiService();
  late final AuthService auth;
  late final ContabilidadService contabilidad;
  late final InventarioService inventario;
  late final CatalogoService catalogo;
  late final VentasService ventas;
  late final CobrosService cobros;
  late final FinanzasService finanzas;

  Usuario? usuario;
  bool inicializado = false;
  bool cargando = false;
  String? error;

  bool get esVendedor => usuario?.rol == 'VENDEDOR';
  bool get esCobrador => usuario?.rol == 'COBRADOR';
  bool get esDueno => usuario?.esDueno ?? false;
  bool get puedeVender => esVendedor || esDueno;
  bool get puedeCobrar => esCobrador || esDueno;

  Future<void> _inicializar() async {
    try {
      usuario = await auth.restoreSession();
    } catch (_) {
      usuario = null;
    } finally {
      inicializado = true;
      notifyListeners();
    }
  }

  Future<void> login(String username) async {
    cargando = true;
    error = null;
    notifyListeners();
    try {
      usuario = await auth.login(username);
    } catch (e) {
      error = e.toString();
      usuario = null;
    } finally {
      cargando = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await auth.logout();
    usuario = null;
    notifyListeners();
  }
}
