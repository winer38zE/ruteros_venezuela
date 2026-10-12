// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cliente_local.dart';

// **************************************************************************
// IsarCollectionGenerator
// **************************************************************************

// coverage:ignore-file
// ignore_for_file: duplicate_ignore, non_constant_identifier_names, constant_identifier_names, invalid_use_of_protected_member, unnecessary_cast, prefer_const_constructors, lines_longer_than_80_chars, require_trailing_commas, inference_failure_on_function_invocation, unnecessary_parenthesis, unnecessary_raw_strings, unnecessary_null_checks, join_return_with_assignment, prefer_final_locals, avoid_js_rounded_ints, avoid_positional_boolean_parameters, always_specify_types

extension GetClienteLocalCollection on Isar {
  IsarCollection<ClienteLocal> get clienteLocals => this.collection();
}

const ClienteLocalSchema = CollectionSchema(
  name: r'ClienteLocal',
  id: -2581183314480681732,
  properties: {
    r'cedula': PropertySchema(
      id: 0,
      name: r'cedula',
      type: IsarType.string,
    ),
    r'clave': PropertySchema(
      id: 1,
      name: r'clave',
      type: IsarType.string,
    ),
    r'creditoVencido': PropertySchema(
      id: 2,
      name: r'creditoVencido',
      type: IsarType.bool,
    ),
    r'direccion': PropertySchema(
      id: 3,
      name: r'direccion',
      type: IsarType.string,
    ),
    r'errorSync': PropertySchema(
      id: 4,
      name: r'errorSync',
      type: IsarType.string,
    ),
    r'esMoroso': PropertySchema(
      id: 5,
      name: r'esMoroso',
      type: IsarType.bool,
    ),
    r'nombre': PropertySchema(
      id: 6,
      name: r'nombre',
      type: IsarType.string,
    ),
    r'payloadJson': PropertySchema(
      id: 7,
      name: r'payloadJson',
      type: IsarType.string,
    ),
    r'score': PropertySchema(
      id: 8,
      name: r'score',
      type: IsarType.long,
    ),
    r'servidorId': PropertySchema(
      id: 9,
      name: r'servidorId',
      type: IsarType.string,
    ),
    r'sincronizado': PropertySchema(
      id: 10,
      name: r'sincronizado',
      type: IsarType.bool,
    ),
    r'telefono': PropertySchema(
      id: 11,
      name: r'telefono',
      type: IsarType.string,
    )
  },
  estimateSize: _clienteLocalEstimateSize,
  serialize: _clienteLocalSerialize,
  deserialize: _clienteLocalDeserialize,
  deserializeProp: _clienteLocalDeserializeProp,
  idName: r'id',
  indexes: {
    r'servidorId': IndexSchema(
      id: -7953509549575050633,
      name: r'servidorId',
      unique: false,
      replace: false,
      properties: [
        IndexPropertySchema(
          name: r'servidorId',
          type: IndexType.hash,
          caseSensitive: true,
        )
      ],
    ),
    r'sincronizado': IndexSchema(
      id: -5635005241243394166,
      name: r'sincronizado',
      unique: false,
      replace: false,
      properties: [
        IndexPropertySchema(
          name: r'sincronizado',
          type: IndexType.value,
          caseSensitive: false,
        )
      ],
    ),
    r'clave': IndexSchema(
      id: 8488737604413641549,
      name: r'clave',
      unique: true,
      replace: true,
      properties: [
        IndexPropertySchema(
          name: r'clave',
          type: IndexType.hash,
          caseSensitive: true,
        )
      ],
    )
  },
  links: {},
  embeddedSchemas: {},
  getId: _clienteLocalGetId,
  getLinks: _clienteLocalGetLinks,
  attach: _clienteLocalAttach,
  version: '3.1.0+1',
);

int _clienteLocalEstimateSize(
  ClienteLocal object,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  var bytesCount = offsets.last;
  {
    final value = object.cedula;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  bytesCount += 3 + object.clave.length * 3;
  {
    final value = object.direccion;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.errorSync;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.nombre;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.payloadJson;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.servidorId;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.telefono;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  return bytesCount;
}

void _clienteLocalSerialize(
  ClienteLocal object,
  IsarWriter writer,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  writer.writeString(offsets[0], object.cedula);
  writer.writeString(offsets[1], object.clave);
  writer.writeBool(offsets[2], object.creditoVencido);
  writer.writeString(offsets[3], object.direccion);
  writer.writeString(offsets[4], object.errorSync);
  writer.writeBool(offsets[5], object.esMoroso);
  writer.writeString(offsets[6], object.nombre);
  writer.writeString(offsets[7], object.payloadJson);
  writer.writeLong(offsets[8], object.score);
  writer.writeString(offsets[9], object.servidorId);
  writer.writeBool(offsets[10], object.sincronizado);
  writer.writeString(offsets[11], object.telefono);
}

ClienteLocal _clienteLocalDeserialize(
  Id id,
  IsarReader reader,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  final object = ClienteLocal();
  object.cedula = reader.readStringOrNull(offsets[0]);
  object.clave = reader.readString(offsets[1]);
  object.creditoVencido = reader.readBool(offsets[2]);
  object.direccion = reader.readStringOrNull(offsets[3]);
  object.errorSync = reader.readStringOrNull(offsets[4]);
  object.esMoroso = reader.readBoolOrNull(offsets[5]);
  object.id = id;
  object.nombre = reader.readStringOrNull(offsets[6]);
  object.payloadJson = reader.readStringOrNull(offsets[7]);
  object.score = reader.readLongOrNull(offsets[8]);
  object.servidorId = reader.readStringOrNull(offsets[9]);
  object.sincronizado = reader.readBool(offsets[10]);
  object.telefono = reader.readStringOrNull(offsets[11]);
  return object;
}

P _clienteLocalDeserializeProp<P>(
  IsarReader reader,
  int propertyId,
  int offset,
  Map<Type, List<int>> allOffsets,
) {
  switch (propertyId) {
    case 0:
      return (reader.readStringOrNull(offset)) as P;
    case 1:
      return (reader.readString(offset)) as P;
    case 2:
      return (reader.readBool(offset)) as P;
    case 3:
      return (reader.readStringOrNull(offset)) as P;
    case 4:
      return (reader.readStringOrNull(offset)) as P;
    case 5:
      return (reader.readBoolOrNull(offset)) as P;
    case 6:
      return (reader.readStringOrNull(offset)) as P;
    case 7:
      return (reader.readStringOrNull(offset)) as P;
    case 8:
      return (reader.readLongOrNull(offset)) as P;
    case 9:
      return (reader.readStringOrNull(offset)) as P;
    case 10:
      return (reader.readBool(offset)) as P;
    case 11:
      return (reader.readStringOrNull(offset)) as P;
    default:
      throw IsarError('Unknown property with id $propertyId');
  }
}

Id _clienteLocalGetId(ClienteLocal object) {
  return object.id;
}

List<IsarLinkBase<dynamic>> _clienteLocalGetLinks(ClienteLocal object) {
  return [];
}

void _clienteLocalAttach(
    IsarCollection<dynamic> col, Id id, ClienteLocal object) {
  object.id = id;
}

extension ClienteLocalByIndex on IsarCollection<ClienteLocal> {
  Future<ClienteLocal?> getByClave(String clave) {
    return getByIndex(r'clave', [clave]);
  }

  ClienteLocal? getByClaveSync(String clave) {
    return getByIndexSync(r'clave', [clave]);
  }

  Future<bool> deleteByClave(String clave) {
    return deleteByIndex(r'clave', [clave]);
  }

  bool deleteByClaveSync(String clave) {
    return deleteByIndexSync(r'clave', [clave]);
  }

  Future<List<ClienteLocal?>> getAllByClave(List<String> claveValues) {
    final values = claveValues.map((e) => [e]).toList();
    return getAllByIndex(r'clave', values);
  }

  List<ClienteLocal?> getAllByClaveSync(List<String> claveValues) {
    final values = claveValues.map((e) => [e]).toList();
    return getAllByIndexSync(r'clave', values);
  }

  Future<int> deleteAllByClave(List<String> claveValues) {
    final values = claveValues.map((e) => [e]).toList();
    return deleteAllByIndex(r'clave', values);
  }

  int deleteAllByClaveSync(List<String> claveValues) {
    final values = claveValues.map((e) => [e]).toList();
    return deleteAllByIndexSync(r'clave', values);
  }

  Future<Id> putByClave(ClienteLocal object) {
    return putByIndex(r'clave', object);
  }

  Id putByClaveSync(ClienteLocal object, {bool saveLinks = true}) {
    return putByIndexSync(r'clave', object, saveLinks: saveLinks);
  }

  Future<List<Id>> putAllByClave(List<ClienteLocal> objects) {
    return putAllByIndex(r'clave', objects);
  }

  List<Id> putAllByClaveSync(List<ClienteLocal> objects,
      {bool saveLinks = true}) {
    return putAllByIndexSync(r'clave', objects, saveLinks: saveLinks);
  }
}

extension ClienteLocalQueryWhereSort
    on QueryBuilder<ClienteLocal, ClienteLocal, QWhere> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhere> anyId() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(const IdWhereClause.any());
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhere> anySincronizado() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        const IndexWhereClause.any(indexName: r'sincronizado'),
      );
    });
  }
}

extension ClienteLocalQueryWhere
    on QueryBuilder<ClienteLocal, ClienteLocal, QWhereClause> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> idEqualTo(Id id) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IdWhereClause.between(
        lower: id,
        upper: id,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> idNotEqualTo(
      Id id) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(
              IdWhereClause.lessThan(upper: id, includeUpper: false),
            )
            .addWhereClause(
              IdWhereClause.greaterThan(lower: id, includeLower: false),
            );
      } else {
        return query
            .addWhereClause(
              IdWhereClause.greaterThan(lower: id, includeLower: false),
            )
            .addWhereClause(
              IdWhereClause.lessThan(upper: id, includeUpper: false),
            );
      }
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> idGreaterThan(
      Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.greaterThan(lower: id, includeLower: include),
      );
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> idLessThan(Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.lessThan(upper: id, includeUpper: include),
      );
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> idBetween(
    Id lowerId,
    Id upperId, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IdWhereClause.between(
        lower: lowerId,
        includeLower: includeLower,
        upper: upperId,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause>
      servidorIdIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'servidorId',
        value: [null],
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause>
      servidorIdIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.between(
        indexName: r'servidorId',
        lower: [null],
        includeLower: false,
        upper: [],
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> servidorIdEqualTo(
      String? servidorId) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'servidorId',
        value: [servidorId],
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause>
      servidorIdNotEqualTo(String? servidorId) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'servidorId',
              lower: [],
              upper: [servidorId],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'servidorId',
              lower: [servidorId],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'servidorId',
              lower: [servidorId],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'servidorId',
              lower: [],
              upper: [servidorId],
              includeUpper: false,
            ));
      }
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause>
      sincronizadoEqualTo(bool sincronizado) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'sincronizado',
        value: [sincronizado],
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause>
      sincronizadoNotEqualTo(bool sincronizado) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'sincronizado',
              lower: [],
              upper: [sincronizado],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'sincronizado',
              lower: [sincronizado],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'sincronizado',
              lower: [sincronizado],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'sincronizado',
              lower: [],
              upper: [sincronizado],
              includeUpper: false,
            ));
      }
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> claveEqualTo(
      String clave) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'clave',
        value: [clave],
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhereClause> claveNotEqualTo(
      String clave) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clave',
              lower: [],
              upper: [clave],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clave',
              lower: [clave],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clave',
              lower: [clave],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clave',
              lower: [],
              upper: [clave],
              includeUpper: false,
            ));
      }
    });
  }
}

extension ClienteLocalQueryFilter
    on QueryBuilder<ClienteLocal, ClienteLocal, QFilterCondition> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'cedula',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'cedula',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> cedulaEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> cedulaBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'cedula',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'cedula',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> cedulaMatches(
      String pattern,
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'cedula',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'cedula',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      cedulaIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'cedula',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveEqualTo(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      claveGreaterThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveLessThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveBetween(
    String lower,
    String upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'clave',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      claveStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveContains(
      String value,
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'clave',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> claveMatches(
      String pattern,
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'clave',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      claveIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clave',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      claveIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'clave',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      creditoVencidoEqualTo(bool value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'creditoVencido',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'direccion',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'direccion',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'direccion',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'direccion',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'direccion',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'direccion',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      direccionIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'direccion',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'errorSync',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'errorSync',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'errorSync',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'errorSync',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'errorSync',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'errorSync',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      errorSyncIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'errorSync',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      esMorosoIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'esMoroso',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      esMorosoIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'esMoroso',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      esMorosoEqualTo(bool? value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'esMoroso',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> idEqualTo(
      Id value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> idGreaterThan(
    Id value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> idLessThan(
    Id value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> idBetween(
    Id lower,
    Id upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'id',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'nombre',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'nombre',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> nombreEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> nombreBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'nombre',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'nombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> nombreMatches(
      String pattern,
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'nombre',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'nombre',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      nombreIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'nombre',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'payloadJson',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'payloadJson',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'payloadJson',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'payloadJson',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'payloadJson',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'payloadJson',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      payloadJsonIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'payloadJson',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      scoreIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'score',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      scoreIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'score',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> scoreEqualTo(
      int? value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'score',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      scoreGreaterThan(
    int? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'score',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> scoreLessThan(
    int? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'score',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition> scoreBetween(
    int? lower,
    int? upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'score',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'servidorId',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'servidorId',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'servidorId',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'servidorId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'servidorId',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'servidorId',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      servidorIdIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'servidorId',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      sincronizadoEqualTo(bool value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'sincronizado',
        value: value,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'telefono',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'telefono',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'telefono',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'telefono',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'telefono',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'telefono',
        value: '',
      ));
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterFilterCondition>
      telefonoIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'telefono',
        value: '',
      ));
    });
  }
}

extension ClienteLocalQueryObject
    on QueryBuilder<ClienteLocal, ClienteLocal, QFilterCondition> {}

extension ClienteLocalQueryLinks
    on QueryBuilder<ClienteLocal, ClienteLocal, QFilterCondition> {}

extension ClienteLocalQuerySortBy
    on QueryBuilder<ClienteLocal, ClienteLocal, QSortBy> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByCedula() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'cedula', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByCedulaDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'cedula', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByClave() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clave', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByClaveDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clave', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      sortByCreditoVencido() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'creditoVencido', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      sortByCreditoVencidoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'creditoVencido', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByDireccion() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'direccion', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByDireccionDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'direccion', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByErrorSync() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'errorSync', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByErrorSyncDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'errorSync', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByEsMoroso() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'esMoroso', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByEsMorosoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'esMoroso', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByNombre() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'nombre', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByNombreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'nombre', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByPayloadJson() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'payloadJson', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      sortByPayloadJsonDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'payloadJson', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByScore() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'score', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByScoreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'score', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByServidorId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'servidorId', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      sortByServidorIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'servidorId', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortBySincronizado() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'sincronizado', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      sortBySincronizadoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'sincronizado', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByTelefono() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'telefono', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> sortByTelefonoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'telefono', Sort.desc);
    });
  }
}

extension ClienteLocalQuerySortThenBy
    on QueryBuilder<ClienteLocal, ClienteLocal, QSortThenBy> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByCedula() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'cedula', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByCedulaDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'cedula', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByClave() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clave', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByClaveDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clave', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      thenByCreditoVencido() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'creditoVencido', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      thenByCreditoVencidoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'creditoVencido', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByDireccion() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'direccion', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByDireccionDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'direccion', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByErrorSync() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'errorSync', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByErrorSyncDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'errorSync', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByEsMoroso() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'esMoroso', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByEsMorosoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'esMoroso', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenById() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByNombre() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'nombre', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByNombreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'nombre', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByPayloadJson() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'payloadJson', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      thenByPayloadJsonDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'payloadJson', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByScore() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'score', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByScoreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'score', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByServidorId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'servidorId', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      thenByServidorIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'servidorId', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenBySincronizado() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'sincronizado', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy>
      thenBySincronizadoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'sincronizado', Sort.desc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByTelefono() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'telefono', Sort.asc);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QAfterSortBy> thenByTelefonoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'telefono', Sort.desc);
    });
  }
}

extension ClienteLocalQueryWhereDistinct
    on QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> {
  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByCedula(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'cedula', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByClave(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'clave', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct>
      distinctByCreditoVencido() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'creditoVencido');
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByDireccion(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'direccion', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByErrorSync(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'errorSync', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByEsMoroso() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'esMoroso');
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByNombre(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'nombre', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByPayloadJson(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'payloadJson', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByScore() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'score');
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByServidorId(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'servidorId', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctBySincronizado() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'sincronizado');
    });
  }

  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByTelefono(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'telefono', caseSensitive: caseSensitive);
    });
  }
}

extension ClienteLocalQueryProperty
    on QueryBuilder<ClienteLocal, ClienteLocal, QQueryProperty> {
  QueryBuilder<ClienteLocal, int, QQueryOperations> idProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'id');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> cedulaProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'cedula');
    });
  }

  QueryBuilder<ClienteLocal, String, QQueryOperations> claveProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'clave');
    });
  }

  QueryBuilder<ClienteLocal, bool, QQueryOperations> creditoVencidoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'creditoVencido');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> direccionProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'direccion');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> errorSyncProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'errorSync');
    });
  }

  QueryBuilder<ClienteLocal, bool?, QQueryOperations> esMorosoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'esMoroso');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> nombreProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'nombre');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> payloadJsonProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'payloadJson');
    });
  }

  QueryBuilder<ClienteLocal, int?, QQueryOperations> scoreProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'score');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> servidorIdProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'servidorId');
    });
  }

  QueryBuilder<ClienteLocal, bool, QQueryOperations> sincronizadoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'sincronizado');
    });
  }

  QueryBuilder<ClienteLocal, String?, QQueryOperations> telefonoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'telefono');
    });
  }
}
