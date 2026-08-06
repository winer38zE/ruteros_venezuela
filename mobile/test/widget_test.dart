import 'package:flutter_test/flutter_test.dart';
import 'package:ruteros_mobile/app.dart';

void main() {
  testWidgets('Muestra pantalla de login al iniciar', (WidgetTester tester) async {
    await tester.pumpWidget(const RuterosApp());
    await tester.pumpAndSettle();

    expect(find.text('ED NET PRO'), findsOneWidget);
  });
}
