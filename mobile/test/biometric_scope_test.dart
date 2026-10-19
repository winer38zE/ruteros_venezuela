import 'package:flutter_test/flutter_test.dart';
import 'package:ruteros_mobile/services/biometric_service.dart';

void main() {
  test('scopeKey separa país y usuario', () {
    expect(
      BiometricService.scopeKey('pais-co', 'Dueno'),
      'biometric:pais-co:dueno',
    );
    expect(
      BiometricService.scopeKey('pais-co', 'Dueno'),
      isNot(BiometricService.scopeKey('pais-ve', 'Dueno')),
    );
  });
}
