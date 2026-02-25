import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http;
import 'screens/knowledge_screen.dart';
import 'screens/logs_screen.dart';

void main() {
  runApp(const OpenClawApp());
}

class OpenClawApp extends StatelessWidget {
  const OpenClawApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GeminiClaw - Company OS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const MainNavigationScreen(),
    );
  }
}

// ──────────────────────────────────────────────
// Shared Models
// ──────────────────────────────────────────────
class KanbanTask {
  final String id;
  final String agent;
  final String task;
  final String status;
  final String emoji;

  const KanbanTask({
    required this.id,
    required this.agent,
    required this.task,
    required this.status,
    required this.emoji,
  });

  factory KanbanTask.fromJson(Map<String, dynamic> json) {
    return KanbanTask(
      id: json['id'] as String? ?? '',
      agent: json['agent'] as String? ?? '',
      task: json['task'] as String? ?? '',
      status: json['status'] as String? ?? 'todo',
      emoji: json['emoji'] as String? ?? '📋',
    );
  }

  KanbanTask copyWith({String? status}) {
    return KanbanTask(
      id: id,
      agent: agent,
      task: task,
      status: status ?? this.status,
      emoji: emoji,
    );
  }
}

class ChatMessage {
  final String role; // "user" or "assistant" or "system"
  final String text;

  ChatMessage({required this.role, required this.text});
}

// ──────────────────────────────────────────────
// MAIN NAVIGATION WRAPPER (Dual Mode)
// ──────────────────────────────────────────────
class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            backgroundColor: Colors.indigo.shade900.withOpacity(0.5),
            selectedIndex: _selectedIndex,
            onDestinationSelected: (int index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.chat_bubble_outline),
                selectedIcon: Icon(Icons.chat_bubble),
                label: Text('Pi Assistant'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.dashboard_customize_outlined),
                selectedIcon: Icon(Icons.dashboard_customize),
                label: Text('Team OS'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.library_books_outlined),
                selectedIcon: Icon(Icons.library_books),
                label: Text('Knowledge Library'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.dvr_outlined),
                selectedIcon: Icon(Icons.dvr),
                label: Text('System Logs'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          // Main Content
          Expanded(
            child: IndexedStack(
              index: _selectedIndex,
              children: const [
                PiChatView(),
                TeamOrchestratorView(),
                KnowledgeLibraryView(),
                SystemLogsView(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ──────────────────────────────────────────────
// MODE 1: Pi Assistant (1:1 Chat)
// ──────────────────────────────────────────────
class PiChatView extends StatefulWidget {
  const PiChatView({super.key});

  @override
  State<PiChatView> createState() => _PiChatViewState();
}

class _PiChatViewState extends State<PiChatView> {
  final TextEditingController _msgController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  WebSocketChannel? _channel;
  bool _isConnecting = false;
  final String _clientId = "pi_client_${DateTime.now().millisecondsSinceEpoch}";

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  void _connectWebSocket() {
    setState(() => _isConnecting = true);
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8001/ws/$_clientId'),
    );
    _channel!.stream.listen(_onMessage, onError: _onError, onDone: _onDone);
    setState(() => _isConnecting = false);
    
    _messages.add(ChatMessage(role: "system", text: "Connected to Pi Agent. Ready to assist."));
  }

  void _onMessage(dynamic message) {
    final data = jsonDecode(message as String) as Map<String, dynamic>;
    final type = data['type'] as String? ?? '';

    setState(() {
      if (type == 'agent_event' && data['node'] == 'pi') {
        _messages.add(ChatMessage(role: "assistant", text: data['message'] ?? ''));
        _scrollToBottom();
      } else if (type == 'approval_request') {
        _messages.add(ChatMessage(role: "system", text: "⚠️ HITL Approval Required: ${data['command']}"));
        _showApprovalDialog(data['command'] as String? ?? '', data['message']?.toString() ?? '');
      } else if (type == 'agent_event' && data['node'] == 'system') {
        _messages.add(ChatMessage(role: "system", text: data['message'] ?? ''));
      }
    });
  }

  void _onError(dynamic error) {
    setState(() => _messages.add(ChatMessage(role: "system", text: "Connection error: $error")));
  }

  void _onDone() {
    setState(() => _messages.add(ChatMessage(role: "system", text: "Disconnected. Reconnecting...")));
    Future.delayed(const Duration(seconds: 3), _connectWebSocket);
  }

  void _sendMessage() {
    if (_msgController.text.trim().isEmpty) return;
    final text = _msgController.text.trim();
    setState(() {
      _messages.add(ChatMessage(role: "user", text: text));
      _msgController.clear();
    });
    _channel?.sink.add(jsonEncode({
      "type": "pi_chat",
      "message": text
    }));
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showApprovalDialog(String command, String reason) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.grey.shade900,
        title: const Text('⚠️ CTO 승인 필요', style: TextStyle(color: Colors.orangeAccent)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('위험한 명령어가 감지되었습니다:'),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red.shade900.withOpacity(0.3),
              child: Text('\$ $command', style: const TextStyle(color: Colors.redAccent, fontFamily: 'Courier')),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(jsonEncode({'type': 'approval_response', 'approved': false, 'command': command}));
            },
            child: const Text('❌ 거절', style: TextStyle(color: Colors.red)),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(jsonEncode({'type': 'approval_response', 'approved': true, 'command': command}));
            },
            style: FilledButton.styleFrom(backgroundColor: Colors.orange.shade800),
            child: const Text('✅ 승인'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _msgController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pi Assistant (Phase 0)'),
        backgroundColor: Colors.black45,
        elevation: 0,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg.role == 'user';
                final isSystem = msg.role == 'system';
                
                return Align(
                  alignment: isUser ? Alignment.centerRight : (isSystem ? Alignment.center : Alignment.centerLeft),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.6),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.indigo.shade600 : (isSystem ? Colors.black45 : Colors.grey.shade800),
                      borderRadius: BorderRadius.circular(12),
                      border: isSystem ? Border.all(color: Colors.orange.withOpacity(0.5)) : null,
                    ),
                    child: Text(
                      msg.text,
                      style: TextStyle(
                        color: isSystem ? Colors.orangeAccent : Colors.white,
                        fontFamily: isSystem ? 'Courier' : null,
                        fontSize: isSystem ? 12 : 14,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.black26,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _msgController,
                    decoration: InputDecoration(
                      hintText: 'Ask Pi to execute local tasks, manage clipboard, etc...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      filled: true,
                      fillColor: Colors.grey.shade900,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 12),
                CircleAvatar(
                  radius: 24,
                  backgroundColor: Colors.indigoAccent,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _sendMessage,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}

// ──────────────────────────────────────────────
// MODE 2: Team Orchestrator (Phase 1 & 2 REST API)
// ──────────────────────────────────────────────
class TeamOrchestratorView extends StatefulWidget {
  const TeamOrchestratorView({super.key});

  @override
  State<TeamOrchestratorView> createState() => _TeamOrchestratorViewState();
}

class _TeamOrchestratorViewState extends State<TeamOrchestratorView> {
  final TextEditingController _taskController = TextEditingController();
  final TextEditingController _companyDescController = TextEditingController(); // Added for dynamic setup
  WebSocketChannel? _channel;
  final List<String> _logs = [];

  bool _isWorkflowRunning = false;
  String _currentAgentNode = 'Idle';
  String _workflowStatus = 'Waiting for input...';
  
  List<KanbanTask> _kanbanTasks = [];
  
  // REST API Data & Dynamic Org Chart
  List<dynamic> _projects = [];
  List<dynamic> _teamPresets = [];
  Map<String, dynamic>? _generatedOrgChart; // Holds the AI generated setup
  String? _selectedProjectId;
  String? _selectedTeamId;
  final String _clientId = "team_client_${DateTime.now().millisecondsSinceEpoch}";

  @override
  void initState() {
    super.initState();
    _fetchRESTData();
  }
  
  Future<void> _fetchRESTData() async {
    try {
      final projRes = await http.get(Uri.parse('http://localhost:8001/api/projects'));
      final teamRes = await http.get(Uri.parse('http://localhost:8001/api/teams'));
      
      if (projRes.statusCode == 200) {
        setState(() {
          _projects = jsonDecode(projRes.body)['projects'];
        });
      }
      if (teamRes.statusCode == 200) {
        setState(() {
          _teamPresets = jsonDecode(teamRes.body)['teams'];
          if (_teamPresets.isEmpty) {
            // Provide a default if backend empty just for UI validation
            _teamPresets = [{"id": "default", "name": "Default Pair (Dev+Reviewer)", "config": [{"name": "developer"}]}];
          }
        });
      }
    } catch (e) {
      _logs.add("[API ERROR] Could not fetch projects/teams: $e");
    }
  }

  Future<void> _createProject(String name) async {
    try {
      final res = await http.post(
        Uri.parse('http://localhost:8001/api/projects'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"name": name, "description": "Created from Frontend"}),
      );
      if (res.statusCode == 200) {
        await _fetchRESTData();
        setState(() {
          _selectedProjectId = jsonDecode(res.body)['id'];
        });
      }
    } catch (e) {
      _logs.add("[API ERROR] Failed to create project: $e");
    }
  }

  void _connectWebSocket() {
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8001/ws/$_clientId'),
    );
    _channel!.stream.listen(_onMessage, onError: _onError, onDone: _onDone);
  }

  void _onMessage(dynamic message) {
    final data = jsonDecode(message as String) as Map<String, dynamic>;
    setState(() {
      final type = data['type'] as String? ?? '';

      if (type == 'info') {
        _logs.add('[INFO] ${data['message']}');
        if (data['message']?.toString().contains('Completed') == true) {
          _isWorkflowRunning = false;
          _kanbanTasks = _kanbanTasks.map((t) {
            if (t.status == 'in_progress' || t.status == 'review') {
              return t.copyWith(status: 'done');
            }
            return t;
          }).toList();
        }
      } else if (type == 'approval_request') {
        _currentAgentNode = data['node'] as String? ?? 'worker';
        _workflowStatus = 'awaiting_approval';
        _logs.add('[${data['node']}] ⚠️ ${data['message']}');
        _showApprovalDialog(data['command'] as String? ?? '', data['message']?.toString() ?? '');
      } else if (type == 'agent_event') {
        _currentAgentNode = data['node'] as String? ?? 'Unknown';
        _workflowStatus = data['status'] as String? ?? 'Processing';
        _logs.add('[${data['node']}] → ${data['status']}\n${data['message']}');
      } else if (type == 'kanban_update') {
        final taskList = data['tasks'] as List?;
        if (taskList != null) {
          _kanbanTasks = taskList.map((t) => KanbanTask.fromJson(Map<String, dynamic>.from(t as Map))).toList();
        }
      } else if (type == 'org_chart_response') {
        _logs.add('[SYSTEM] AI Org Chart Received!');
        _generatedOrgChart = data['data'] as Map<String, dynamic>?;
        
        // Auto-select the newly generated org chart format as a 'team preset'
        if (_generatedOrgChart != null && _generatedOrgChart!['departments'] != null) {
            List<dynamic> depts = _generatedOrgChart!['departments'];
            List<Map<String, String>> newConfig = [];
            for (var d in depts) {
                if (d['default_enabled'] == true && d['agents'] != null && (d['agents'] as List).isNotEmpty) {
                    newConfig.add({"name": d['agents'][0]});
                }
            }
            if (newConfig.isNotEmpty) {
                 _teamPresets.insert(0, {
                     "id": "dynamic_ai", 
                     "name": "🌟 AI Generated Org", 
                     "config": newConfig
                 });
                 _selectedTeamId = "dynamic_ai";
            }
        }
      }
    });
  }

  void _onError(dynamic error) {
    setState(() {
      _logs.add('[ERROR] $error');
      _isWorkflowRunning = false;
    });
  }

  void _onDone() {
    setState(() {
      _logs.add('[SYSTEM] WebSocket closed.');
      _isWorkflowRunning = false;
    });
  }

  void _requestAiOrgChart() {
    if (_companyDescController.text.trim().isEmpty) return;
    
    // Ensure we have a project to bound the skills to
    if (_selectedProjectId == null) {
      _logs.add("[WARNING] Please select or create a project first so AI knows where to save the manuals.");
      return;
    }

    _logs.add("[SYSTEM] Requesting AI to build org chart and skill manuals...");
    _connectWebSocket();
    _channel!.sink.add(jsonEncode({
      'type': 'org_chart_request',
      'company_description': _companyDescController.text,
      'project_id': _selectedProjectId
    }));
  }

  void _deployTeam() {
    if (_taskController.text.isEmpty) return;
    String finalProjectId = _selectedProjectId ?? _clientId;
    
    // Find selected team config
    List<dynamic> targetConfig = [{"name": "developer"}]; // fallback
    if (_selectedTeamId != null) {
      final team = _teamPresets.firstWhere((t) => t['id'] == _selectedTeamId, orElse: () => null);
      if (team != null && team['config'] != null) {
        targetConfig = team['config'];
      }
    }

    setState(() {
      _logs.clear();
      _kanbanTasks = [];
      _isWorkflowRunning = true;
      _workflowStatus = 'Starting workflow...';
      _currentAgentNode = 'PM';
    });

    _connectWebSocket();
    // Send standard task + thread_id for Checkpointer state retention
    _channel!.sink.add(jsonEncode({
      'task': _taskController.text, 
      'team': targetConfig,
      'thread_id': finalProjectId
    }));
  }

  void _showApprovalDialog(String command, String reason) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.grey.shade900,
        title: const Text('⚠️ CTO 승인 필요', style: TextStyle(color: Colors.orangeAccent)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('위험한 명령어가 감지되었습니다:'),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red.shade900.withOpacity(0.3),
              child: Text('\$ $command', style: const TextStyle(color: Colors.redAccent, fontFamily: 'Courier')),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(jsonEncode({'type': 'approval_response', 'approved': false, 'command': command}));
            },
            child: const Text('❌ 거절', style: TextStyle(color: Colors.red)),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(jsonEncode({'type': 'approval_response', 'approved': true, 'command': command}));
            },
            style: FilledButton.styleFrom(backgroundColor: Colors.orange.shade800),
            child: const Text('✅ 승인'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _taskController.dispose();
    _companyDescController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // ═══════════════════════════════════════════
        // LEFT PANEL: Project & Team Setup
        // ═══════════════════════════════════════════
        Expanded(
          flex: 3,
          child: Container(
            padding: const EdgeInsets.all(20.0),
            decoration: BoxDecoration(border: Border(right: BorderSide(color: Colors.grey.shade800))),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("1. Workspace (Memory)", style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  decoration: const InputDecoration(labelText: 'Select Project context...', border: OutlineInputBorder()),
                  value: _selectedProjectId,
                  items: [
                    const DropdownMenuItem(value: null, child: Text("Create New Temporary Project")),
                    ..._projects.map((p) => DropdownMenuItem(value: p['id'].toString(), child: Text(p['name'].toString())))
                  ],
                  onChanged: (v) => setState(() => _selectedProjectId = v),
                ),
                TextButton.icon(onPressed: _showNewProjectDialog, icon: const Icon(Icons.add, size: 16), label: const Text("Create Global Project")),
                
                const Divider(),
                
                Text("2. AI Org & Skills Builder", style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: _companyDescController,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Describe company target & goals (e.g. "We are an indie game studio building a 2D RPG")',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: _requestAiOrgChart,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Generate Custom Org & Skills'),
                ),
                
                const Divider(height: 32),
                
                Text("3. Final Team Preset", style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  decoration: const InputDecoration(labelText: 'Verify Team Loadout', border: OutlineInputBorder()),
                  value: _selectedTeamId,
                  items: [
                    const DropdownMenuItem(value: null, child: Text("Default Dev Team")),
                    ..._teamPresets.map((t) => DropdownMenuItem(value: t['id'].toString(), child: Text(t['name'].toString())))
                  ],
                  onChanged: (v) => setState(() => _selectedTeamId = v),
                ),
                
                const Spacer(),
                
                Text('Task Instruction', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: _taskController,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    hintText: 'e.g. Build a new React button component...',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: FilledButton.icon(
                    onPressed: _isWorkflowRunning ? null : _deployTeam,
                    icon: const Icon(Icons.rocket_launch, size: 22),
                    label: const Text('Deploy Team'),
                    style: FilledButton.styleFrom(backgroundColor: Colors.deepOrange.shade700),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ═══════════════════════════════════════════
        // CENTER PANEL: Kanban Board
        // ═══════════════════════════════════════════
        Expanded(
          flex: 5,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.grey.shade900,
              border: Border(right: BorderSide(color: Colors.grey.shade800)),
            ),
            child: _kanbanTasks.isEmpty 
              ? Center(child: Text("Deploy a team to see the Kanban board.", style: TextStyle(color: Colors.grey.shade600)))
              : _buildKanbanBoard(),
          ),
        ),

        // ═══════════════════════════════════════════
        // RIGHT PANEL: Live Terminal
        // ═══════════════════════════════════════════
        Expanded(
          flex: 4,
          child: Container(
            padding: const EdgeInsets.all(16.0),
            color: Colors.black87,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.circle, size: 10, color: _isWorkflowRunning ? Colors.greenAccent : Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(child: Text('Active: $_currentAgentNode  |  Status: $_workflowStatus', style: TextStyle(color: Colors.grey.shade400, fontSize: 11, fontFamily: 'Courier'))),
                    if (_isWorkflowRunning) const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                  ],
                ),
                const Divider(color: Colors.green),
                Expanded(
                  child: ListView.builder(
                    itemCount: _logs.length,
                    itemBuilder: (context, index) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8.0),
                        child: Text(_logs[index], style: const TextStyle(fontFamily: 'Courier', color: Colors.greenAccent, fontSize: 11)),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _showNewProjectDialog() {
    final tc = TextEditingController();
    showDialog(
      context: context, 
      builder: (ctx) => AlertDialog(
        title: const Text("New Project"),
        content: TextField(controller: tc, decoration: const InputDecoration(labelText: 'Project Name')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          FilledButton(onPressed: () { _createProject(tc.text); Navigator.pop(ctx); }, child: const Text("Create"))
        ],
      )
    );
  }

  // Simplified Kanban Board
  Widget _buildKanbanBoard() {
    const columns = [
      {'key': 'todo', 'label': 'TODO', 'icon': '📋'},
      {'key': 'in_progress', 'label': 'IN PROGRESS', 'icon': '⚡'},
      {'key': 'review', 'label': 'REVIEW', 'icon': '🔍'},
      {'key': 'done', 'label': 'DONE', 'icon': '✅'},
    ];

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          color: Colors.indigo.shade900.withOpacity(0.5),
          child: const Row(children: [Icon(Icons.view_kanban, color: Colors.indigoAccent), SizedBox(width: 8), Text('Team Kanban Board', style: TextStyle(fontWeight: FontWeight.bold))]),
        ),
        Expanded(
          child: Row(
            children: columns.map((col) {
              final tasks = _kanbanTasks.where((t) => t.status == col['key']).toList();
              return Expanded(
                child: Container(
                  decoration: BoxDecoration(border: Border(right: BorderSide(color: Colors.grey.shade800))),
                  child: Column(
                    children: [
                      Container(padding: const EdgeInsets.all(8), child: Text("${col['icon']} ${col['label']} (${tasks.length})", style: TextStyle(color: Colors.grey.shade400, fontSize: 12))),
                      Expanded(
                        child: ListView(
                          padding: const EdgeInsets.all(8),
                          children: tasks.map((t) => Card(
                            color: col['key'] == 'in_progress' ? Colors.blue.shade900.withOpacity(0.5) : Colors.grey.shade800,
                            child: Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Row(children: [Text(t.emoji), const SizedBox(width: 4), Text(t.agent.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12))]),
                                const SizedBox(height: 8),
                                Text(t.task, style: const TextStyle(fontSize: 11)),
                              ]),
                            ),
                          )).toList(),
                        ),
                      )
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}
