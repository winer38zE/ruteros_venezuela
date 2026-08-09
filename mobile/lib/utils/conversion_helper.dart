/// Cálculos multimoneda locales usando tasas del día.
class DesgloseMoneda {
  const DesgloseMoneda({
    required this.montoOrigen,
    required this.monedaOrigen,
    required this.usd,
    required this.vesBcv,
    required this.vesParalelo,
    required this.cop,
  });

  final double montoOrigen;
  final String monedaOrigen;
  final double usd;
  final double vesBcv;
  final double vesParalelo;
  final double cop;
}

DesgloseMoneda calcularDesglose({
  required double monto,
  required String monedaOrigen,
  required double tasaBcv,
  required double tasaParalelo,
  required double copPorUsd,
  String tipoTasaActiva = 'bcv',
}) {
  final tasaVes = tipoTasaActiva == 'paralelo' ? tasaParalelo : tasaBcv;

  double usd;
  if (monedaOrigen == 'usd') {
    usd = monto;
  } else if (monedaOrigen == 'ves') {
    usd = tasaVes > 0 ? monto / tasaVes : 0;
  } else {
    usd = copPorUsd > 0 ? monto / copPorUsd : 0;
  }

  return DesgloseMoneda(
    montoOrigen: monto,
    monedaOrigen: monedaOrigen,
    usd: usd,
    vesBcv: usd * tasaBcv,
    vesParalelo: usd * tasaParalelo,
    cop: usd * copPorUsd,
  );
}

/// Convierte un abono en moneda local a USD para restar del saldo del crédito.
double abonoAMontoUsd({
  required double monto,
  required String moneda,
  required double tasaBcv,
  required double copPorUsd,
}) {
  switch (moneda) {
    case 'usd':
      return monto;
    case 'ves':
      return tasaBcv > 0 ? monto / tasaBcv : 0;
    case 'cop':
      return copPorUsd > 0 ? monto / copPorUsd : 0;
    default:
      return monto;
  }
}

String etiquetaMoneda(String codigo) {
  switch (codigo) {
    case 'usd':
      return 'USD';
    case 'ves':
      return 'VES (Bs)';
    case 'cop':
      return 'COP';
    default:
      return codigo.toUpperCase();
  }
}

String monedaPagoBackend(String codigo) {
  switch (codigo) {
    case 'ves':
      return 'bolivar';
    case 'cop':
      return 'transferencia';
    default:
      return 'dolar';
  }
}
