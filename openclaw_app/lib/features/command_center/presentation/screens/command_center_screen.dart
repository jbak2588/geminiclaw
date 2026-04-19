import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';

class CommandCenterScreen extends StatefulWidget {
  const CommandCenterScreen({super.key});

  @override
  State<CommandCenterScreen> createState() => _CommandCenterScreenState();
}

class _CommandCenterScreenState extends State<CommandCenterScreen> {
  final TextEditingController _taskController = TextEditingController();
  String? _selectedProjectId;
  String? _selectedTeamId;
  List<dynamic> _projects = [];
  List<dynamic> _teams = [];
  bool _submitting = false;
  String _lastResponse = '';

  @override
  void initState() {
    super.initState();
    _loadSeedData();
  }

  Future<void> _loadSeedData() async {
    try {
      final projects = await ApiClient.instance.getJson('/api/projects');
      final teams = await ApiClient.instance.getJson('/api/teams');
      setState(() {
        _projects = projects['projects'] as List<dynamic>? ?? [];
        _teams = teams['teams'] as List<dynamic>? ?? [];
        if (_projects.isNotEmpty) {
          _selectedProjectId = _projects.first['id'].toString();
        }
        if (_teams.isNotEmpty) {
          _selectedTeamId = _teams.first['id'].toString();
        }
      });
    } catch (_) {}
  }

  Future<void> _createTask() async {
    if (_taskController.text.trim().isEmpty) return;
    setState(() {
      _submitting = true;
      _lastResponse = '';
    });

    try {
      final response = await ApiClient.instance.postJson('/api/tasks', {
        'title': _taskController.text.trim(),
        'instruction': _taskController.text.trim(),
        'project_id': _selectedProjectId,
        'team_id': _selectedTeamId,
        'source': 'dashboard',
      });
      setState(() {
        _lastResponse = 'Task created: ${response['task_id']}';
      });
      _taskController.clear();
    } catch (e) {
      setState(() => _lastResponse = '$e');
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  Future<void> _createProject() async {
    final controller = TextEditingController();
    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Create Project'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(labelText: 'Project name'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              await ApiClient.instance.postJson('/api/projects', {
                'name': controller.text.trim().isEmpty ? 'Untitled Project' : controller.text.trim(),
                'description': 'Created from Company OS dashboard',
              });
              if (!mounted) return;
              Navigator.pop(context);
              _loadSeedData();
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Command Center', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        const Text(
          'Send a natural-language instruction. The backend will create a task, dispatch a workflow, stream node updates, and raise approval requests if needed.',
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                initialValue: _selectedProjectId,
                decoration: const InputDecoration(
                  labelText: 'Project',
                  border: OutlineInputBorder(),
                ),
                items: _projects
                    .map(
                      (item) => DropdownMenuItem<String>(
                        value: item['id'].toString(),
                        child: Text(item['name'].toString()),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _selectedProjectId = value),
              ),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: _createProject,
              icon: const Icon(Icons.add),
              label: const Text('New Project'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _selectedTeamId,
          decoration: const InputDecoration(
            labelText: 'Department Team Preset',
            border: OutlineInputBorder(),
          ),
          items: _teams
              .map(
                (item) => DropdownMenuItem<String>(
                  value: item['id'].toString(),
                  child: Text(item['name'].toString()),
                ),
              )
              .toList(),
          onChanged: (value) => setState(() => _selectedTeamId = value),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _taskController,
          maxLines: 8,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Example: Create a beta launch checklist, assign planning and ops, prepare report, and request final approval before external distribution.',
          ),
        ),
        const SizedBox(height: 12),
        Align(
          alignment: Alignment.centerRight,
          child: FilledButton.icon(
            onPressed: _submitting ? null : _createTask,
            icon: const Icon(Icons.send),
            label: Text(_submitting ? 'Submitting...' : 'Dispatch Task'),
          ),
        ),
        if (_lastResponse.isNotEmpty) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(_lastResponse),
            ),
          ),
        ],
      ],
    );
  }
}
