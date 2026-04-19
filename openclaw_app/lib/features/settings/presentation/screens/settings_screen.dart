import 'package:flutter/material.dart';

import '../../../../core/config/app_constants.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Settings', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        const Card(
          child: ListTile(
            leading: Icon(Icons.key_outlined),
            title: Text('AI Provider'),
            subtitle: Text('Connect one provider key such as GPT or Gemini on the backend side.'),
          ),
        ),
        Card(
          child: ListTile(
            leading: const Icon(Icons.http),
            title: const Text('API Base URL'),
            subtitle: Text(AppConstants.apiBaseUrl),
          ),
        ),
        Card(
          child: ListTile(
            leading: const Icon(Icons.cable_outlined),
            title: const Text('WebSocket URL'),
            subtitle: Text(AppConstants.wsBaseUrl),
          ),
        ),
      ],
    );
  }
}
