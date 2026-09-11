import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/audit_log.dart';
import '../../repositories/audit_repository.dart';
import '../../core/config/app_config.dart';
import '../../core/network/sse_client.dart';

// ---------- Providers ----------

const _auditRepo = AuditRepository();

final auditTimelineProvider = FutureProvider<List<AuditLog>>((ref) async {
  return _auditRepo.getTimeline(limit: AppConfig.auditTimelineDefaultLimit);
});

/// Dashboard stats derived from the timeline.
final dashboardStatsProvider = Provider<AsyncValue<_DashboardStats>>((ref) {
  return ref.watch(auditTimelineProvider).whenData((logs) => _DashboardStats.from(logs));
});

/// SSE live events from executor's global bus.
final globalEventsProvider = StreamProvider<Map<String, dynamic>>((ref) {
  return SseClient.subscribe('${AppConfig.executorBaseUrl}/v1/events');
});

class _DashboardStats {
  const _DashboardStats({
    required this.total,
    required this.allowed,
    required this.pendingApproval,
    required this.blocked,
    required this.recentLogs,
  });

  final int total;
  final int allowed;
  final int pendingApproval;
  final int blocked;
  final List<AuditLog> recentLogs;

  factory _DashboardStats.from(List<AuditLog> logs) {
    int allowed = 0, pending = 0, blocked = 0;
    for (final log in logs) {
      switch (log.decision) {
        case 'ALLOW':
          allowed++;
        case 'REQUIRE_APPROVAL':
          pending++;
        case 'BLOCK':
          blocked++;
      }
    }
    // Show most recent 10
    final recent = logs.take(10).toList();
    return _DashboardStats(
      total: logs.length,
      allowed: allowed,
      pendingApproval: pending,
      blocked: blocked,
      recentLogs: recent,
    );
  }
}

// Export for screen access
typedef DashboardStats = _DashboardStats;
