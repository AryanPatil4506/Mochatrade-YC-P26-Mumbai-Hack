import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../models/audit_log.dart';
import '../../repositories/audit_repository.dart';
import '../../widgets/sentinel_drawer.dart';
import '../../widgets/event_feed_tile.dart';

const _auditRepo = AuditRepository();

final auditLogsProvider = FutureProvider.autoDispose<List<AuditLog>>((ref) async {
  return _auditRepo.getTimeline(limit: 100);
});

class AuditTimelineScreen extends ConsumerWidget {
  const AuditTimelineScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final logsAsync = ref.watch(auditLogsProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      drawer: const SentinelDrawer(currentRoute: '/timeline'),
      appBar: AppBar(
        title: const Text('Incident Timeline & Audit'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(auditLogsProvider),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.amber,
        backgroundColor: AppTheme.surface,
        onRefresh: () async => ref.refresh(auditLogsProvider.future),
        child: logsAsync.when(
          data: (logs) {
            if (logs.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.history_toggle_off, color: AppTheme.textMuted, size: 48),
                      const SizedBox(height: 16),
                      Text('No Audit Events', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 4),
                      const Text(
                        'Audit timeline logs appear here as agent actions are evaluated and executed.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppTheme.textMuted, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              );
            }

            return ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: logs.length,
              itemBuilder: (context, index) {
                return EventFeedTile(log: logs[index]);
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.amber)),
          error: (err, _) => Center(
            child: Text('Error: $err', style: const TextStyle(color: AppTheme.red)),
          ),
        ),
      ),
    );
  }
}
