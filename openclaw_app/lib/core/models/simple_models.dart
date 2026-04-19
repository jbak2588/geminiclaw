class DashboardOverview {
  final int projectsCount;
  final int tasksCount;
  final int pendingApprovals;
  final int knowledgeCount;
  final int channelMessages;

  const DashboardOverview({
    required this.projectsCount,
    required this.tasksCount,
    required this.pendingApprovals,
    required this.knowledgeCount,
    required this.channelMessages,
  });

  factory DashboardOverview.fromJson(Map<String, dynamic> json) {
    return DashboardOverview(
      projectsCount: json['projects_count'] as int? ?? 0,
      tasksCount: json['tasks_count'] as int? ?? 0,
      pendingApprovals: json['pending_approvals'] as int? ?? 0,
      knowledgeCount: json['knowledge_count'] as int? ?? 0,
      channelMessages: json['channel_messages'] as int? ?? 0,
    );
  }
}
