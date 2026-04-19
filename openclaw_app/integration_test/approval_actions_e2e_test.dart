import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';
import 'package:openclaw_app/core/realtime/realtime_hub.dart';

import 'package:openclaw_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('approval actions resolve end-to-end for reject and approve paths', (
    tester,
  ) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 4));

    final rejectTitle =
        'Approval Reject ${DateTime.now().millisecondsSinceEpoch} publish approval';
    final rejectTaskId = await _createTaskFromCommandCenter(
      tester,
      rejectTitle,
    );
    final rejectApproval = await _waitForTaskApproval(
      taskId: rejectTaskId,
      expectedStatus: 'pending',
    );
    await _resolveFromApprovalCenter(
      tester,
      taskTitle: rejectTitle,
      actionLabel: 'Reject',
      expectedStatusLabel: 'rejected',
    );
    await _waitForTaskStatus(taskId: rejectTaskId, expectedStatus: 'rejected');
    await _waitForApprovalStatus(
      approvalId: rejectApproval['approval_id'].toString(),
      expectedStatus: 'rejected',
    );
    await _waitForRealtimeEvent(
      taskId: rejectTaskId,
      expectedStatus: 'rejected',
      timeout: const Duration(seconds: 25),
    );
    await _verifyLog(
      tester,
      taskId: rejectTaskId,
      requiredLine: 'Approval rejected by dashboard_owner',
    );

    final approveTitle =
        'Approval Approve ${DateTime.now().millisecondsSinceEpoch} publish approval';
    final approveTaskId = await _createTaskViaApi(approveTitle);
    final approveApproval = await _waitForTaskApproval(
      taskId: approveTaskId,
      expectedStatus: 'pending',
    );
    await _resolveFromApprovalCenter(
      tester,
      taskTitle: approveTitle,
      actionLabel: 'Approve',
      expectedStatusLabel: 'approved',
    );
    await _waitForTaskStatus(
      taskId: approveTaskId,
      expectedStatus: 'completed',
    );
    await _waitForApprovalStatus(
      approvalId: approveApproval['approval_id'].toString(),
      expectedStatus: 'approved',
    );
    await _waitForRealtimeEvent(
      taskId: approveTaskId,
      expectedStatus: 'approved',
      timeout: const Duration(seconds: 25),
    );
    await _verifyLog(
      tester,
      taskId: approveTaskId,
      requiredLine: 'Approval approved by dashboard_owner',
    );
  });
}

Future<String> _createTaskFromCommandCenter(
  WidgetTester tester,
  String taskTitle,
) async {
  await _openTab(tester, 'Command');
  expect(find.text('Command Center'), findsOneWidget);

  final beforeResponse = await _getJson('/api/tasks');
  final beforeCount = (beforeResponse['tasks'] as List<dynamic>? ?? []).length;

  await tester.enterText(find.byType(TextField).last, taskTitle);
  await tester.tap(find.text('Dispatch Task'));
  await tester.pump();

  late String createdTaskId;
  await _waitFor(() async {
    final tasksResponse = await _getJson('/api/tasks');
    final tasks = (tasksResponse['tasks'] as List<dynamic>? ?? [])
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
    final matched = tasks
        .where((task) => task['title']?.toString() == taskTitle)
        .toList();
    if (matched.isEmpty) {
      return false;
    }
    final hasNewTask = tasks.length > beforeCount;
    createdTaskId = matched.first['id']?.toString() ?? '';
    return hasNewTask && createdTaskId.isNotEmpty;
  }, timeout: const Duration(seconds: 20));

  return createdTaskId;
}

Future<String> _createTaskViaApi(String taskTitle) async {
  final projects = await _getJson('/api/projects');
  final teams = await _getJson('/api/teams');

  final projectList = (projects['projects'] as List<dynamic>? ?? [])
      .map((item) => Map<String, dynamic>.from(item as Map))
      .toList();
  final teamList = (teams['teams'] as List<dynamic>? ?? [])
      .map((item) => Map<String, dynamic>.from(item as Map))
      .toList();

  if (projectList.isEmpty || teamList.isEmpty) {
    throw TestFailure(
      'Cannot create task via API because projects/teams are empty.',
    );
  }

  final response = await _postJson('/api/tasks', {
    'title': taskTitle,
    'instruction': taskTitle,
    'project_id': projectList.first['id'],
    'team_id': teamList.first['id'],
    'source': 'dashboard',
  });
  final taskId = response['task_id']?.toString() ?? '';
  if (taskId.isEmpty) {
    throw TestFailure('Task ID missing from /api/tasks response: $response');
  }
  return taskId;
}

Future<void> _resolveFromApprovalCenter(
  WidgetTester tester, {
  required String taskTitle,
  required String actionLabel,
  required String expectedStatusLabel,
}) async {
  await _openTab(tester, 'Approvals');
  expect(find.text('Approval Center'), findsOneWidget);
  await _pumpUntilFound(
    tester,
    find.text('Task: $taskTitle'),
    timeout: const Duration(seconds: 30),
  );

  final cardFinder = find.ancestor(
    of: find.text('Task: $taskTitle').first,
    matching: find.byType(Card),
  );

  await _pumpUntilFound(
    tester,
    find.descendant(of: cardFinder.first, matching: find.text(actionLabel)),
    timeout: const Duration(seconds: 20),
  );
  await tester.tap(
    find
        .descendant(of: cardFinder.first, matching: find.text(actionLabel))
        .first,
  );
  await tester.pump();

  await _pumpUntilFound(
    tester,
    find.descendant(
      of: cardFinder.first,
      matching: find.textContaining('Status: $expectedStatusLabel'),
    ),
    timeout: const Duration(seconds: 20),
  );
}

Future<void> _verifyLog(
  WidgetTester tester, {
  required String taskId,
  required String requiredLine,
}) async {
  final filename = 'task_$taskId.txt';
  await _waitFor(() async {
    final logResponse = await _getJson('/api/logs/$filename');
    final content = logResponse['content']?.toString() ?? '';
    return content.contains(requiredLine);
  }, timeout: const Duration(seconds: 20));

  await _openTab(tester, 'Logs');
  expect(find.text('System Logs'), findsOneWidget);
  await _pumpUntilFound(
    tester,
    find.text(filename),
    timeout: const Duration(seconds: 25),
  );
  await tester.tap(find.text(filename).first);
  await tester.pumpAndSettle(const Duration(seconds: 1));
  await _pumpUntilFound(
    tester,
    find.textContaining(requiredLine),
    timeout: const Duration(seconds: 20),
  );
}

Future<void> _waitForTaskStatus({
  required String taskId,
  required String expectedStatus,
}) async {
  await _waitFor(() async {
    final task = await _getJson('/api/tasks/$taskId');
    return task['status'] == expectedStatus;
  }, timeout: const Duration(seconds: 40));
}

Future<Map<String, dynamic>> _waitForTaskApproval({
  required String taskId,
  required String expectedStatus,
}) async {
  late Map<String, dynamic> approval;
  await _waitFor(() async {
    final response = await _getJson('/api/approvals');
    final approvals = (response['approvals'] as List<dynamic>? ?? [])
        .map((item) => Map<String, dynamic>.from(item as Map))
        .where((item) => item['task_id']?.toString() == taskId)
        .toList();
    if (approvals.isEmpty) {
      return false;
    }
    approval = approvals.first;
    return approval['status']?.toString() == expectedStatus;
  }, timeout: const Duration(seconds: 30));
  return approval;
}

Future<void> _waitForApprovalStatus({
  required String approvalId,
  required String expectedStatus,
}) async {
  await _waitFor(() async {
    final response = await _getJson('/api/approvals');
    final approvals = (response['approvals'] as List<dynamic>? ?? []).map(
      (item) => Map<String, dynamic>.from(item as Map),
    );
    final matched = approvals
        .where((item) => item['approval_id']?.toString() == approvalId)
        .toList();
    if (matched.isEmpty) {
      return false;
    }
    return matched.first['status']?.toString() == expectedStatus;
  }, timeout: const Duration(seconds: 20));
}

Future<void> _waitForRealtimeEvent({
  required String taskId,
  required String expectedStatus,
  Duration timeout = const Duration(seconds: 20),
}) async {
  await _waitFor(() async {
    final hub = RealtimeHub.instance;
    return hub.recentEvents.any(
      (event) =>
          event['task_id']?.toString() == taskId &&
          event['status']?.toString() == expectedStatus,
    );
  }, timeout: timeout);
}

Future<void> _openTab(WidgetTester tester, String label) async {
  await tester.ensureVisible(find.text(label).first);
  await tester.tap(find.text(label).first);
  await tester.pumpAndSettle(const Duration(seconds: 1));
}

Future<Map<String, dynamic>> _getJson(String path) async {
  final response = await http
      .get(Uri.parse('http://127.0.0.1:8001$path'))
      .timeout(const Duration(seconds: 10));
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw TestFailure(
      'GET $path failed with ${response.statusCode}: ${response.body}',
    );
  }
  return jsonDecode(response.body) as Map<String, dynamic>;
}

Future<Map<String, dynamic>> _postJson(
  String path,
  Map<String, dynamic> body,
) async {
  final response = await http
      .post(
        Uri.parse('http://127.0.0.1:8001$path'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      )
      .timeout(const Duration(seconds: 10));
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw TestFailure(
      'POST $path failed with ${response.statusCode}: ${response.body}',
    );
  }
  return jsonDecode(response.body) as Map<String, dynamic>;
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
