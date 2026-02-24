import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const OpenClawApp());
}

class OpenClawApp extends StatelessWidget {
  const OpenClawApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Agentic Team Platform',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueGrey,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final TextEditingController _taskController = TextEditingController();
  WebSocketChannel? _channel;
  final List<String> _logs = [];

  // Basic State Tracking
  bool _isConnecting = false;
  String _currentAgentNode = "Idle";
  String _workflowStatus = "Waiting for task...";

  void _startTask() {
    if (_taskController.text.isEmpty) return;

    setState(() {
      _logs.clear();
      _isConnecting = true;
      _workflowStatus = "Starting workflow...";
      _currentAgentNode = "Initializing";
    });

    // In a real app, generate a unique client ID
    final clientId = DateTime.now().millisecondsSinceEpoch.toString();

    // Connect to local FastAPI backend
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$clientId'),
    );

    // Send the task
    _channel!.sink.add(jsonEncode({"task": _taskController.text}));

    // Listen to streaming results
    _channel!.stream.listen(
      (message) {
        final data = jsonDecode(message);
        setState(() {
          if (data["type"] == "info") {
            _logs.add("[INFO] ${data['message']}");
          } else if (data["type"] == "agent_event") {
            _currentAgentNode = data["node"] ?? "Unknown Node";
            _workflowStatus = data["status"] ?? "Processing";
            _logs.add(
              "[${data['node']}] -> Status: ${data['status']}\n${data['message']}",
            );

            // Trigger approval dialog if dangerous operation detected
            if (data["message"] != null &&
                data["message"].toString().contains("APPROVAL_REQUIRED")) {
              _showApprovalDialog(data["message"].toString());
            }
          }
          _isConnecting = false;
        });
      },
      onError: (error) {
        setState(() {
          _logs.add("[ERROR] Connection failed: $error");
          _isConnecting = false;
          _workflowStatus = "Error";
        });
      },
      onDone: () {
        setState(() {
          _logs.add("[SYSTEM] WebSocket closed.");
          _isConnecting = false;
          if (_workflowStatus != "approved") {
            _workflowStatus = "Finished with ending state";
          }
        });
      },
    );
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _taskController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CTO Dashboard - Team of Agents'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Row(
        children: [
          // Left Panel: Task Input
          Expanded(
            flex: 1,
            child: Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: Colors.grey.shade800)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "New Objective (Epic)",
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _taskController,
                    maxLines: 5,
                    decoration: const InputDecoration(
                      hintText:
                          "Enter the project requirements, subtasks, or bug to fix...",
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _isConnecting ? null : _startTask,
                      icon: const Icon(Icons.rocket_launch),
                      label: const Text("Deploy Team"),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Middle Panel: Kanban/State Visualization
          Expanded(
            flex: 1,
            child: Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: Colors.grey.shade800)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Current Workflow State",
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 32),
                  _buildStateCard(
                    "Active Node",
                    _currentAgentNode,
                    Icons.computer,
                  ),
                  const SizedBox(height: 16),
                  _buildStateCard(
                    "Overall Status",
                    _workflowStatus,
                    Icons.timeline,
                  ),
                  const Spacer(),
                  if (_isConnecting ||
                      _workflowStatus == "Processing" ||
                      _workflowStatus == "needs_review" ||
                      _workflowStatus == "rejected")
                    const Center(child: CircularProgressIndicator()),
                  const Spacer(),
                ],
              ),
            ),
          ),

          // Right Panel: Live Terminal / Logs
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(16.0),
              color: Colors.black87,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Live Terminal & Thoughts",
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.greenAccent,
                    ),
                  ),
                  const Divider(color: Colors.green),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _logs.length,
                      itemBuilder: (context, index) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Text(
                            _logs[index],
                            style: const TextStyle(
                              fontFamily: 'Courier',
                              color: Colors.greenAccent,
                              fontSize: 12,
                            ),
                          ),
                        );
                      },
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

  void _showApprovalDialog(String message) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text(
          "Human-In-The-Loop Approval",
          style: TextStyle(color: Colors.orangeAccent),
        ),
        content: Text(
          "A dangerous command has been detected:\n\n$message\n\nDo you want to authorize it?",
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(
                jsonEncode({
                  "task":
                      "User REJECTED the command. Do not execute it and try another approach.",
                }),
              );
            },
            child: const Text("Reject", style: TextStyle(color: Colors.red)),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(
                jsonEncode({
                  "task":
                      "User APPROVED the command. Note: You can't actually bypass the prompt yet in this PoC, but assume it succeeded for demo.",
                }),
              );
            },
            child: const Text("Approve"),
          ),
        ],
      ),
    );
  }

  Widget _buildStateCard(String title, String value, IconData icon) {
    return Card(
      color: Colors.blueGrey.shade900,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Icon(icon, size: 40, color: Colors.blueAccent),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                  Text(
                    value,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
