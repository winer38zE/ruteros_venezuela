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
    r'esMoroso': PropertySchema(
      id: 1,
      name: r'esMoroso',
      type: IsarType.bool,
    ),
    r'nombre': PropertySchema(
      id: 2,
      name: r'nombre',
      type: IsarType.string,
    ),
    r'score': PropertySchema(
      id: 3,
      name: r'score',
      type: IsarType.long,
    ),
    r'servidorId': PropertySchema(
      id: 4,
      name: r'servidorId',
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
      unique: true,
      replace: true,
      properties: [
        IndexPropertySchema(
          name: r'servidorId',
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
  {
    final value = object.nombre;
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
  return bytesCount;
}

void _clienteLocalSerialize(
  ClienteLocal object,
  IsarWriter writer,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  writer.writeString(offsets[0], object.cedula);
  writer.writeBool(offsets[1], object.esMoroso);
  writer.writeString(offsets[2], object.nombre);
  writer.writeLong(offsets[3], object.score);
  writer.writeString(offsets[4], object.servidorId);
}

ClienteLocal _clienteLocalDeserialize(
  Id id,
  IsarReader reader,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  final object = ClienteLocal();
  object.cedula = reader.readStringOrNull(offsets[0]);
  object.esMoroso = reader.readBoolOrNull(offsets[1]);
  object.id = id;
  object.nombre = reader.readStringOrNull(offsets[2]);
  object.score = reader.readLongOrNull(offsets[3]);
  object.servidorId = reader.readStringOrNull(offsets[4]);
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
      return (reader.readBoolOrNull(offset)) as P;
    case 2:
      return (reader.readStringOrNull(offset)) as P;
    case 3:
      return (reader.readLongOrNull(offset)) as P;
    case 4:
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
  Future<ClienteLocal?> getByServidorId(String? servidorId) {
    return getByIndex(r'servidorId', [servidorId]);
  }

  ClienteLocal? getByServidorIdSync(String? servidorId) {
    return getByIndexSync(r'servidorId', [servidorId]);
  }

  Future<bool> deleteByServidorId(String? servidorId) {
    return deleteByIndex(r'servidorId', [servidorId]);
  }

  bool deleteByServidorIdSync(String? servidorId) {
    return deleteByIndexSync(r'servidorId', [servidorId]);
  }

  Future<List<ClienteLocal?>> getAllByServidorId(
      List<String?> servidorIdValues) {
    final values = servidorIdValues.map((e) => [e]).toList();
    return getAllByIndex(r'servidorId', values);
  }

  List<ClienteLocal?> getAllByServidorIdSync(List<String?> servidorIdValues) {
    final values = servidorIdValues.map((e) => [e]).toList();
    return getAllByIndexSync(r'servidorId', values);
  }

  Future<int> deleteAllByServidorId(List<String?> servidorIdValues) {
    final values = servidorIdValues.map((e) => [e]).toList();
    return deleteAllByIndex(r'servidorId', values);
  }

  int deleteAllByServidorIdSync(List<String?> servidorIdValues) {
    final values = servidorIdValues.map((e) => [e]).toList();
    return deleteAllByIndexSync(r'servidorId', values);
  }

  Future<Id> putByServidorId(ClienteLocal object) {
    return putByIndex(r'servidorId', object);
  }

  Id putByServidorIdSync(ClienteLocal object, {bool saveLinks = true}) {
    return putByIndexSync(r'servidorId', object, saveLinks: saveLinks);
  }

  Future<List<Id>> putAllByServidorId(List<ClienteLocal> objects) {
    return putAllByIndex(r'servidorId', objects);
  }

  List<Id> putAllByServidorIdSync(List<ClienteLocal> objects,
      {bool saveLinks = true}) {
    return putAllByIndexSync(r'servidorId', objects, saveLinks: saveLinks);
  }
}

extension ClienteLocalQueryWhereSort
    on QueryBuilder<ClienteLocal, ClienteLocal, QWhere> {
  QueryBuilder<ClienteLocal, ClienteLocal, QAfterWhere> anyId() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(const IdWhereClause.any());
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
}

extension ClienteLocalQueryWhereDistinct
    on QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> {
  QueryBuilder<ClienteLocal, ClienteLocal, QDistinct> distinctByCedula(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'cedula', caseSensitive: caseSensitive);
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
}
