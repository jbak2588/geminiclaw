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
      title: 'GeminiClaw - Company OS',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}

// ──────────────────────────────────────────────
// Pre-built company profiles
// ──────────────────────────────────────────────
final Map<String, Map<String, String>> companyProfiles = {
  'pt_humantric': {
    'name': 'PT Humantric Net Indonesia',
    'type': 'PMA (외국인 투자 법인)',
    'kbli': '63122',
    'product': 'Mozzy - 하이퍼로컬 커뮤니티 슈퍼앱',
  },
};

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final TextEditingController _taskController = TextEditingController();
  WebSocketChannel? _channel;
  final List<String> _logs = [];

  // ── State Tracking ──
  bool _isWorkflowRunning = false;
  String _currentAgentNode = "Idle";
  String _workflowStatus = "조직 구성 대기 중...";

  // ── Setup Wizard State ──
  int _setupStep = 0; // 0=company, 1=org chart, 2=ready
  final String _selectedCompanyId = 'pt_humantric';
  List<Map<String, dynamic>> _departments = [];
  bool _isGeneratingOrgChart = false;

  void _connectWebSocket() {
    final clientId = DateTime.now().millisecondsSinceEpoch.toString();
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$clientId'),
    );
    _channel!.stream.listen(_onMessage, onError: _onError, onDone: _onDone);
  }

  void _onMessage(dynamic message) {
    final data = jsonDecode(message);
    setState(() {
      final type = data["type"] ?? "";

      if (type == "org_chart_response") {
        _isGeneratingOrgChart = false;
        final orgData = data["data"] as Map<String, dynamic>?;
        if (orgData != null && orgData.containsKey("departments")) {
          _departments = (orgData["departments"] as List)
              .map((d) => Map<String, dynamic>.from(d))
              .toList();
          _setupStep = 1; // Move to org chart selection
        }
      } else if (type == "info") {
        _logs.add("[INFO] ${data['message']}");
        if (data['message']?.toString().contains('Completed') == true) {
          _isWorkflowRunning = false;
        }
      } else if (type == "approval_request") {
        _currentAgentNode = data["node"] ?? "worker";
        _workflowStatus = "awaiting_approval";
        _logs.add("[${data['node']}] ⚠️ ${data['message']}");
        _showApprovalDialog(
          data["command"] ?? "",
          data["message"]?.toString() ?? "",
        );
      } else if (type == "agent_event") {
        _currentAgentNode = data["node"] ?? "Unknown";
        _workflowStatus = data["status"] ?? "Processing";
        _logs.add("[${data['node']}] → ${data['status']}\n${data['message']}");
      }
    });
  }

  void _onError(dynamic error) {
    setState(() {
      _logs.add("[ERROR] $error");
      _isWorkflowRunning = false;
      _isGeneratingOrgChart = false;
    });
  }

  void _onDone() {
    setState(() {
      _logs.add("[SYSTEM] WebSocket closed.");
      _isWorkflowRunning = false;
    });
  }

  // ── Step 1: Request AI Org Chart ──
  void _requestOrgChart() {
    setState(() {
      _isGeneratingOrgChart = true;
    });
    _connectWebSocket();

    final docDir = r'E:\geminiclaw\doc';
    _channel!.sink.add(
      jsonEncode({
        "type": "org_chart_request",
        "profile_id": _selectedCompanyId,
        "whitepaper_dir": docDir,
      }),
    );
  }

  // ── Step 2: Deploy Team ──
  void _deployTeam() {
    if (_taskController.text.isEmpty) return;

    // Build team from enabled departments
    final enabledDepts = _departments
        .where((d) => d['enabled'] == true)
        .toList();
    final teamConfig = <Map<String, String>>[];
    for (final dept in enabledDepts) {
      final agents = dept['agents'] as List? ?? [dept['id']];
      for (final agentName in agents) {
        teamConfig.add({'name': agentName.toString()});
      }
    }

    if (teamConfig.isEmpty) {
      teamConfig.add({'name': 'developer'});
    }

    setState(() {
      _logs.clear();
      _isWorkflowRunning = true;
      _workflowStatus = "Starting workflow...";
      _currentAgentNode = "PM";
    });

    // Reconnect for task flow
    _connectWebSocket();

    _channel!.sink.add(
      jsonEncode({"task": _taskController.text, "team": teamConfig}),
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
        title: const Text('🏢 GeminiClaw - Company OS'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (_setupStep > 0)
            TextButton.icon(
              onPressed: () => setState(() {
                _setupStep = 0;
                _departments.clear();
              }),
              icon: const Icon(Icons.restart_alt, size: 18),
              label: const Text("Reset"),
            ),
        ],
      ),
      body: Row(
        children: [
          // ═══════════════════════════════════════════
          // LEFT PANEL: Setup Wizard + Task Input
          // ═══════════════════════════════════════════
          Expanded(
            flex: 3,
            child: Container(
              padding: const EdgeInsets.all(20.0),
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: Colors.grey.shade800)),
              ),
              child: SingleChildScrollView(child: _buildLeftPanel()),
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
                  // Status bar
                  Row(
                    children: [
                      Icon(
                        Icons.circle,
                        size: 10,
                        color: _isWorkflowRunning
                            ? Colors.greenAccent
                            : Colors.grey,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        "Active: $_currentAgentNode  |  Status: $_workflowStatus",
                        style: TextStyle(
                          color: Colors.grey.shade400,
                          fontSize: 12,
                          fontFamily: 'Courier',
                        ),
                      ),
                      const Spacer(),
                      if (_isWorkflowRunning)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                    ],
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

  // ═══════════════════════════════════════════════
  // LEFT PANEL BUILDER
  // ═══════════════════════════════════════════════
  Widget _buildLeftPanel() {
    switch (_setupStep) {
      case 0:
        return _buildStepCompanySelect();
      case 1:
        return _buildStepOrgChart();
      case 2:
        return _buildStepDeploy();
      default:
        return _buildStepCompanySelect();
    }
  }

  // ── STEP 0: Company Profile Selection ──
  Widget _buildStepCompanySelect() {
    final profile = companyProfiles[_selectedCompanyId]!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildStepHeader(0, "회사 프로필 선택", "Step 1 of 3"),
        const SizedBox(height: 16),

        // Company Card
        Card(
          color: Colors.indigo.shade900,
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.business,
                      size: 32,
                      color: Colors.indigoAccent,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        profile['name']!,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _infoRow("법인 유형", profile['type']!),
                _infoRow("KBLI", profile['kbli']!),
                _infoRow("제품", profile['product']!),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),

        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton.icon(
            onPressed: _isGeneratingOrgChart ? null : _requestOrgChart,
            icon: _isGeneratingOrgChart
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.auto_awesome),
            label: Text(
              _isGeneratingOrgChart ? "AI가 조직도를 생성하는 중..." : "🤖 AI 조직도 생성",
            ),
          ),
        ),
      ],
    );
  }

  // ── STEP 1: Org Chart Toggle Selection ──
  Widget _buildStepOrgChart() {
    final enabledCount = _departments.where((d) => d['enabled'] == true).length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildStepHeader(1, "조직도 구성", "Step 2 of 3"),
        const SizedBox(height: 8),
        Text(
          "AI가 추천한 부서입니다. 토글로 선택/제외하세요.",
          style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
        ),
        const SizedBox(height: 16),

        ...List.generate(_departments.length, (index) {
          final dept = _departments[index];
          final emoji = dept['emoji'] ?? '📋';
          final name = dept['name'] ?? dept['id'];
          final nameEn = dept['name_en'] ?? '';
          final desc = dept['description'] ?? '';
          final priority = dept['priority'] ?? '';
          final enabled = dept['enabled'] ?? dept['default_enabled'] ?? true;

          // Set initial enabled state if not already set
          if (!dept.containsKey('enabled')) {
            dept['enabled'] = dept['default_enabled'] ?? true;
          }

          Color priorityColor;
          String priorityLabel;
          switch (priority) {
            case 'essential':
              priorityColor = Colors.redAccent;
              priorityLabel = '필수';
              break;
            case 'important':
              priorityColor = Colors.orangeAccent;
              priorityLabel = '중요';
              break;
            default:
              priorityColor = Colors.grey;
              priorityLabel = '선택';
          }

          return Card(
            color: enabled
                ? Colors.indigo.shade900.withValues(alpha: 0.7)
                : Colors.grey.shade900.withValues(alpha: 0.3),
            margin: const EdgeInsets.only(bottom: 8),
            child: SwitchListTile(
              value: enabled,
              onChanged: (val) {
                setState(() {
                  _departments[index]['enabled'] = val;
                });
              },
              secondary: Text(emoji, style: const TextStyle(fontSize: 28)),
              title: Row(
                children: [
                  Expanded(
                    child: Text(
                      name,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: enabled ? Colors.white : Colors.grey,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: priorityColor.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(
                        color: priorityColor.withValues(alpha: 0.5),
                      ),
                    ),
                    child: Text(
                      priorityLabel,
                      style: TextStyle(color: priorityColor, fontSize: 11),
                    ),
                  ),
                ],
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (nameEn.isNotEmpty)
                    Text(
                      nameEn,
                      style: TextStyle(
                        color: Colors.grey.shade500,
                        fontSize: 11,
                      ),
                    ),
                  const SizedBox(height: 4),
                  Text(
                    desc,
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                  ),
                ],
              ),
            ),
          );
        }),

        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton.icon(
            onPressed: enabledCount > 0
                ? () => setState(() => _setupStep = 2)
                : null,
            icon: const Icon(Icons.check_circle),
            label: Text("$enabledCount개 부서 확정 → 다음"),
          ),
        ),
      ],
    );
  }

  // ── STEP 2: Deploy ──
  Widget _buildStepDeploy() {
    final enabledDepts = _departments
        .where((d) => d['enabled'] == true)
        .toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildStepHeader(2, "업무 지시", "Step 3 of 3"),
        const SizedBox(height: 12),

        // Team summary
        Card(
          color: Colors.green.shade900.withValues(alpha: 0.3),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "✅ 구성된 조직",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: enabledDepts.map((d) {
                    return Chip(
                      avatar: Text(
                        d['emoji'] ?? '📋',
                        style: const TextStyle(fontSize: 14),
                      ),
                      label: Text(
                        d['name'] ?? d['id'],
                        style: const TextStyle(fontSize: 12),
                      ),
                      backgroundColor: Colors.indigo.shade800,
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        Text("CTO 지시사항", style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _taskController,
          maxLines: 4,
          decoration: const InputDecoration(
            hintText: "예: 앱스토어 등록을 위한 모든 문서를 준비해줘",
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),

        SizedBox(
          width: double.infinity,
          height: 52,
          child: FilledButton.icon(
            onPressed: _isWorkflowRunning ? null : _deployTeam,
            icon: const Icon(Icons.rocket_launch, size: 24),
            label: const Text("🚀 Deploy Team", style: TextStyle(fontSize: 16)),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.deepOrange.shade700,
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextButton.icon(
          onPressed: () => setState(() => _setupStep = 1),
          icon: const Icon(Icons.arrow_back, size: 16),
          label: const Text("← 조직 수정"),
        ),
      ],
    );
  }

  // ═══════════════════════════════════════════════
  // HELPER WIDGETS
  // ═══════════════════════════════════════════════

  Widget _buildStepHeader(int step, String title, String subtitle) {
    return Row(
      children: [
        CircleAvatar(
          radius: 18,
          backgroundColor: Colors.indigoAccent,
          child: Text(
            "${step + 1}",
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            Text(
              subtitle,
              style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
            ),
          ],
        ),
      ],
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              "$label:",
              style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }

  void _showApprovalDialog(String command, String reason) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.grey.shade900,
        title: const Row(
          children: [
            Icon(
              Icons.warning_amber_rounded,
              color: Colors.orangeAccent,
              size: 28,
            ),
            SizedBox(width: 8),
            Text(
              "⚠️ CTO 승인 필요",
              style: TextStyle(
                color: Colors.orangeAccent,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "위험한 명령어가 감지되었습니다:",
              style: TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.maxFinite,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade900.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade700),
              ),
              child: Text(
                "\$ $command",
                style: const TextStyle(
                  fontFamily: 'Courier',
                  color: Colors.redAccent,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              "이 명령어를 실행하시겠습니까?",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(
                jsonEncode({
                  "type": "approval_response",
                  "approved": false,
                  "command": command,
                }),
              );
              setState(() {
                _logs.add("[CTO] ❌ 거절: $command");
                _workflowStatus = "rejected";
              });
            },
            child: const Text(
              "❌ 거절",
              style: TextStyle(color: Colors.red, fontSize: 16),
            ),
          ),
          const SizedBox(width: 8),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.orange.shade800,
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              _channel?.sink.add(
                jsonEncode({
                  "type": "approval_response",
                  "approved": true,
                  "command": command,
                }),
              );
              setState(() {
                _logs.add("[CTO] ✅ 승인: $command");
                _workflowStatus = "approved";
              });
            },
            child: const Text("✅ 승인", style: TextStyle(fontSize: 16)),
          ),
        ],
      ),
    );
  }
}
