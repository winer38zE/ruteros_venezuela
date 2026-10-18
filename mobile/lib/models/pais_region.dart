class PaisRegion {
  final String id;
  final String nombre;
  final String codigoIso;
  final String monedaPrincipal;
  final String simboloMoneda;
  final Map<String, dynamic>? configuracionBancaria;

  const PaisRegion({
    required this.id,
    required this.nombre,
    required this.codigoIso,
    required this.monedaPrincipal,
    required this.simboloMoneda,
    this.configuracionBancaria,
  });

  factory PaisRegion.fromJson(Map<String, dynamic> j) {
    Map<String, dynamic>? cfg;
    final rawCfg = j['configuracion_bancaria'];
    if (rawCfg is Map<String, dynamic>) {
      cfg = rawCfg;
    } else if (rawCfg is Map) {
      cfg = Map<String, dynamic>.from(rawCfg);
    }
    return PaisRegion(
      id: (j['id'] ?? '').toString(),
      nombre: (j['nombre'] ?? '').toString(),
      codigoIso: (j['codigo_iso'] ?? '').toString(),
      monedaPrincipal: (j['moneda_principal'] ?? '').toString(),
      simboloMoneda: (j['simbolo_moneda'] ?? '').toString(),
      configuracionBancaria: cfg,
    );
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
      };

  String get etiquetaLista => '$nombre ($codigoIso · $simboloMoneda)';
}
