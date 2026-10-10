import 'package:isar/isar.dart';

part 'cliente_local.g.dart';

@collection
class ClienteLocal {
  Id id = Isar.autoIncrement;

  String? nombre;
  String? cedula;
  bool? esMoroso;
  int? score;

  /// Id del cliente en el servidor, para sincronizar sin duplicar.
  @Index(unique: true, replace: true)
  String? servidorId;
}
