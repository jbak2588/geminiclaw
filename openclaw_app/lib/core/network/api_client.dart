import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_constants.dart';

class ApiClient {
  ApiClient._();

  static final ApiClient instance = ApiClient._();

  Uri _uri(String path) => Uri.parse('${AppConstants.apiBaseUrl}$path');

  Future<Map<String, dynamic>> getJson(String path) async {
    try {
      final response = await http.get(_uri(path)).timeout(const Duration(seconds: 5));
      _ensureSuccess(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      throw Exception(_formatError(path, e));
    }
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    try {
      final response = await http
          .post(
            _uri(path),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 5));
      _ensureSuccess(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      throw Exception(_formatError(path, e));
    }
  }

  Future<Map<String, dynamic>> postEmpty(String path) async {
    try {
      final response = await http.post(_uri(path)).timeout(const Duration(seconds: 5));
      _ensureSuccess(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      throw Exception(_formatError(path, e));
    }
  }

  Future<Map<String, dynamic>> multipartUpload(
    String path, {
    required List<int> bytes,
    required String filename,
    String fieldName = 'file',
  }) async {
    try {
      final request = http.MultipartRequest('POST', _uri(path));
      request.files.add(http.MultipartFile.fromBytes(fieldName, bytes, filename: filename));
      final streamed = await request.send().timeout(const Duration(seconds: 10));
      final response = await http.Response.fromStream(streamed);
      _ensureSuccess(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      throw Exception(_formatError(path, e));
    }
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('API ${response.statusCode}: ${response.body}');
    }
  }

  String _formatError(String path, Object error) {
    return 'Request failed for $path. Ensure the backend is running at ${AppConstants.apiBaseUrl}. Details: $error';
  }
}
