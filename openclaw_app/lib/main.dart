import 'package:flutter/material.dart';
import 'app/app_shell.dart';
import 'core/realtime/realtime_hub.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  RealtimeHub.instance.ensureConnected();
  runApp(const GeminiClawCompanyOsApp());
}

class GeminiClawCompanyOsApp extends StatelessWidget {
  const GeminiClawCompanyOsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GeminiClaw - Company OS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const AppShell(),
    );
  }
}
