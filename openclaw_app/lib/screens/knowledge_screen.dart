import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

class KnowledgeLibraryView extends StatefulWidget {
  const KnowledgeLibraryView({super.key});

  @override
  State<KnowledgeLibraryView> createState() => _KnowledgeLibraryViewState();
}

class _KnowledgeLibraryViewState extends State<KnowledgeLibraryView> {
  List<dynamic> _documents = [];
  List<dynamic> _projects = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchRESTData();
  }

  Future<void> _fetchRESTData() async {
    setState(() => _isLoading = true);
    try {
      final docsRes = await http.get(Uri.parse('http://localhost:8001/api/projects/knowledge'));
      final projRes = await http.get(Uri.parse('http://localhost:8001/api/projects'));

      if (docsRes.statusCode == 200) {
        setState(() {
          _documents = jsonDecode(docsRes.body)['documents'] ?? [];
        });
      }
      if (projRes.statusCode == 200) {
        setState(() {
          _projects = jsonDecode(projRes.body)['projects'] ?? [];
        });
      }
    } catch (e) {
      debugPrint("Error fetching knowledge data: \$e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _showUploadDialog() async {
    String? selectedProjectId = _projects.isNotEmpty ? _projects.first['id'] as String : null;
    PlatformFile? selectedFile;

    await showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Upload PDF Knowledge'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Select Target Project:'),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: selectedProjectId,
                    isExpanded: true,
                    items: _projects.map((p) => DropdownMenuItem<String>(
                      value: p['id'] as String,
                      child: Text(p['name'] as String),
                    )).toList(),
                    onChanged: (val) {
                      setDialogState(() {
                        selectedProjectId = val;
                      });
                    },
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () async {
                      FilePickerResult? result = await FilePicker.platform.pickFiles(
                        type: FileType.custom,
                        allowedExtensions: ['pdf'],
                        withData: true, // Needed for web
                      );
                      if (result != null) {
                        setDialogState(() {
                          selectedFile = result.files.first;
                        });
                      }
                    },
                    icon: const Icon(Icons.attach_file),
                    label: const Text('Select PDF File'),
                  ),
                  if (selectedFile != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text('Selected: \${selectedFile!.name}', style: const TextStyle(color: Colors.green)),
                    ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: (selectedProjectId != null && selectedFile != null)
                      ? () async {
                          Navigator.pop(context);
                          await _uploadFile(selectedProjectId!, selectedFile!);
                        }
                      : null,
                  child: const Text('Upload'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _uploadFile(String projectId, PlatformFile file) async {
    setState(() => _isLoading = true);
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://localhost:8001/api/projects/\$projectId/knowledge'),
      );
      
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        file.bytes!,
        filename: file.name,
      ));

      var response = await request.send();
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Upload successful! Processing complete.')),
        );
        _fetchRESTData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Upload failed: \${response.statusCode}')),
        );
        setState(() => _isLoading = false);
      }
    } catch (e) {
      debugPrint("Upload Error: \$e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error uploading file: \$e')),
      );
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Global Knowledge Library'),
        backgroundColor: Colors.indigo.shade800,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchRESTData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _documents.isEmpty
              ? const Center(child: Text('No knowledge documents found.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _documents.length,
                  itemBuilder: (context, index) {
                    final doc = _documents[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      elevation: 2,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    doc['title'] ?? 'Untitled',
                                    style: const TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.indigo.shade900,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    "Project: ${doc['project_id']}",
                                    style: const TextStyle(fontSize: 12),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              doc['summary'] ?? 'No summary available.',
                              style: TextStyle(color: Colors.grey.shade400),
                            ),
                            const SizedBox(height: 12),
                            const Text('Contents:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            const SizedBox(height: 4),
                            Text(
                              doc['toc'] ?? '',
                              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                              maxLines: 5,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 8),
                            Align(
                              alignment: Alignment.bottomRight,
                              child: Text(
                                "Uploaded at: ${doc['uploaded_at']}",
                                style: const TextStyle(fontSize: 11, color: Colors.grey),
                              ),
                            )
                          ],
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showUploadDialog,
        icon: const Icon(Icons.upload_file),
        label: const Text('Upload PDF'),
      ),
    );
  }
}
