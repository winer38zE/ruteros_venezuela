class PaisRegion {
  final String id;
  final String nombre;
  final String codigoIso;
  final String monedaPrincipal;
  final String simboloMoneda;

  const PaisRegion({
    required this.id,
    required this.nombre,
    required this.codigoIso,
    required this.monedaPrincipal,
    required this.simboloMoneda,
  });

  factory PaisRegion.fromJson(Map<String, dynamic> j) => PaisRegion(
        id: (j['id'] ?? '').toString(),
        nombre: (j['nombre'] ?? '').toString(),
        codigoIso: (j['codigo_iso'] ?? '').toString(),
        monedaPrincipal: (j['moneda_principal'] ?? '').toString(),
        simboloMoneda: (j['simbolo_moneda'] ?? '').toString(),
      );

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
      };

  String get etiquetaLista => '$nombre ($codigoIso · $simboloMoneda)';
}
