import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../models/approval_record.dart';
import '../../repositories/approval_repository.dart';
import '../../widgets/sentinel_drawer.dart';

const _approvalRepo = ApprovalRepository();

final approvalsListProvider = FutureProvider.autoDispose<List<ApprovalRecord>>((ref) async {
  return _approvalRepo.listApprovals();
});

class ApprovalsScreen extends ConsumerWidget {
  const ApprovalsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final approvalsAsync = ref.watch(approvalsListProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      drawer: const SentinelDrawer(currentRoute: '/approvals'),
      appBar: AppBar(
        title: const Text('Human Approval Queue'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(approvalsListProvider),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.amber,
        backgroundColor: AppTheme.surface,
        onRefresh: () async => ref.refresh(approvalsListProvider.future),
        child: approvalsAsync.when(
          data: (records) {
            if (records.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.check_circle_outline, color: AppTheme.green, size: 54),
                      const SizedBox(height: 16),
                      Text('Queue Clear', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 6),
                      const Text(
                        'No actions currently require human approval authorization.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
              );
            }

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: records.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final record = records[index];
                return _ApprovalCard(
                  record: record,
                  onResolved: () => ref.refresh(approvalsListProvider),
                );
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

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({required this.record, required this.onResolved});

  final ApprovalRecord record;
  final VoidCallback onResolved;

  Future<void> _handleResolve(BuildContext context, String status) async {
    try {
      await _approvalRepo.resolve(
        record.approvalId,
        status: status,
        approverId: 'admin-mobile-user',
        reason: status == 'APPROVED' ? 'Approved via Sentinel Mobile' : 'Rejected via Sentinel Mobile',
      );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(status == 'APPROVED' ? 'Action Approved. Token generated.' : 'Action Rejected.'),
            backgroundColor: status == 'APPROVED' ? AppTheme.green : AppTheme.red,
          ),
        );
      }
      onResolved();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e'), backgroundColor: AppTheme.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPending = record.status == 'PENDING';

    return Container(
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
              Text(
                'Approval #${record.approvalId.substring(0, 8)}',
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isPending
                      ? AppTheme.amberDim.withValues(alpha: 0.3)
                      : (record.status == 'APPROVED'
                          ? AppTheme.greenDim.withValues(alpha: 0.3)
                          : AppTheme.redDim.withValues(alpha: 0.3)),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  record.status,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: isPending
                        ? AppTheme.amber
                        : (record.status == 'APPROVED' ? AppTheme.green : AppTheme.red),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Request ID: ${record.requestId}',
            style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
          ),
          if (record.reason != null) ...[
            const SizedBox(height: 6),
            Text('Reason: ${record.reason}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
          ],
          if (isPending) ...[
            const Divider(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.red,
                      side: const BorderSide(color: AppTheme.red),
                    ),
                    icon: const Icon(Icons.close, size: 18),
                    label: const Text('Reject'),
                    onPressed: () => _handleResolve(context, 'REJECTED'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.green,
                      foregroundColor: Colors.black,
                    ),
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('Approve'),
                    onPressed: () => _handleResolve(context, 'APPROVED'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
