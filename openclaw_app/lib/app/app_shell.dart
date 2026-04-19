import 'package:flutter/material.dart';

import '../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../features/command_center/presentation/screens/command_center_screen.dart';
import '../features/workflow_live/presentation/screens/workflow_live_screen.dart';
import '../features/approval_center/presentation/screens/approval_center_screen.dart';
import '../features/logs/presentation/screens/logs_screen.dart';
import '../features/knowledge/presentation/screens/knowledge_screen.dart';
import '../features/channels/presentation/screens/channels_screen.dart';
import '../features/departments/presentation/screens/departments_screen.dart';
import '../features/settings/presentation/screens/settings_screen.dart';
import '../core/realtime/realtime_hub.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _selectedIndex = 0;

  final _screens = const [
    DashboardScreen(),
    CommandCenterScreen(),
    WorkflowLiveScreen(),
    ApprovalCenterScreen(),
    LogsScreen(),
    KnowledgeScreen(),
    ChannelsScreen(),
    DepartmentsScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final hub = RealtimeHub.instance;

    return AnimatedBuilder(
      animation: hub,
      builder: (context, _) {
        return Scaffold(
          body: Row(
            children: [
              NavigationRail(
                backgroundColor: Colors.indigo.shade900.withValues(alpha: 0.45),
                selectedIndex: _selectedIndex,
                onDestinationSelected: (value) {
                  setState(() => _selectedIndex = value);
                },
                scrollable: true,
                labelType: NavigationRailLabelType.all,
                leading: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                  child: Column(
                    children: [
                      const CircleAvatar(
                        radius: 26,
                        child: Icon(Icons.hub_outlined),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        'Company OS',
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ],
                  ),
                ),
                trailing: Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Badge(
                    isLabelVisible: hub.pendingApprovalCount > 0,
                    label: Text('${hub.pendingApprovalCount}'),
                    child: Icon(
                      hub.isConnected ? Icons.cloud_done : Icons.cloud_off,
                      color: hub.isConnected ? Colors.greenAccent : Colors.redAccent,
                    ),
                  ),
                ),
                destinations: const [
                  NavigationRailDestination(
                    icon: Icon(Icons.space_dashboard_outlined),
                    selectedIcon: Icon(Icons.space_dashboard),
                    label: Text('Dashboard'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.chat_bubble_outline),
                    selectedIcon: Icon(Icons.chat_bubble),
                    label: Text('Command'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.account_tree_outlined),
                    selectedIcon: Icon(Icons.account_tree),
                    label: Text('Workflow'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.approval_outlined),
                    selectedIcon: Icon(Icons.approval),
                    label: Text('Approvals'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.description_outlined),
                    selectedIcon: Icon(Icons.description),
                    label: Text('Logs'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.library_books_outlined),
                    selectedIcon: Icon(Icons.library_books),
                    label: Text('Knowledge'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.forum_outlined),
                    selectedIcon: Icon(Icons.forum),
                    label: Text('Channels'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.groups_2_outlined),
                    selectedIcon: Icon(Icons.groups_2),
                    label: Text('Departments'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.settings_outlined),
                    selectedIcon: Icon(Icons.settings),
                    label: Text('Settings'),
                  ),
                ],
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: Column(
                  children: [
                    Container(
                      height: 56,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.18),
                        border: Border(
                          bottom: BorderSide(color: Colors.grey.shade800),
                        ),
                      ),
                      child: Row(
                        children: [
                          Text(
                            hub.latestTaskTitle.isEmpty
                                ? 'Ready'
                                : 'Current Task: ${hub.latestTaskTitle}',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          const Spacer(),
                          if (hub.activeNode.isNotEmpty)
                            Text(
                              'Active Node: ${hub.activeNode}',
                              style: TextStyle(color: Colors.grey.shade400),
                            ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: IndexedStack(
                        index: _selectedIndex,
                        children: _screens,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
