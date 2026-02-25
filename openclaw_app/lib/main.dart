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
      debugShowCheckedModeBanner: false,
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

// ──────────────────────────────────────────────
// Kanban Task Model
// ──────────────────────────────────────────────
class KanbanTask {
  final String id;
  final String agent;
  final String task;
  final String status; // todo | in_progress | review | done
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

// ──────────────────────────────────────────────
// Dashboard Screen
// ──────────────────────────────────────────────
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
  String _currentAgentNode = 'Idle';
  String _workflowStatus = '조직 구성 대기 중...';

  // ── Setup Wizard State ──
  int _setupStep = 0; // 0=company, 1=org chart, 2=ready
  final String _selectedCompanyId = 'pt_humantric';
  List<Map<String, dynamic>> _departments = [];
  bool _isGeneratingOrgChart = false;

  // ── Kanban State ──
  List<KanbanTask> _kanbanTasks = [];

  void _connectWebSocket() {
    final clientId = DateTime.now().millisecondsSinceEpoch.toString();
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$clientId'),
    );
    _channel!.stream.listen(_onMessage, onError: _onError, onDone: _onDone);
  }

  void _onMessage(dynamic message) {
    final data = jsonDecode(message as String) as Map<String, dynamic>;
    setState(() {
      final type = data['type'] as String? ?? '';

      if (type == 'org_chart_response') {
        _isGeneratingOrgChart = false;
        final orgData = data['data'] as Map<String, dynamic>?;
        if (orgData != null && orgData.containsKey('departments')) {
          _departments = (orgData['departments'] as List)
              .map((d) => Map<String, dynamic>.from(d as Map))
              .toList();
          _setupStep = 1;
        }
      } else if (type == 'info') {
        _logs.add('[INFO] ${data['message']}');
        if (data['message']?.toString().contains('Completed') == true) {
          _isWorkflowRunning = false;
          // 워크플로우 완료 시 모든 in_progress/review 태스크를 done으로
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
        _showApprovalDialog(
          data['command'] as String? ?? '',
          data['message']?.toString() ?? '',
        );
      } else if (type == 'agent_event') {
        _currentAgentNode = data['node'] as String? ?? 'Unknown';
        _workflowStatus = data['status'] as String? ?? 'Processing';
        _logs.add('[${data['node']}] → ${data['status']}\n${data['message']}');
      } else if (type == 'kanban_update') {
        // ── 칸반 보드 업데이트 ──
        final taskList = data['tasks'] as List?;
        if (taskList != null) {
          _kanbanTasks = taskList
              .map(
                (t) => KanbanTask.fromJson(Map<String, dynamic>.from(t as Map)),
              )
              .toList();
        }
      }
    });
  }

  void _onError(dynamic error) {
    setState(() {
      _logs.add('[ERROR] $error');
      _isWorkflowRunning = false;
      _isGeneratingOrgChart = false;
    });
  }

  void _onDone() {
    setState(() {
      _logs.add('[SYSTEM] WebSocket closed.');
      _isWorkflowRunning = false;
    });
  }

  void _requestOrgChart() {
    setState(() {
      _isGeneratingOrgChart = true;
    });
    _connectWebSocket();

    const docDir = r'E:\geminiclaw\doc';
    _channel!.sink.add(
      jsonEncode({
        'type': 'org_chart_request',
        'profile_id': _selectedCompanyId,
        'whitepaper_dir': docDir,
      }),
    );
  }

  void _deployTeam() {
    if (_taskController.text.isEmpty) return;

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
      _kanbanTasks = [];
      _isWorkflowRunning = true;
      _workflowStatus = 'Starting workflow...';
      _currentAgentNode = 'PM';
    });

    _connectWebSocket();
    _channel!.sink.add(
      jsonEncode({'task': _taskController.text, 'team': teamConfig}),
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
                _kanbanTasks = [];
              }),
              icon: const Icon(Icons.restart_alt, size: 18),
              label: const Text('Reset'),
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
          // CENTER PANEL: Kanban Board
          // ═══════════════════════════════════════════
          Expanded(
            flex: 5,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.grey.shade900,
                border: Border(right: BorderSide(color: Colors.grey.shade800)),
              ),
              child: _buildKanbanPanel(),
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
                      Expanded(
                        child: Text(
                          'Active: $_currentAgentNode  |  Status: $_workflowStatus',
                          style: TextStyle(
                            color: Colors.grey.shade400,
                            fontSize: 11,
                            fontFamily: 'Courier',
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
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
                              fontSize: 11,
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
  // KANBAN PANEL
  // ═══════════════════════════════════════════════
  Widget _buildKanbanPanel() {
    const columns = [
      {'key': 'todo', 'label': 'TODO', 'icon': '📋'},
      {'key': 'in_progress', 'label': 'IN PROGRESS', 'icon': '⚡'},
      {'key': 'review', 'label': 'REVIEW', 'icon': '🔍'},
      {'key': 'done', 'label': 'DONE', 'icon': '✅'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 칸반 헤더
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.indigo.shade900.withValues(alpha: 0.5),
            border: Border(bottom: BorderSide(color: Colors.grey.shade800)),
          ),
          child: Row(
            children: [
              const Icon(
                Icons.view_kanban,
                size: 18,
                color: Colors.indigoAccent,
              ),
              const SizedBox(width: 8),
              const Text(
                'Kanban Board',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 12),
              if (_kanbanTasks.isNotEmpty)
                Text(
                  '${_kanbanTasks.where((t) => t.status == 'done').length}/${_kanbanTasks.length} 완료',
                  style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                ),
            ],
          ),
        ),

        // 칸반 컬럼
        Expanded(
          child: _kanbanTasks.isEmpty
              ? _buildEmptyKanban()
              : Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: columns.map((col) {
                    final key = col['key']!;
                    final tasks = _kanbanTasks
                        .where((t) => t.status == key)
                        .toList();
                    return Expanded(
                      child: _buildKanbanColumn(
                        label: col['label']!,
                        icon: col['icon']!,
                        statusKey: key,
                        tasks: tasks,
                      ),
                    );
                  }).toList(),
                ),
        ),
      ],
    );
  }

  Widget _buildEmptyKanban() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.view_kanban_outlined,
            size: 64,
            color: Colors.grey.shade700,
          ),
          const SizedBox(height: 16),
          Text(
            '팀을 Deploy하면 칸반 보드가 시작됩니다',
            style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Text(
            'TODO → IN PROGRESS → REVIEW → DONE',
            style: TextStyle(color: Colors.grey.shade700, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildKanbanColumn({
    required String label,
    required String icon,
    required String statusKey,
    required List<KanbanTask> tasks,
  }) {
    // 컬럼별 색상 설정
    final (headerColor, accentColor, cardBorder) = switch (statusKey) {
      'todo' => (
        Colors.grey.shade800,
        Colors.grey.shade400,
        Colors.grey.shade600,
      ),
      'in_progress' => (
        Colors.blue.shade900,
        Colors.blue.shade300,
        Colors.blue.shade500,
      ),
      'review' => (
        Colors.orange.shade900,
        Colors.orange.shade300,
        Colors.orange.shade500,
      ),
      'done' => (
        Colors.green.shade900,
        Colors.green.shade300,
        Colors.green.shade600,
      ),
      _ => (Colors.grey.shade800, Colors.grey.shade400, Colors.grey.shade600),
    };

    return Container(
      decoration: BoxDecoration(
        border: Border(right: BorderSide(color: Colors.grey.shade800)),
      ),
      child: Column(
        children: [
          // 컬럼 헤더
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: headerColor.withValues(alpha: 0.6),
              border: Border(
                bottom: BorderSide(color: cardBorder.withValues(alpha: 0.4)),
              ),
            ),
            child: Row(
              children: [
                Text(icon, style: const TextStyle(fontSize: 14)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    label,
                    style: TextStyle(
                      color: accentColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: accentColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: accentColor.withValues(alpha: 0.4),
                    ),
                  ),
                  child: Text(
                    '${tasks.length}',
                    style: TextStyle(
                      color: accentColor,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // 카드 리스트
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(8),
              children: tasks
                  .map(
                    (task) => _buildKanbanCard(
                      task: task,
                      accentColor: accentColor,
                      cardBorder: cardBorder,
                      isActive: statusKey == 'in_progress',
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKanbanCard({
    required KanbanTask task,
    required Color accentColor,
    required Color cardBorder,
    required bool isActive,
  }) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 400),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isActive
            ? Colors.blue.shade900.withValues(alpha: 0.3)
            : Colors.grey.shade900.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isActive
              ? cardBorder.withValues(alpha: 0.7)
              : Colors.grey.shade700.withValues(alpha: 0.4),
          width: isActive ? 1.5 : 1.0,
        ),
        boxShadow: isActive
            ? [
                BoxShadow(
                  color: cardBorder.withValues(alpha: 0.2),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
              ]
            : null,
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 에이전트 이름 + 이모지
            Row(
              children: [
                Text(task.emoji, style: const TextStyle(fontSize: 16)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    task.agent.toUpperCase(),
                    style: TextStyle(
                      color: accentColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                if (isActive)
                  const SizedBox(
                    width: 10,
                    height: 10,
                    child: CircularProgressIndicator(strokeWidth: 1.5),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            // 태스크 설명
            Text(
              task.task,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: Colors.grey.shade300,
                fontSize: 11,
                height: 1.4,
              ),
            ),
          ],
        ),
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
        _buildStepHeader(0, '회사 프로필 선택', 'Step 1 of 3'),
        const SizedBox(height: 16),

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
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _infoRow('법인 유형', profile['type']!),
                _infoRow('KBLI', profile['kbli']!),
                _infoRow('제품', profile['product']!),
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
              _isGeneratingOrgChart ? 'AI가 조직도를 생성하는 중...' : '🤖 AI 조직도 생성',
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
        _buildStepHeader(1, '조직도 구성', 'Step 2 of 3'),
        const SizedBox(height: 8),
        Text(
          'AI가 추천한 부서입니다. 토글로 선택/제외하세요.',
          style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
        ),
        const SizedBox(height: 16),

        ...List.generate(_departments.length, (index) {
          final dept = _departments[index];
          final emoji = dept['emoji'] as String? ?? '📋';
          final name = dept['name'] as String? ?? dept['id'] as String? ?? '';
          final nameEn = dept['name_en'] as String? ?? '';
          final desc = dept['description'] as String? ?? '';
          final priority = dept['priority'] as String? ?? '';
          final enabled = dept.containsKey('enabled')
              ? dept['enabled'] as bool
              : (dept['default_enabled'] as bool? ?? true);

          if (!dept.containsKey('enabled')) {
            dept['enabled'] = dept['default_enabled'] ?? true;
          }

          Color priorityColor;
          String priorityLabel;
          switch (priority) {
            case 'essential':
              priorityColor = Colors.redAccent;
              priorityLabel = '필수';
            case 'important':
              priorityColor = Colors.orangeAccent;
              priorityLabel = '중요';
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
              onChanged: (val) =>
                  setState(() => _departments[index]['enabled'] = val),
              secondary: Text(emoji, style: const TextStyle(fontSize: 26)),
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
                      style: TextStyle(color: priorityColor, fontSize: 10),
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
                        fontSize: 10,
                      ),
                    ),
                  const SizedBox(height: 2),
                  Text(
                    desc,
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 11),
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
            label: Text('$enabledCount개 부서 확정 → 다음'),
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
        _buildStepHeader(2, '업무 지시', 'Step 3 of 3'),
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
                  '✅ 구성된 조직',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: enabledDepts.map((d) {
                    return Chip(
                      avatar: Text(
                        d['emoji'] as String? ?? '📋',
                        style: const TextStyle(fontSize: 12),
                      ),
                      label: Text(
                        d['name'] as String? ?? d['id'] as String? ?? '',
                        style: const TextStyle(fontSize: 11),
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

        // 칸반 진행 상황 미리보기 (워크플로우 중일 때)
        if (_kanbanTasks.isNotEmpty) ...[
          _buildInlineKanbanSummary(),
          const SizedBox(height: 16),
        ],

        Text('CTO 지시사항', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _taskController,
          maxLines: 4,
          decoration: const InputDecoration(
            hintText: '예: 앱스토어 등록을 위한 모든 문서를 준비해줘',
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
            label: const Text('🚀 Deploy Team', style: TextStyle(fontSize: 15)),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.deepOrange.shade700,
            ),
          ),
        ),
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: () => setState(() => _setupStep = 1),
          icon: const Icon(Icons.arrow_back, size: 16),
          label: const Text('← 조직 수정'),
        ),
      ],
    );
  }

  // 좌측 패널 칸반 미니 요약
  Widget _buildInlineKanbanSummary() {
    final todo = _kanbanTasks.where((t) => t.status == 'todo').length;
    final inProgress = _kanbanTasks
        .where((t) => t.status == 'in_progress')
        .length;
    final review = _kanbanTasks.where((t) => t.status == 'review').length;
    final done = _kanbanTasks.where((t) => t.status == 'done').length;

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.indigo.shade900.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Colors.indigo.shade700.withValues(alpha: 0.4),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _miniStat('📋', todo, Colors.grey.shade400),
          _miniStat('⚡', inProgress, Colors.blue.shade300),
          _miniStat('🔍', review, Colors.orange.shade300),
          _miniStat('✅', done, Colors.green.shade400),
        ],
      ),
    );
  }

  Widget _miniStat(String icon, int count, Color color) {
    return Column(
      children: [
        Text(icon, style: const TextStyle(fontSize: 16)),
        Text(
          '$count',
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
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
            '${step + 1}',
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
            width: 72,
            child: Text(
              '$label:',
              style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 12))),
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
              '⚠️ CTO 승인 필요',
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
              '위험한 명령어가 감지되었습니다:',
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
                '\$ $command',
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
              '이 명령어를 실행하시겠습니까?',
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
                  'type': 'approval_response',
                  'approved': false,
                  'command': command,
                }),
              );
              setState(() {
                _logs.add('[CTO] ❌ 거절: $command');
                _workflowStatus = 'rejected';
              });
            },
            child: const Text(
              '❌ 거절',
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
                  'type': 'approval_response',
                  'approved': true,
                  'command': command,
                }),
              );
              setState(() {
                _logs.add('[CTO] ✅ 승인: $command');
                _workflowStatus = 'approved';
              });
            },
            child: const Text('✅ 승인', style: TextStyle(fontSize: 16)),
          ),
        ],
      ),
    );
  }
}
