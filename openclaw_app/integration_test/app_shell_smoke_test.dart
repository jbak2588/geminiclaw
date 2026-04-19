import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:openclaw_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('main shell opens and primary sections render', (tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    expect(find.text('Dashboard'), findsWidgets);

    await tester.tap(find.text('Command').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Command Center'), findsOneWidget);

    await tester.tap(find.text('Workflow').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Workflow Live'), findsOneWidget);

    await tester.tap(find.text('Approvals').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Approval Center'), findsOneWidget);

    await tester.ensureVisible(find.text('Logs').first);
    await tester.tap(find.text('Logs').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('System Logs'), findsOneWidget);

    await tester.ensureVisible(find.text('Knowledge').first);
    await tester.tap(find.text('Knowledge').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Knowledge Library'), findsOneWidget);

    await tester.ensureVisible(find.text('Channels').first);
    await tester.tap(find.text('Channels').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Channel Hub'), findsOneWidget);

    await tester.ensureVisible(find.text('Departments').first);
    await tester.tap(find.text('Departments').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Department Teams'), findsOneWidget);

    await tester.ensureVisible(find.text('Settings').first);
    await tester.tap(find.text('Settings').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Settings'), findsWidgets);
  });
}
