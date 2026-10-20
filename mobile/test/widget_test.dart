import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ruteros_mobile/l10n/regional_copy.dart';
import 'package:ruteros_mobile/screens/welcome_onboarding_screen.dart';

void main() {
  test('Subtítulo de login (Venezuela)', () {
    expect(
      RegionalCopy.fromEsVenezuela(true).loginSubtitulo,
      'Controla tus ventas fiadas, cobros y rutas',
    );
  });

  test('Subtítulo de login (otros países)', () {
    expect(
      RegionalCopy.fromEsVenezuela(false).loginSubtitulo,
      'Controla tus ventas a crédito, cobros y rutas',
    );
  });

  testWidgets('Onboarding de bienvenida muestra primera diapositiva', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: WelcomeOnboardingScreen()));

    expect(find.text('Ventas a crédito'), findsOneWidget);
    expect(find.text('Saltar'), findsOneWidget);
    expect(find.text('Siguiente'), findsOneWidget);
  });
}
