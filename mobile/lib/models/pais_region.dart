class PaisRegion {
  final String id;
  final String nombre;
  final String codigoIso;
  final String monedaPrincipal;
  final String simboloMoneda;
  final Map<String, dynamic>? configuracionBancaria;
  final Map<String, dynamic>? configuracionUi;

  const PaisRegion({
    required this.id,
    required this.nombre,
    required this.codigoIso,
    required this.monedaPrincipal,
    required this.simboloMoneda,
    this.configuracionBancaria,
    this.configuracionUi,
  });

  factory PaisRegion.fromJson(Map<String, dynamic> j) {
    Map<String, dynamic>? cfg;
    final rawCfg = j['configuracion_bancaria'];
    if (rawCfg is Map<String, dynamic>) {
      cfg = rawCfg;
    } else if (rawCfg is Map) {
      cfg = Map<String, dynamic>.from(rawCfg);
    }
    Map<String, dynamic>? ui;
    final rawUi = j['configuracion_ui'];
    if (rawUi is Map<String, dynamic>) {
      ui = rawUi;
    } else if (rawUi is Map) {
      ui = Map<String, dynamic>.from(rawUi);
    }

    return PaisRegion(
      id: (j['id'] ?? '').toString(),
      nombre: (j['nombre'] ?? '').toString(),
      codigoIso: (j['codigo_iso'] ?? '').toString(),
      monedaPrincipal: (j['moneda_principal'] ?? '').toString(),
      simboloMoneda: (j['simbolo_moneda'] ?? '').toString(),
      configuracionBancaria: cfg,
      configuracionUi: ui,
    );
  }

  List<String> get monedasVisibles {
    final raw = configuracionUi?['monedas_visibles'];
    if (raw is List) {
      return raw.map((e) => e.toString().toUpperCase()).where((e) => e.isNotEmpty).toList();
    }
    final local = monedaPrincipal.toUpperCase();
    if (local == 'USD') return ['USD'];
    return [local, 'USD'];
  }

  bool get valido =>
      id.isNotEmpty &&
      nombre.isNotEmpty &&
      codigoIso.isNotEmpty &&
      monedaPrincipal.isNotEmpty;

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'codigo_iso': codigoIso,
        'moneda_principal': monedaPrincipal,
        'simbolo_moneda': simboloMoneda,
        if (configuracionBancaria != null) 'configuracion_bancaria': configuracionBancaria,
        if (configuracionUi != null) 'configuracion_ui': configuracionUi,
      };

  String get etiquetaLista => '$nombre ($codigoIso · $simboloMoneda)';

  /// Módulo de tasas BCV/paralelo: solo aplica a la economía venezolana.
  bool get esVenezuela {
    if (codigoIso.toUpperCase().trim() == 'VE') return true;
    return nombre.toLowerCase().trim() == 'venezuela';
  }
}
