import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/app_constants.dart';

class RealtimeHub extends ChangeNotifier {
  RealtimeHub._();

  static final RealtimeHub instance = RealtimeHub._();

  WebSocketChannel? _channel;
  bool isConnected = false;
  String activeNode = '';
  String latestTaskId = '';
  String latestTaskTitle = '';
  String latestStatus = '';
  List<Map<String, dynamic>> workflowNodes = [];
  List<Map<String, dynamic>> workflowEdges = [];
  List<Map<String, dynamic>> recentEvents = [];
  List<Map<String, dynamic>> pendingApprovals = [];
  List<String> terminalLogs = [];

  final String _clientId = 'dashboard_client';

  void ensureConnected() {
    if (_channel != null) return;
    _connect();
  }

  int get pendingApprovalCount => pendingApprovals.where((e) => e['status'] == 'pending').length;

  void _connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('${AppConstants.wsBaseUrl}/ws/$_clientId'),
    );

    isConnected = true;
    notifyListeners();

    _channel!.stream.listen(
      _handleMessage,
      onError: (_) {
        isConnected = false;
        notifyListeners();
        _reconnect();
      },
      onDone: () {
        isConnected = false;
        notifyListeners();
        _reconnect();
      },
    );
  }

  void _reconnect() {
    _channel = null;
    Future.delayed(const Duration(seconds: 2), _connect);
  }

  void _handleMessage(dynamic raw) {
    final data = jsonDecode(raw as String) as Map<String, dynamic>;
    final type = data['type']?.toString() ?? '';

    if (type == 'node_update') {
      workflowNodes = List<Map<String, dynamic>>.from(data['nodes'] ?? []);
      workflowEdges = List<Map<String, dynamic>>.from(data['edges'] ?? []);
      activeNode = data['active_node']?.toString() ?? '';
      latestTaskId = data['task_id']?.toString() ?? latestTaskId;
      latestTaskTitle = data['task_title']?.toString() ?? latestTaskTitle;
    } else if (type == 'task_event') {
      latestTaskId = data['task_id']?.toString() ?? latestTaskId;
      latestTaskTitle = data['task_title']?.toString() ?? latestTaskTitle;
      latestStatus = data['status']?.toString() ?? '';
      recentEvents.insert(0, data);
      terminalLogs.insert(0, '[${data['node']}] ${data['message']}');
    } else if (type == 'approval_request') {
      pendingApprovals.removeWhere((e) => e['approval_id'] == data['approval_id']);
      pendingApprovals.insert(0, data);
      terminalLogs.insert(0, '[APPROVAL] ${data['title']}');
    } else if (type == 'approval_resolved') {
      final approvalId = data['approval_id'];
      pendingApprovals = pendingApprovals.map((item) {
        if (item['approval_id'] == approvalId) {
          return {...item, 'status': data['status']};
        }
        return item;
      }).toList();
      terminalLogs.insert(0, '[APPROVAL] ${data['status']} - ${data['approval_id']}');
    } else if (type == 'log_append') {
      terminalLogs.insert(0, data['line']?.toString() ?? '');
    } else if (type == 'channel_event') {
      recentEvents.insert(0, data);
      terminalLogs.insert(0, '[CHANNEL:${data['channel']}] ${data['message']}');
    }

    if (terminalLogs.length > 200) {
      terminalLogs = terminalLogs.sublist(0, 200);
    }
    if (recentEvents.length > 100) {
      recentEvents = recentEvents.sublist(0, 100);
    }
    notifyListeners();
  }

  void disposeChannel() {
    _channel?.sink.close();
    _channel = null;
  }
}
