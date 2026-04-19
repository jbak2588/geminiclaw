import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../../../core/network/api_client.dart';

class KnowledgeScreen extends StatefulWidget {
  const KnowledgeScreen({super.key});

  @override
  State<KnowledgeScreen> createState() => _KnowledgeScreenState();
}

class _KnowledgeScreenState extends State<KnowledgeScreen> {
  List<dynamic> _documents = [];
  List<dynamic> _projects = [];
  String? _selectedProjectId;
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
      final docs = await ApiClient.instance.getJson('/api/projects/knowledge');
      final projects = await ApiClient.instance.getJson('/api/projects');
      _documents = docs['documents'] as List<dynamic>? ?? [];
      _projects = projects['projects'] as List<dynamic>? ?? [];
      if (_projects.isNotEmpty && _selectedProjectId == null) {
        _selectedProjectId = _projects.first['id'].toString();
      }
    } catch (e) {
      _error = '$e';
      _documents = [];
      _projects = [];
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _upload() async {
    if (_selectedProjectId == null) return;
    try {
      final result = await FilePicker.platform.pickFiles(withData: true);
      if (result == null) return;
      final file = result.files.first;
      if (file.bytes == null) return;

      await ApiClient.instance.multipartUpload(
        '/api/projects/${_selectedProjectId!}/knowledge',
        bytes: file.bytes!,
        filename: file.name,
      );
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
        Text('Knowledge Library', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                initialValue: _selectedProjectId,
                decoration: const InputDecoration(
                  labelText: 'Target Project',
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
            FilledButton.icon(
              onPressed: _upload,
              icon: const Icon(Icons.upload_file),
              label: const Text('Upload'),
            ),
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
          )
        else if (_documents.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('No knowledge documents uploaded yet.'),
            ),
          )
        else
          ..._documents.map(
            (doc) => Card(
              child: ListTile(
                leading: const Icon(Icons.description_outlined),
                title: Text(doc['title']?.toString() ?? 'Untitled'),
                subtitle: Text(doc['summary']?.toString() ?? ''),
                trailing: Text(doc['project_id']?.toString() ?? ''),
              ),
            ),
          ),
      ],
    );
  }
}
