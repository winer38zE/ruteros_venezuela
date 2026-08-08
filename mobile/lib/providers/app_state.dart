import 'package:flutter/foundation.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/contabilidad_service.dart';
import '../services/inventario_service.dart';
import '../services/productos_service.dart';
import '../services/catalogo_service.dart';
import '../services/ventas_service.dart';
import '../services/cobros_service.dart';
import '../services/finanzas_service.dart';
import '../services/usuarios_service.dart';
import '../services/proveedores_service.dart';
import '../services/clientes_service.dart';
import '../services/tasas_service.dart';

class AppState extends ChangeNotifier {
  AppState() {
    auth = AuthService(api);
    contabilidad = ContabilidadService(api);
    inventario = InventarioService(api);
    productos = ProductosService(api);
    catalogo = CatalogoService(api);
    ventas = VentasService(api);
    cobros = CobrosService(api);
    finanzas = FinanzasService(api);
    usuarios = UsuariosService(api);
    proveedores = ProveedoresService(api);
    clientes = ClientesService(api);
    tasas = TasasService(api);
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
  late final FinanzasService finanzas;
  late final UsuariosService usuarios;
  late final ProveedoresService proveedores;
  late final ClientesService clientes;
  late final TasasService tasas;

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
