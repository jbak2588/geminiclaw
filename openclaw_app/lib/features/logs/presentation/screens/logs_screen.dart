import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/realtime/realtime_hub.dart';

class LogsScreen extends StatefulWidget {
  const LogsScreen({super.key});

  @override
  State<LogsScreen> createState() => _LogsScreenState();
}

class _LogsScreenState extends State<LogsScreen> {
  List<dynamic> _logs = [];
  String? _selectedFilename;
  String _content = 'Select a log file.';
  bool _loading = true;
  String _error = '';
  String _lastObservedTaskId = '';
  int _lastObservedTerminalLogCount = 0;

  @override
  void initState() {
    super.initState();
    _loadList();
  }

  Future<void> _loadList() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final response = await ApiClient.instance.getJson('/api/logs');
      _logs = response['logs'] as List<dynamic>? ?? [];
    } catch (e) {
      _error = '$e';
      _logs = [];
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _openLog(String filename) async {
    try {
      final response = await ApiClient.instance.getJson('/api/logs/$filename');
      if (!mounted) return;
      setState(() {
        _selectedFilename = filename;
        _content = response['content']?.toString() ?? '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _selectedFilename = filename;
        _content = '$e';
      });
    }
  }

  void _syncFromRealtime(RealtimeHub hub) {
    final latestTaskId = hub.latestTaskId;
    final latestLogFilename = latestTaskId.isEmpty ? null : 'task_$latestTaskId.txt';
    final hasNewTask = latestTaskId.isNotEmpty && latestTaskId != _lastObservedTaskId;
    final hasNewTerminalLog = hub.terminalLogs.length != _lastObservedTerminalLogCount;

    _lastObservedTaskId = latestTaskId;
    _lastObservedTerminalLogCount = hub.terminalLogs.length;

    if (!hasNewTask && !hasNewTerminalLog) {
      return;
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _loadList();
      if (_selectedFilename != null && _selectedFilename == latestLogFilename) {
        _openLog(_selectedFilename!);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final hub = RealtimeHub.instance;

    return AnimatedBuilder(
      animation: hub,
      builder: (context, _) {
        _syncFromRealtime(hub);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
              child: Text('System Logs', style: Theme.of(context).textTheme.headlineSmall),
            ),
            Expanded(
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border(right: BorderSide(color: Colors.grey.shade800)),
                      ),
                      child: _loading
                          ? const Center(child: CircularProgressIndicator())
                          : _error.isNotEmpty
                              ? Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Text(_error),
                                )
                              : ListView(
                                  children: _logs
                                      .map(
                                        (item) => ListTile(
                                          selected: _selectedFilename == item['filename'],
                                          title: Text(item['filename'].toString()),
                                          subtitle: Text('${item['size_bytes']} bytes'),
                                          onTap: () => _openLog(item['filename'].toString()),
                                        ),
                                      )
                                      .toList(),
                                ),
                    ),
                  ),
                  Expanded(
                    flex: 5,
                    child: Container(
                      color: const Color(0xFF171717),
                      padding: const EdgeInsets.all(16),
                      child: SingleChildScrollView(
                        child: SelectableText(
                          _content,
                          style: const TextStyle(fontFamily: 'monospace', color: Colors.greenAccent),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
