import 'package:isar/isar.dart';

part 'cliente_local.g.dart';

@collection
class ClienteLocal {
  Id id = Isar.autoIncrement;

  String? nombre;
  String? cedula;
  String? telefono;
  String? direccion;
  bool? esMoroso;
  int? score;

  /// Id en el servidor. Puede quedar vacío en varios pendientes a la vez.
  @Index()
  String? servidorId;

  /// Pasa a true solo cuando el backend confirma el alta o devuelve el catálogo.
  @Index()
  bool sincronizado = false;

  /// Clave única: uuid local mientras está pendiente, id del servidor al confirmar.
  @Index(unique: true, replace: true)
  String clave = '';

  /// Cuerpo del alta, igual al de POST /clientes/, para no perder la ruta ni el GPS.
  String? payloadJson;

  /// Último rechazo del servidor. La sync automática no reintenta este registro.
  String? errorSync;
}
