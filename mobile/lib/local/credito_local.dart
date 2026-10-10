import 'package:isar/isar.dart';

part 'credito_local.g.dart';

@collection
class CreditoLocal {
  Id id = Isar.autoIncrement;

  /// Id de la venta en el servidor.
  @Index(unique: true, replace: true)
  String ventaId = '';

  @Index()
  String? clienteId;

  String? clienteNombre;
  DateTime? fechaVencimiento;

  /// pendiente, vencido o pagado. El teléfono no lo envía al servidor.
  String estado = 'pendiente';

  double saldo = 0;

  /// Día en que ya se avisó, para no repetir la alerta en cada apertura.
  DateTime? ultimoAviso;
}
