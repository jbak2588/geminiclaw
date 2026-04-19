import 'package:flutter/material.dart';

import '../../../../core/realtime/realtime_hub.dart';

class WorkflowLiveScreen extends StatelessWidget {
  const WorkflowLiveScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final hub = RealtimeHub.instance;

    return AnimatedBuilder(
      animation: hub,
      builder: (context, _) {
        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text('Workflow Live', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 12),
            Text(
              hub.latestTaskTitle.isEmpty
                  ? 'No active workflow yet.'
                  : 'Task: ${hub.latestTaskTitle}',
            ),
            const SizedBox(height: 20),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: hub.workflowNodes.map((node) {
                final status = node['status']?.toString() ?? 'pending';
                final active = hub.activeNode == node['id']?.toString();
                return SizedBox(
                  width: 220,
                  child: Card(
                    color: _statusColor(status).withValues(alpha: active ? 0.35 : 0.18),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            node['label']?.toString() ?? 'Node',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('Role: ${node['role']}'),
                          const SizedBox(height: 4),
                          Text('Status: $status'),
                          if (active) ...[
                            const SizedBox(height: 8),
                            const Text('ACTIVE NOW', style: TextStyle(color: Colors.amberAccent)),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),
            Text('Edges', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            if (hub.workflowEdges.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Workflow graph has not been streamed yet.'),
                ),
              )
            else
              ...hub.workflowEdges.map(
                (edge) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.trending_flat),
                    title: Text('${edge['from']} -> ${edge['to']}'),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'running':
        return Colors.blue;
      case 'pending':
        return Colors.orange;
      case 'error':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
