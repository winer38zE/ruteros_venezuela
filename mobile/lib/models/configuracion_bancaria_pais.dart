/// Catálogo bancario del país (desde `configuracion_bancaria` en PocketBase/FastAPI).
class ConfiguracionBancariaPais {
  final List<String> bancos;
  final List<String> documentosLegales;
  final List<({String id, String label})> tiposCuenta;
  final List<({String id, String label})> canalesPago;

  const ConfiguracionBancariaPais({
    required this.bancos,
    required this.documentosLegales,
    required this.tiposCuenta,
    required this.canalesPago,
  });

  factory ConfiguracionBancariaPais.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return ConfiguracionBancariaPais.fallbackVenezuela();
    }
    final bancosRaw = json['bancos'];
    final docsRaw = json['documentos_legales'];
    final bancos = bancosRaw is List
        ? bancosRaw.map((e) => e.toString()).where((s) => s.isNotEmpty).toList()
        : <String>[];
    var docs = docsRaw is List
        ? docsRaw.map((e) => e.toString()).where((s) => s.isNotEmpty).toList()
        : <String>[];
    if (docs.isEmpty && json['tipos_identificacion'] is List) {
      for (final t in json['tipos_identificacion'] as List) {
        if (t is Map && t['label'] != null) {
          docs.add(t['label'].toString());
        }
      }
    }

    final tipos = <({String id, String label})>[];
    if (json['tipos_cuenta'] is List) {
      for (final t in json['tipos_cuenta'] as List) {
        if (t is Map) {
          final id = (t['id'] ?? t['label'] ?? '').toString();
          final label = (t['label'] ?? id).toString();
          if (id.isNotEmpty) tipos.add((id: id, label: label));
        }
      }
    }
    if (tipos.isEmpty) {
      tipos.addAll([
        (id: 'ahorro', label: 'Ahorro'),
        (id: 'corriente', label: 'Corriente'),
      ]);
    }

    final canales = <({String id, String label})>[];
    if (json['canales_pago'] is List) {
      for (final c in json['canales_pago'] as List) {
        if (c is Map) {
          final id = (c['id'] ?? '').toString();
          final label = (c['label'] ?? id).toString();
          if (id.isNotEmpty) canales.add((id: id, label: label));
        }
      }
    }
    if (canales.isEmpty) {
      canales.addAll([
        (id: 'transferencia', label: 'Transferencia'),
        if (bancos.any((b) => b.toLowerCase().contains('pago móvil') || b.toLowerCase() == 'pago movil'))
          (id: 'pago_movil', label: 'Pago móvil'),
      ]);
    }

    if (bancos.isEmpty) {
      return ConfiguracionBancariaPais.fallbackVenezuela();
    }

    return ConfiguracionBancariaPais(
      bancos: bancos,
      documentosLegales: docs.isNotEmpty ? docs : ['Doc'],
      tiposCuenta: tipos,
      canalesPago: canales,
    );
  }

  factory ConfiguracionBancariaPais.fallbackVenezuela() => const ConfiguracionBancariaPais(
        bancos: [
          'Pago Móvil',
          'Banco de Venezuela',
          'Banesco',
          'Mercantil',
          'Provincial',
        ],
        documentosLegales: ['V', 'J', 'E', 'G'],
        tiposCuenta: [
          (id: 'ahorro', label: 'Ahorro'),
          (id: 'corriente', label: 'Corriente'),
        ],
        canalesPago: [
          (id: 'transferencia', label: 'Transferencia'),
          (id: 'pago_movil', label: 'Pago móvil'),
        ],
      );

  bool get bancoEsPagoMovil => bancos.any((b) => b.toLowerCase().contains('pago móvil') || b.toLowerCase() == 'pago movil');

  bool esCanalPagoMovil(String banco, String canal) {
    if (canal == 'pago_movil') return true;
    final b = banco.toLowerCase();
    return b.contains('pago móvil') || b == 'pago movil' || b == 'yape' || b == 'plin' || b == 'pix' || b == 'nequi' || b == 'daviplata';
  }
}
