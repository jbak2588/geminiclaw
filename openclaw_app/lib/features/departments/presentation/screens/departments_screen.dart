import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';

class DepartmentsScreen extends StatefulWidget {
  const DepartmentsScreen({super.key});

  @override
  State<DepartmentsScreen> createState() => _DepartmentsScreenState();
}

class _DepartmentsScreenState extends State<DepartmentsScreen> {
  List<dynamic> _teams = [];
  bool _loading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final response = await ApiClient.instance.getJson('/api/teams');
      _teams = response['teams'] as List<dynamic>? ?? [];
    } catch (e) {
      _error = '$e';
      _teams = [];
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Department Teams', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        if (_loading)
          const Center(child: CircularProgressIndicator())
        else if (_error.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(_error),
            ),
          )
        else
          ..._teams.map(
            (team) => Card(
              child: ExpansionTile(
                title: Text(team['name']?.toString() ?? 'Team'),
                subtitle: Text(team['description']?.toString() ?? ''),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text((team['config'] as List<dynamic>? ?? []).join('\n')),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
