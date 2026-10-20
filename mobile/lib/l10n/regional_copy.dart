/// Textos en español con variantes ligeras por país (sin i18n completo).
class RegionalCopy {
  const RegionalCopy({required this.esVenezuela});

  final bool esVenezuela;

  factory RegionalCopy.fromEsVenezuela(bool? esVenezuela) {
    return RegionalCopy(esVenezuela: esVenezuela ?? false);
  }

  /// Ventas a crédito / fiadas según región.
  String get ventasCreditoCorto => esVenezuela ? 'ventas fiadas' : 'ventas a crédito';

  String get loginSubtitulo =>
      'Controla tus $ventasCreditoCorto, cobros y rutas';

  String get emptyClientesTitulo => 'Aún no tienes clientes';

  String get emptyClientesDetalle => esVenezuela
      ? 'Registra a quienes compran fiado para llevar saldo y cobros en ruta.'
      : 'Registra a tus clientes para vender a crédito y cobrar en ruta.';

  String get emptyVentasTitulo => 'Sin ventas todavía';

  String get emptyVentasDetalle => esVenezuela
      ? 'Registra la primera venta fiada o al contado desde aquí.'
      : 'Registra tu primera venta a crédito o al contado desde aquí.';

  String get emptyCobrosTitulo => 'Sin cobros registrados';

  String get emptyCobrosDetalle => esVenezuela
      ? 'Cuando cobres en la ruta, registra el abono y actualiza el saldo.'
      : 'Registra los abonos de tus clientes cuando cobres en calle.';
}
