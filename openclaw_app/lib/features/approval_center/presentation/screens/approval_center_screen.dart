import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/realtime/realtime_hub.dart';

class ApprovalCenterScreen extends StatefulWidget {
  const ApprovalCenterScreen({super.key});

  @override
  State<ApprovalCenterScreen> createState() => _ApprovalCenterScreenState();
}

class _ApprovalCenterScreenState extends State<ApprovalCenterScreen> {
  List<dynamic> _approvals = [];
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
      final response = await ApiClient.instance.getJson('/api/approvals');
      _approvals = response['approvals'] as List<dynamic>? ?? [];
    } catch (e) {
      _error = '$e';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _decide(String approvalId, String decision) async {
    try {
      await ApiClient.instance.postJson('/api/approvals/$approvalId/decision', {
        'decision': decision,
        'actor': 'dashboard_owner',
        'comment': '',
      });
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final hub = RealtimeHub.instance;

    return AnimatedBuilder(
      animation: hub,
      builder: (context, _) {
        final merged = [...hub.pendingApprovals, ..._approvals];
        final seen = <String>{};
        final unique = merged.where((item) => seen.add(item['approval_id'].toString())).toList();

        return RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text('Approval Center', style: Theme.of(context).textTheme.headlineSmall),
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
              else if (unique.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No approvals waiting.'),
                  ),
                )
              else
                ...unique.map(
                  (item) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item['title']?.toString() ?? 'Approval',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('Task: ${item['task_title'] ?? '-'}'),
                          Text('Node: ${item['node'] ?? '-'}'),
                          Text('Status: ${item['status'] ?? 'pending'}'),
                          const SizedBox(height: 8),
                          Text(item['message']?.toString() ?? ''),
                          const SizedBox(height: 12),
                          if ((item['status']?.toString() ?? 'pending') == 'pending')
                            Row(
                              children: [
                                OutlinedButton.icon(
                                  onPressed: () => _decide(item['approval_id'].toString(), 'rejected'),
                                  icon: const Icon(Icons.close),
                                  label: const Text('Reject'),
                                ),
                                const SizedBox(width: 12),
                                FilledButton.icon(
                                  onPressed: () => _decide(item['approval_id'].toString(), 'approved'),
                                  icon: const Icon(Icons.check),
                                  label: const Text('Approve'),
                                ),
                              ],
                            ),
                        ],
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
}
