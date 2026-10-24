import '../models/pais_region.dart';

/// Precios de inventario según país: solo Venezuela usa USD + VES + COP.
class ProductoPreciosRegionConfig {
  const ProductoPreciosRegionConfig({
    required this.esVenezuela,
    required this.monedaLocal,
    required this.mostrarUsd,
    required this.mostrarVes,
    required this.mostrarCop,
    required this.mostrarMonedaLocal,
    required this.usdEsObligatorio,
    required this.localEsObligatorio,
  });

  final bool esVenezuela;
  final String monedaLocal;
  final bool mostrarUsd;
  final bool mostrarVes;
  final bool mostrarCop;
  final bool mostrarMonedaLocal;
  final bool usdEsObligatorio;
  final bool localEsObligatorio;

  factory ProductoPreciosRegionConfig.from(PaisRegion? region, {required bool esVenezuela}) {
    if (esVenezuela) {
      return const ProductoPreciosRegionConfig(
        esVenezuela: true,
        monedaLocal: 'VES',
        mostrarUsd: true,
        mostrarVes: true,
        mostrarCop: true,
        mostrarMonedaLocal: false,
        usdEsObligatorio: true,
        localEsObligatorio: false,
      );
    }

    final local = (region?.monedaPrincipal ?? 'USD').toUpperCase();
    final visibles = region?.monedasVisibles ?? [local, if (local != 'USD') 'USD'];
    final set = visibles.map((m) => m.toUpperCase()).toSet();

    final muestraUsd = set.contains('USD');
    final muestraCop = set.contains('COP');
    final muestraLocal = local != 'USD' && local != 'VES' && local != 'COP';

    // Colombia y similares: COP local + USD opcional.
    if (local == 'COP') {
      return ProductoPreciosRegionConfig(
        esVenezuela: false,
        monedaLocal: 'COP',
        mostrarUsd: muestraUsd,
        mostrarVes: false,
        mostrarCop: true,
        mostrarMonedaLocal: false,
        usdEsObligatorio: false,
        localEsObligatorio: true,
      );
    }

    // USD como moneda principal (Puerto Rico, etc.).
    if (local == 'USD') {
      return const ProductoPreciosRegionConfig(
        esVenezuela: false,
        monedaLocal: 'USD',
        mostrarUsd: true,
        mostrarVes: false,
        mostrarCop: false,
        mostrarMonedaLocal: false,
        usdEsObligatorio: true,
        localEsObligatorio: false,
      );
    }

    // BRL, PEN, MXN…: precio en moneda local; USD de referencia si el catálogo lo incluye.
    return ProductoPreciosRegionConfig(
      esVenezuela: false,
      monedaLocal: local,
      mostrarUsd: muestraUsd && local != 'USD',
      mostrarVes: false,
      mostrarCop: false,
      mostrarMonedaLocal: true,
      usdEsObligatorio: false,
      localEsObligatorio: true,
    );
  }

  String etiquetaUsd({required bool obligatorio}) =>
      obligatorio ? 'Precio de venta USD *' : 'Precio de venta USD (opcional)';

  String get etiquetaVes => 'Precio de venta VES (opcional)';

  String get etiquetaCop {
    if (esVenezuela) return 'Precio de venta COP (opcional)';
    return 'Precio de venta COP *';
  }

  String get etiquetaMonedaLocal => 'Precio de venta $monedaLocal *';

  /// Mapeo al cuerpo POST/PUT del backend (`precio_base_usd`, `precio_ves`, `precio_cop`).
  static ProductoPreciosApiPayload toApi({
    required ProductoPreciosRegionConfig config,
    required double? usd,
    required double? ves,
    required double? cop,
    required double? local,
  }) {
    if (config.esVenezuela) {
      if (usd == null || usd <= 0) {
        throw ArgumentError('Precio USD obligatorio');
      }
      return ProductoPreciosApiPayload(precioUsd: usd, precioVes: ves, precioCop: cop);
    }

    if (config.monedaLocal == 'COP') {
      final copVal = cop ?? local;
      if (copVal == null || copVal <= 0) {
        throw ArgumentError('Precio COP obligatorio');
      }
      final usdVal = (usd != null && usd > 0) ? usd : 0;
      return ProductoPreciosApiPayload(precioUsd: usdVal, precioVes: null, precioCop: copVal);
    }

    if (config.monedaLocal == 'USD') {
      if (usd == null || usd <= 0) throw ArgumentError('Precio USD obligatorio');
      return ProductoPreciosApiPayload(precioUsd: usd, precioVes: null, precioCop: null);
    }

    final localVal = local ?? usd;
    if (localVal == null || localVal <= 0) {
      throw ArgumentError('Precio en ${config.monedaLocal} obligatorio');
    }
    final usdRef = (usd != null && usd > 0) ? usd : localVal;
    return ProductoPreciosApiPayload(precioUsd: usdRef, precioVes: null, precioCop: null);
  }

  /// Texto para la lista de inventario.
  String resumenLista({
    required double precioUsd,
    double? precioVes,
    double? precioCop,
    required String Function(double) fmt,
  }) {
    if (esVenezuela) {
      final partes = <String>['USD ${fmt(precioUsd)}'];
      if (precioVes != null && precioVes > 0) partes.add('VES ${fmt(precioVes)}');
      if (precioCop != null && precioCop > 0) partes.add('COP ${fmt(precioCop)}');
      return partes.join(' · ');
    }
    if (monedaLocal == 'COP' && precioCop != null && precioCop > 0) {
      if (precioUsd > 0 && (precioCop - precioUsd).abs() > 0.01) {
        return 'COP ${fmt(precioCop)} · USD ${fmt(precioUsd)}';
      }
      return 'COP ${fmt(precioCop)}';
    }
    if (monedaLocal != 'USD') {
      return '$monedaLocal ${fmt(precioUsd)}';
    }
    return 'USD ${fmt(precioUsd)}';
  }
}

class ProductoPreciosApiPayload {
  const ProductoPreciosApiPayload({
    required this.precioUsd,
    this.precioVes,
    this.precioCop,
  });

  final double precioUsd;
  final double? precioVes;
  final double? precioCop;
}
