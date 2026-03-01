import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class SystemLogsView extends StatefulWidget {
  const SystemLogsView({super.key});

  @override
  State<SystemLogsView> createState() => _SystemLogsViewState();
}

class _SystemLogsViewState extends State<SystemLogsView> {
  List<dynamic> _logs = [];
  bool _isLoading = false;

  String? _selectedFilename;
  String _logContent = "Select a log file to view details.";
  bool _isLoadingContent = false;

  @override
  void initState() {
    super.initState();
    _fetchLogsList();
  }

  Future<void> _fetchLogsList() async {
    setState(() => _isLoading = true);
    try {
      final res = await http.get(Uri.parse('http://localhost:8001/api/logs'));
      if (res.statusCode == 200) {
        setState(() {
          _logs = jsonDecode(res.body)['logs'] ?? [];
        });
      }
    } catch (e) {
      debugPrint("Error fetching logs: \$e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchLogContent(String filename) async {
    setState(() {
      _selectedFilename = filename;
      _isLoadingContent = true;
      _logContent = "Loading...";
    });

    try {
      final res = await http.get(
        Uri.parse('http://localhost:8001/api/logs/$filename'),
      );
      if (res.statusCode == 200) {
        setState(() {
          _logContent = jsonDecode(res.body)['content'] ?? "No content.";
        });
      } else {
        setState(() {
          _logContent = "Failed to load: ${res.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _logContent = "Error: $e";
      });
    } finally {
      setState(() => _isLoadingContent = false);
    }
  }

  String _formatDate(String timestampStr) {
    try {
      double ms = double.parse(timestampStr) * 1000;
      DateTime dt = DateTime.fromMillisecondsSinceEpoch(ms.toInt());
      return "${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    } catch (e) {
      return timestampStr;
    }
  }

  String _formatSize(String bytesStr) {
    try {
      int bytes = int.parse(bytesStr);
      if (bytes < 1024) return "$bytes B";
      if (bytes < 1024 * 1024) return "${(bytes / 1024).toStringAsFixed(1)} KB";
      return "${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB";
    } catch (e) {
      return bytesStr;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('System Logs'),
        backgroundColor: Colors.indigo.shade800,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _fetchLogsList();
              if (_selectedFilename != null) {
                _fetchLogContent(_selectedFilename!);
              }
            },
          ),
        ],
      ),
      body: Row(
        children: [
          // Left side: List
          Expanded(
            flex: 2,
            child: Container(
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: Colors.grey.shade800)),
              ),
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _logs.isEmpty
                  ? const Center(child: Text('No logs found.'))
                  : ListView.separated(
                      itemCount: _logs.length,
                      separatorBuilder: (context, index) =>
                          const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final log = _logs[index];
                        final isSelected = _selectedFilename == log['filename'];

                        return ListTile(
                          selected: isSelected,
                          selectedTileColor: Colors.indigo.shade900.withValues(
                            alpha: 0.5,
                          ),
                          leading: const Icon(
                            Icons.description,
                            color: Colors.grey,
                          ),
                          title: Text(
                            log['filename'] ?? '',
                            style: const TextStyle(fontSize: 14),
                          ),
                          subtitle: Text(
                            "${_formatDate(log['modified_at'])} • ${_formatSize(log['size_bytes'])}",
                            style: TextStyle(
                              color: Colors.grey.shade500,
                              fontSize: 12,
                            ),
                          ),
                          onTap: () => _fetchLogContent(log['filename']),
                        );
                      },
                    ),
            ),
          ),

          // Right side: Detail
          Expanded(
            flex: 5,
            child: Container(
              color: const Color(0xFF1E1E1E),
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_selectedFilename != null) ...[
                    Text(
                      _selectedFilename!,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    const Divider(),
                  ],
                  Expanded(
                    child: _isLoadingContent
                        ? const Center(child: CircularProgressIndicator())
                        : SingleChildScrollView(
                            child: SelectableText(
                              _logContent,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 13,
                                color: Colors.greenAccent,
                              ),
                            ),
                          ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
