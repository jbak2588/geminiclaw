import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';

class ChannelsScreen extends StatefulWidget {
  const ChannelsScreen({super.key});

  @override
  State<ChannelsScreen> createState() => _ChannelsScreenState();
}

class _ChannelsScreenState extends State<ChannelsScreen> {
  final TextEditingController _messageController = TextEditingController();
  String _channel = 'telegram';
  List<dynamic> _messages = [];
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
      final response = await ApiClient.instance.getJson('/api/channels/messages');
      _messages = response['messages'] as List<dynamic>? ?? [];
    } catch (e) {
      _error = '$e';
      _messages = [];
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _sendMock() async {
    if (_messageController.text.trim().isEmpty) return;
    try {
      await ApiClient.instance.postJson('/api/channels/messages', {
        'channel': _channel,
        'sender': 'field_user',
        'message': _messageController.text.trim(),
        'create_task': true,
      });
      _messageController.clear();
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
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Channel Hub', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        Row(
          children: [
            DropdownButton<String>(
              value: _channel,
              items: const [
                DropdownMenuItem(value: 'telegram', child: Text('Telegram')),
                DropdownMenuItem(value: 'whatsapp', child: Text('WhatsApp')),
                DropdownMenuItem(value: 'slack', child: Text('Slack')),
              ],
              onChanged: (value) => setState(() => _channel = value ?? 'telegram'),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: const InputDecoration(
                  hintText: 'Simulate an incoming field message...',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 12),
            FilledButton(onPressed: _sendMock, child: const Text('Send')),
          ],
        ),
        const SizedBox(height: 20),
        if (_loading)
          const Center(child: CircularProgressIndicator())
        else if (_error.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(_error),
            ),
          ),
        ..._messages.map(
          (item) => Card(
            child: ListTile(
              leading: const Icon(Icons.forum_outlined),
              title: Text(item['channel']?.toString() ?? ''),
              subtitle: Text(item['message']?.toString() ?? ''),
              trailing: Text(item['sender']?.toString() ?? ''),
            ),
          ),
        ),
      ],
    );
  }
}
