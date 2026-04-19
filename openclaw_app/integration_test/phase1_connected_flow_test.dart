import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';

import 'package:openclaw_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('phase-1 desktop shell stays connected to the backend', (tester) async {
    final beforeOverview = await _getJson('/api/dashboard/overview');
    final taskTitle = 'Desktop Integration ${DateTime.now().millisecondsSinceEpoch} publish approval';

    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 4));

    expect(find.text('Dashboard'), findsWidgets);
    await _pumpUntilFound(
      tester,
      _metricValueFinder('Tasks', '${beforeOverview['tasks_count']}'),
    );
    await _pumpUntilFound(
      tester,
      _metricValueFinder('Pending Approvals', '${beforeOverview['pending_approvals']}'),
    );

    await tester.tap(find.text('Command').first);
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Command Center'), findsOneWidget);

    await tester.enterText(find.byType(TextField).last, taskTitle);
    await tester.tap(find.text('Dispatch Task'));
    await tester.pump();
    await _pumpUntilFound(tester, find.textContaining('Task created:'), timeout: const Duration(seconds: 12));

    final responseText = tester.widget<Text>(find.textContaining('Task created:').first).data ?? '';
    final taskIdMatch = RegExp(r'Task created: ([a-z0-9-]+)$').firstMatch(responseText);
    expect(taskIdMatch, isNotNull);
    final taskId = taskIdMatch!.group(1)!;

    await _waitFor(
      () async {
        final task = await _getJson('/api/tasks/$taskId');
        return task['id'] == taskId;
      },
      timeout: const Duration(seconds: 10),
    );

    await tester.tap(find.text('Workflow').first);
    await tester.pumpAndSettle(const Duration(seconds: 1));
    expect(find.text('Workflow Live'), findsOneWidget);
    await _pumpUntilFound(
      tester,
      find.text('Task: $taskTitle'),
      timeout: const Duration(seconds: 20),
    );
    await _pumpUntilFound(
      tester,
      find.text('Control'),
      timeout: const Duration(seconds: 10),
    );

    await tester.tap(find.text('Approvals').first);
    await tester.pumpAndSettle(const Duration(seconds: 1));
    expect(find.text('Approval Center'), findsOneWidget);
    await _pumpUntilFound(
      tester,
      find.text('Task: $taskTitle'),
      timeout: const Duration(seconds: 20),
    );

    await tester.tap(find.text('Logs').first);
    await tester.pumpAndSettle(const Duration(seconds: 1));
    expect(find.text('System Logs'), findsOneWidget);
    await _pumpUntilFound(
      tester,
      find.text('task_$taskId.txt'),
      timeout: const Duration(seconds: 20),
    );
    await tester.tap(find.text('task_$taskId.txt'));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    final logText = tester.widget<SelectableText>(find.byType(SelectableText).first).data ?? '';
    expect(logText, contains(taskTitle));

    final afterOverview = await _waitForOverviewGrowth(
      beforeTasks: beforeOverview['tasks_count'] as int? ?? 0,
      beforePendingApprovals: beforeOverview['pending_approvals'] as int? ?? 0,
    );

    await tester.tap(find.text('Dashboard').first);
    await tester.pumpAndSettle(const Duration(seconds: 1));
    await tester.drag(find.byType(ListView).first, const Offset(0, 300));
    await tester.pump();
    await tester.pump(const Duration(seconds: 2));
    await _pumpUntilFound(
      tester,
      _metricValueFinder('Tasks', '${afterOverview['tasks_count']}'),
      timeout: const Duration(seconds: 10),
    );
    await _pumpUntilFound(
      tester,
      _metricValueFinder('Pending Approvals', '${afterOverview['pending_approvals']}'),
      timeout: const Duration(seconds: 10),
    );
  });
}

Finder _metricValueFinder(String title, String value) {
  final cardFinder = find.ancestor(
    of: find.text(title),
    matching: find.byType(Card),
  );
  return find.descendant(of: cardFinder.first, matching: find.text(value));
}

Future<Map<String, dynamic>> _getJson(String path) async {
  final response = await http
      .get(Uri.parse('http://127.0.0.1:8001$path'))
      .timeout(const Duration(seconds: 10));
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw TestFailure('GET $path failed with ${response.statusCode}: ${response.body}');
  }
  return jsonDecode(response.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> _waitForOverviewGrowth({
  required int beforeTasks,
  required int beforePendingApprovals,
}) async {
  late Map<String, dynamic> overview;
  await _waitFor(
    () async {
      overview = await _getJson('/api/dashboard/overview');
      return (overview['tasks_count'] as int? ?? 0) > beforeTasks &&
          (overview['pending_approvals'] as int? ?? 0) > beforePendingApprovals;
    },
    timeout: const Duration(seconds: 20),
  );
  return overview;
}

Future<void> _waitFor(
  Future<bool> Function() condition, {
  Duration timeout = const Duration(seconds: 15),
  Duration interval = const Duration(milliseconds: 400),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    if (await condition()) {
      return;
    }
    await Future<void>.delayed(interval);
  }
  throw TestFailure('Condition not met within $timeout');
}

Future<void> _pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 10),
  Duration step = const Duration(milliseconds: 300),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    await tester.pump(step);
    if (finder.evaluate().isNotEmpty) {
      return;
    }
  }
  throw TestFailure('Finder not found within $timeout: $finder');
}
