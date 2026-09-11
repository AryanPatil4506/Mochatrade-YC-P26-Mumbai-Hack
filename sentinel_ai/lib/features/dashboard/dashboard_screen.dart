import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'dashboard_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/sentinel_drawer.dart';
import '../../widgets/decision_chip.dart';
import '../../models/audit_log.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(dashboardStatsProvider);
    final eventsAsync = ref.watch(globalEventsProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      drawer: const SentinelDrawer(currentRoute: '/dashboard'),
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.security, color: AppTheme.amber, size: 22),
            SizedBox(width: 8),
            Text('Dashboard'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: () => ref.refresh(auditTimelineProvider),
          ),
          eventsAsync.when(
            data: (_) => const Padding(
              padding: EdgeInsets.only(right: 16),
              child: Center(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.fiber_manual_record, color: AppTheme.green, size: 12),
                    SizedBox(width: 4),
                    Text('LIVE', style: TextStyle(color: AppTheme.green, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
            loading: () => const Padding(
              padding: EdgeInsets.only(right: 16),
              child: Center(
                child: SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.amber),
                ),
              ),
            ),
            error: (_, __) => const Padding(
              padding: EdgeInsets.only(right: 16),
              child: Icon(Icons.cloud_off, color: AppTheme.textMuted, size: 18),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.amber,
        backgroundColor: AppTheme.surface,
        onRefresh: () async => ref.refresh(auditTimelineProvider.future),
        child: statsAsync.when(
          data: (stats) => _buildDashboardContent(context, stats),
          loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.amber),
          ),
          error: (err, stack) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.error_outline, color: AppTheme.red, size: 48),
                  const SizedBox(height: 16),
                  Text(
                    'Failed to connect to Executor service (:8003)',
                    style: Theme.of(context).textTheme.titleMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    err.toString(),
                    style: Theme.of(context).textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.amber,
                      foregroundColor: Colors.black,
                    ),
                    onPressed: () => ref.refresh(auditTimelineProvider),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry Connection'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDashboardContent(BuildContext context, DashboardStats stats) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Security Summary banner
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.amberDim.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.shield_outlined, color: AppTheme.amber, size: 28),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Enforcement Active',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Deterministic risk scoring with fail-closed gatekeeping',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // KPI Stat Cards Grid
        Row(
          children: [
            Expanded(
              child: _StatCard(
                title: 'Total Evaluated',
                value: stats.total.toString(),
                icon: Icons.analytics_outlined,
                color: AppTheme.cyan,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatCard(
                title: 'Allowed',
                value: stats.allowed.toString(),
                icon: Icons.check_circle_outline,
                color: AppTheme.green,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _StatCard(
                title: 'Pending Review',
                value: stats.pendingApproval.toString(),
                icon: Icons.pending_actions,
                color: AppTheme.amber,
                onTap: () => context.go('/approvals'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatCard(
                title: 'Blocked Attacks',
                value: stats.blocked.toString(),
                icon: Icons.gpp_bad_outlined,
                color: AppTheme.red,
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),

        // Quick Navigation Section
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Quick Workflows',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _QuickActionBtn(
                icon: Icons.smart_toy_outlined,
                label: 'Agent Chat',
                color: AppTheme.cyan,
                onTap: () => context.go('/chat'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _QuickActionBtn(
                icon: Icons.approval_outlined,
                label: 'Approvals',
                color: AppTheme.amber,
                onTap: () => context.go('/approvals'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _QuickActionBtn(
                icon: Icons.science_outlined,
                label: 'Attack Lab',
                color: AppTheme.red,
                onTap: () => context.go('/lab'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),

        // Recent Audit Activity Header
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Recent Evaluated Actions',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            TextButton(
              onPressed: () => context.go('/timeline'),
              child: const Text('View All', style: TextStyle(color: AppTheme.amber)),
            ),
          ],
        ),
        const SizedBox(height: 8),

        if (stats.recentLogs.isEmpty)
          Container(
            padding: const EdgeInsets.all(28),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.border),
            ),
            child: Column(
              children: [
                const Icon(Icons.inbox_outlined, color: AppTheme.textMuted, size: 40),
                const SizedBox(height: 12),
                Text(
                  'No evaluated actions yet',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 4),
                Text(
                  'Trigger a query in Agent Chat or run an Attack Lab scenario',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          )
        else
          ...stats.recentLogs.map((log) => _RecentLogCard(log: log)),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
    this.onTap,
  });

  final String title;
  final String value;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.textMuted)),
                Icon(icon, color: color, size: 18),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickActionBtn extends StatelessWidget {
  const _QuickActionBtn({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(height: 6),
            Text(
              label,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppTheme.textPrimary),
            ),
          ],
        ),
      ),
    );
  }
}

class _RecentLogCard extends StatelessWidget {
  const _RecentLogCard({required this.log});

  final AuditLog log;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.border),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.surfaceVariant,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.build_circle_outlined, color: AppTheme.textSecondary, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      log.toolName,
                      style: const TextStyle(fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(width: 6),
                    Text('• ${log.operation}', style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  'Risk Score: ${log.riskScore}/100',
                  style: TextStyle(
                    fontSize: 12,
                    color: log.riskScore >= 70
                        ? AppTheme.red
                        : (log.riskScore >= 35 ? AppTheme.amber : AppTheme.green),
                  ),
                ),
              ],
            ),
          ),
          DecisionChip(decision: log.decision, compact: true),
        ],
      ),
    );
  }
}
