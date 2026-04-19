import 'package:flutter/material.dart';

import '../../../../core/models/simple_models.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/realtime/realtime_hub.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  DashboardOverview? _overview;
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
      final json = await ApiClient.instance.getJson('/api/dashboard/overview');
      _overview = DashboardOverview.fromJson(json);
    } catch (e) {
      _error = '$e';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final hub = RealtimeHub.instance;

    return AnimatedBuilder(
      animation: hub,
      builder: (context, _) {
        return RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text('Dashboard', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 16),
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
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _metricCard('Projects', '${_overview?.projectsCount ?? 0}', Icons.folder_copy_outlined),
                    _metricCard('Tasks', '${_overview?.tasksCount ?? 0}', Icons.checklist_outlined),
                    _metricCard('Pending Approvals', '${_overview?.pendingApprovals ?? 0}', Icons.approval_outlined),
                    _metricCard('Knowledge Docs', '${_overview?.knowledgeCount ?? 0}', Icons.library_books_outlined),
                    _metricCard('Channel Messages', '${_overview?.channelMessages ?? 0}', Icons.forum_outlined),
                  ],
                ),
              const SizedBox(height: 24),
              Text('Recent Events', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              if (hub.recentEvents.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No live events yet. Create a task from Command Center.'),
                  ),
                )
              else
                ...hub.recentEvents.take(12).map(
                  (event) => Card(
                    child: ListTile(
                      leading: const Icon(Icons.bolt_outlined),
                      title: Text(event['type']?.toString() ?? 'event'),
                      subtitle: Text(
                        [
                          event['task_title']?.toString(),
                          event['message']?.toString(),
                        ].where((e) => e != null && e.isNotEmpty).join(' | '),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _metricCard(String title, String value, IconData icon) {
    return SizedBox(
      width: 230,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(child: Icon(icon)),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
