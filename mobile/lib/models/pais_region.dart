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
        id: j['id'] as String,
        nombre: j['nombre'] as String,
        codigoIso: j['codigo_iso'] as String,
        monedaPrincipal: j['moneda_principal'] as String,
        simboloMoneda: j['simbolo_moneda'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'codigo_iso': codigoIso,
        'moneda_principal': monedaPrincipal,
        'simbolo_moneda': simboloMoneda,
      };

  String get etiquetaLista => '$nombre ($codigoIso · $simboloMoneda)';
}
