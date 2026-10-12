// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'credito_local.dart';

// **************************************************************************
// IsarCollectionGenerator
// **************************************************************************

// coverage:ignore-file
// ignore_for_file: duplicate_ignore, non_constant_identifier_names, constant_identifier_names, invalid_use_of_protected_member, unnecessary_cast, prefer_const_constructors, lines_longer_than_80_chars, require_trailing_commas, inference_failure_on_function_invocation, unnecessary_parenthesis, unnecessary_raw_strings, unnecessary_null_checks, join_return_with_assignment, prefer_final_locals, avoid_js_rounded_ints, avoid_positional_boolean_parameters, always_specify_types

extension GetCreditoLocalCollection on Isar {
  IsarCollection<CreditoLocal> get creditoLocals => this.collection();
}

const CreditoLocalSchema = CollectionSchema(
  name: r'CreditoLocal',
  id: -233851782298654657,
  properties: {
    r'clienteId': PropertySchema(
      id: 0,
      name: r'clienteId',
      type: IsarType.string,
    ),
    r'clienteNombre': PropertySchema(
      id: 1,
      name: r'clienteNombre',
      type: IsarType.string,
    ),
    r'estado': PropertySchema(
      id: 2,
      name: r'estado',
      type: IsarType.string,
    ),
    r'fechaVencimiento': PropertySchema(
      id: 3,
      name: r'fechaVencimiento',
      type: IsarType.dateTime,
    ),
    r'saldo': PropertySchema(
      id: 4,
      name: r'saldo',
      type: IsarType.double,
    ),
    r'ultimoAviso': PropertySchema(
      id: 5,
      name: r'ultimoAviso',
      type: IsarType.dateTime,
    ),
    r'ventaId': PropertySchema(
      id: 6,
      name: r'ventaId',
      type: IsarType.string,
    )
  },
  estimateSize: _creditoLocalEstimateSize,
  serialize: _creditoLocalSerialize,
  deserialize: _creditoLocalDeserialize,
  deserializeProp: _creditoLocalDeserializeProp,
  idName: r'id',
  indexes: {
    r'ventaId': IndexSchema(
      id: -8258295233686175365,
      name: r'ventaId',
      unique: true,
      replace: true,
      properties: [
        IndexPropertySchema(
          name: r'ventaId',
          type: IndexType.hash,
          caseSensitive: true,
        )
      ],
    ),
    r'clienteId': IndexSchema(
      id: 8548357859431292524,
      name: r'clienteId',
      unique: false,
      replace: false,
      properties: [
        IndexPropertySchema(
          name: r'clienteId',
          type: IndexType.hash,
          caseSensitive: true,
        )
      ],
    )
  },
  links: {},
  embeddedSchemas: {},
  getId: _creditoLocalGetId,
  getLinks: _creditoLocalGetLinks,
  attach: _creditoLocalAttach,
  version: '3.1.0+1',
);

int _creditoLocalEstimateSize(
  CreditoLocal object,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  var bytesCount = offsets.last;
  {
    final value = object.clienteId;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  {
    final value = object.clienteNombre;
    if (value != null) {
      bytesCount += 3 + value.length * 3;
    }
  }
  bytesCount += 3 + object.estado.length * 3;
  bytesCount += 3 + object.ventaId.length * 3;
  return bytesCount;
}

void _creditoLocalSerialize(
  CreditoLocal object,
  IsarWriter writer,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  writer.writeString(offsets[0], object.clienteId);
  writer.writeString(offsets[1], object.clienteNombre);
  writer.writeString(offsets[2], object.estado);
  writer.writeDateTime(offsets[3], object.fechaVencimiento);
  writer.writeDouble(offsets[4], object.saldo);
  writer.writeDateTime(offsets[5], object.ultimoAviso);
  writer.writeString(offsets[6], object.ventaId);
}

CreditoLocal _creditoLocalDeserialize(
  Id id,
  IsarReader reader,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  final object = CreditoLocal();
  object.clienteId = reader.readStringOrNull(offsets[0]);
  object.clienteNombre = reader.readStringOrNull(offsets[1]);
  object.estado = reader.readString(offsets[2]);
  object.fechaVencimiento = reader.readDateTimeOrNull(offsets[3]);
  object.id = id;
  object.saldo = reader.readDouble(offsets[4]);
  object.ultimoAviso = reader.readDateTimeOrNull(offsets[5]);
  object.ventaId = reader.readString(offsets[6]);
  return object;
}

P _creditoLocalDeserializeProp<P>(
  IsarReader reader,
  int propertyId,
  int offset,
  Map<Type, List<int>> allOffsets,
) {
  switch (propertyId) {
    case 0:
      return (reader.readStringOrNull(offset)) as P;
    case 1:
      return (reader.readStringOrNull(offset)) as P;
    case 2:
      return (reader.readString(offset)) as P;
    case 3:
      return (reader.readDateTimeOrNull(offset)) as P;
    case 4:
      return (reader.readDouble(offset)) as P;
    case 5:
      return (reader.readDateTimeOrNull(offset)) as P;
    case 6:
      return (reader.readString(offset)) as P;
    default:
      throw IsarError('Unknown property with id $propertyId');
  }
}

Id _creditoLocalGetId(CreditoLocal object) {
  return object.id;
}

List<IsarLinkBase<dynamic>> _creditoLocalGetLinks(CreditoLocal object) {
  return [];
}

void _creditoLocalAttach(
    IsarCollection<dynamic> col, Id id, CreditoLocal object) {
  object.id = id;
}

extension CreditoLocalByIndex on IsarCollection<CreditoLocal> {
  Future<CreditoLocal?> getByVentaId(String ventaId) {
    return getByIndex(r'ventaId', [ventaId]);
  }

  CreditoLocal? getByVentaIdSync(String ventaId) {
    return getByIndexSync(r'ventaId', [ventaId]);
  }

  Future<bool> deleteByVentaId(String ventaId) {
    return deleteByIndex(r'ventaId', [ventaId]);
  }

  bool deleteByVentaIdSync(String ventaId) {
    return deleteByIndexSync(r'ventaId', [ventaId]);
  }

  Future<List<CreditoLocal?>> getAllByVentaId(List<String> ventaIdValues) {
    final values = ventaIdValues.map((e) => [e]).toList();
    return getAllByIndex(r'ventaId', values);
  }

  List<CreditoLocal?> getAllByVentaIdSync(List<String> ventaIdValues) {
    final values = ventaIdValues.map((e) => [e]).toList();
    return getAllByIndexSync(r'ventaId', values);
  }

  Future<int> deleteAllByVentaId(List<String> ventaIdValues) {
    final values = ventaIdValues.map((e) => [e]).toList();
    return deleteAllByIndex(r'ventaId', values);
  }

  int deleteAllByVentaIdSync(List<String> ventaIdValues) {
    final values = ventaIdValues.map((e) => [e]).toList();
    return deleteAllByIndexSync(r'ventaId', values);
  }

  Future<Id> putByVentaId(CreditoLocal object) {
    return putByIndex(r'ventaId', object);
  }

  Id putByVentaIdSync(CreditoLocal object, {bool saveLinks = true}) {
    return putByIndexSync(r'ventaId', object, saveLinks: saveLinks);
  }

  Future<List<Id>> putAllByVentaId(List<CreditoLocal> objects) {
    return putAllByIndex(r'ventaId', objects);
  }

  List<Id> putAllByVentaIdSync(List<CreditoLocal> objects,
      {bool saveLinks = true}) {
    return putAllByIndexSync(r'ventaId', objects, saveLinks: saveLinks);
  }
}

extension CreditoLocalQueryWhereSort
    on QueryBuilder<CreditoLocal, CreditoLocal, QWhere> {
  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhere> anyId() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(const IdWhereClause.any());
    });
  }
}

extension CreditoLocalQueryWhere
    on QueryBuilder<CreditoLocal, CreditoLocal, QWhereClause> {
  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> idEqualTo(Id id) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IdWhereClause.between(
        lower: id,
        upper: id,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> idNotEqualTo(
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

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> idGreaterThan(
      Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.greaterThan(lower: id, includeLower: include),
      );
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> idLessThan(Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.lessThan(upper: id, includeUpper: include),
      );
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> idBetween(
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

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> ventaIdEqualTo(
      String ventaId) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'ventaId',
        value: [ventaId],
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> ventaIdNotEqualTo(
      String ventaId) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'ventaId',
              lower: [],
              upper: [ventaId],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'ventaId',
              lower: [ventaId],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'ventaId',
              lower: [ventaId],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'ventaId',
              lower: [],
              upper: [ventaId],
              includeUpper: false,
            ));
      }
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause>
      clienteIdIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'clienteId',
        value: [null],
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause>
      clienteIdIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.between(
        indexName: r'clienteId',
        lower: [null],
        includeLower: false,
        upper: [],
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause> clienteIdEqualTo(
      String? clienteId) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'clienteId',
        value: [clienteId],
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterWhereClause>
      clienteIdNotEqualTo(String? clienteId) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clienteId',
              lower: [],
              upper: [clienteId],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clienteId',
              lower: [clienteId],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clienteId',
              lower: [clienteId],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'clienteId',
              lower: [],
              upper: [clienteId],
              includeUpper: false,
            ));
      }
    });
  }
}

extension CreditoLocalQueryFilter
    on QueryBuilder<CreditoLocal, CreditoLocal, QFilterCondition> {
  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'clienteId',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'clienteId',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'clienteId',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'clienteId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'clienteId',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clienteId',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteIdIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'clienteId',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'clienteNombre',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'clienteNombre',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreEqualTo(
    String? value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreGreaterThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreLessThan(
    String? value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreBetween(
    String? lower,
    String? upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'clienteNombre',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'clienteNombre',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'clienteNombre',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'clienteNombre',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      clienteNombreIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'clienteNombre',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> estadoEqualTo(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoGreaterThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoLessThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> estadoBetween(
    String lower,
    String upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'estado',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'estado',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> estadoMatches(
      String pattern,
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'estado',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'estado',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      estadoIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'estado',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'fechaVencimiento',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'fechaVencimiento',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoEqualTo(DateTime? value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'fechaVencimiento',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoGreaterThan(
    DateTime? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'fechaVencimiento',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoLessThan(
    DateTime? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'fechaVencimiento',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      fechaVencimientoBetween(
    DateTime? lower,
    DateTime? upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'fechaVencimiento',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> idEqualTo(
      Id value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> idGreaterThan(
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

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> idLessThan(
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

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> idBetween(
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

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> saldoEqualTo(
    double value, {
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'saldo',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      saldoGreaterThan(
    double value, {
    bool include = false,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'saldo',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> saldoLessThan(
    double value, {
    bool include = false,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'saldo',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition> saldoBetween(
    double lower,
    double upper, {
    bool includeLower = true,
    bool includeUpper = true,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'saldo',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoIsNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNull(
        property: r'ultimoAviso',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoIsNotNull() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(const FilterCondition.isNotNull(
        property: r'ultimoAviso',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoEqualTo(DateTime? value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'ultimoAviso',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoGreaterThan(
    DateTime? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'ultimoAviso',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoLessThan(
    DateTime? value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'ultimoAviso',
        value: value,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ultimoAvisoBetween(
    DateTime? lower,
    DateTime? upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'ultimoAviso',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdEqualTo(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdGreaterThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdLessThan(
    String value, {
    bool include = false,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdBetween(
    String lower,
    String upper, {
    bool includeLower = true,
    bool includeUpper = true,
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'ventaId',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdStartsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.startsWith(
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdEndsWith(
    String value, {
    bool caseSensitive = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.endsWith(
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdContains(String value, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.contains(
        property: r'ventaId',
        value: value,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdMatches(String pattern, {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.matches(
        property: r'ventaId',
        wildcard: pattern,
        caseSensitive: caseSensitive,
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'ventaId',
        value: '',
      ));
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterFilterCondition>
      ventaIdIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        property: r'ventaId',
        value: '',
      ));
    });
  }
}

extension CreditoLocalQueryObject
    on QueryBuilder<CreditoLocal, CreditoLocal, QFilterCondition> {}

extension CreditoLocalQueryLinks
    on QueryBuilder<CreditoLocal, CreditoLocal, QFilterCondition> {}

extension CreditoLocalQuerySortBy
    on QueryBuilder<CreditoLocal, CreditoLocal, QSortBy> {
  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByClienteId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteId', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByClienteIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteId', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByClienteNombre() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteNombre', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      sortByClienteNombreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteNombre', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByEstado() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'estado', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByEstadoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'estado', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      sortByFechaVencimiento() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'fechaVencimiento', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      sortByFechaVencimientoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'fechaVencimiento', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortBySaldo() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'saldo', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortBySaldoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'saldo', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByUltimoAviso() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ultimoAviso', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      sortByUltimoAvisoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ultimoAviso', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByVentaId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ventaId', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> sortByVentaIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ventaId', Sort.desc);
    });
  }
}

extension CreditoLocalQuerySortThenBy
    on QueryBuilder<CreditoLocal, CreditoLocal, QSortThenBy> {
  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByClienteId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteId', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByClienteIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteId', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByClienteNombre() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteNombre', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      thenByClienteNombreDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'clienteNombre', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByEstado() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'estado', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByEstadoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'estado', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      thenByFechaVencimiento() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'fechaVencimiento', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      thenByFechaVencimientoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'fechaVencimiento', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenById() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenBySaldo() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'saldo', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenBySaldoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'saldo', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByUltimoAviso() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ultimoAviso', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy>
      thenByUltimoAvisoDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ultimoAviso', Sort.desc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByVentaId() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ventaId', Sort.asc);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QAfterSortBy> thenByVentaIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'ventaId', Sort.desc);
    });
  }
}

extension CreditoLocalQueryWhereDistinct
    on QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> {
  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctByClienteId(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'clienteId', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctByClienteNombre(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'clienteNombre',
          caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctByEstado(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'estado', caseSensitive: caseSensitive);
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct>
      distinctByFechaVencimiento() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'fechaVencimiento');
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctBySaldo() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'saldo');
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctByUltimoAviso() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'ultimoAviso');
    });
  }

  QueryBuilder<CreditoLocal, CreditoLocal, QDistinct> distinctByVentaId(
      {bool caseSensitive = true}) {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'ventaId', caseSensitive: caseSensitive);
    });
  }
}

extension CreditoLocalQueryProperty
    on QueryBuilder<CreditoLocal, CreditoLocal, QQueryProperty> {
  QueryBuilder<CreditoLocal, int, QQueryOperations> idProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'id');
    });
  }

  QueryBuilder<CreditoLocal, String?, QQueryOperations> clienteIdProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'clienteId');
    });
  }

  QueryBuilder<CreditoLocal, String?, QQueryOperations>
      clienteNombreProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'clienteNombre');
    });
  }

  QueryBuilder<CreditoLocal, String, QQueryOperations> estadoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'estado');
    });
  }

  QueryBuilder<CreditoLocal, DateTime?, QQueryOperations>
      fechaVencimientoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'fechaVencimiento');
    });
  }

  QueryBuilder<CreditoLocal, double, QQueryOperations> saldoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'saldo');
    });
  }

  QueryBuilder<CreditoLocal, DateTime?, QQueryOperations>
      ultimoAvisoProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'ultimoAviso');
    });
  }

  QueryBuilder<CreditoLocal, String, QQueryOperations> ventaIdProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'ventaId');
    });
  }
}
