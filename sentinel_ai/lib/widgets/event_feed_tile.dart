import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../models/audit_log.dart';
import 'decision_chip.dart';

/// Timeline event tile used in the Incident Timeline screen.
class EventFeedTile extends StatelessWidget {
  const EventFeedTile({
    super.key,
    required this.log,
    this.onTap,
  });

  final AuditLog log;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final timeStr = _formatTime(log.createdAt);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Timeline dot
            Column(
              children: [
                const SizedBox(height: 2),
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: AppTheme.decisionColor(log.decision),
                    shape: BoxShape.circle,
                  ),
                ),
              ],
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        timeStr,
                        style: const TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 11,
                          fontFeatures: [FontFeature.tabularFigures()],
                        ),
                      ),
                      const SizedBox(width: 8),
                      DecisionChip(decision: log.decision, compact: true),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${log.agentId} • ${log.toolName} • ${log.operation}',
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _describeAction(log),
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Risk score
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  'Risk: ${log.riskScore}',
                  style: TextStyle(
                    color: AppTheme.riskScoreColor(log.riskScore),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final local = dt.toLocal();
    final m = local.minute.toString().padLeft(2, '0');
    final ampm = local.hour >= 12 ? 'PM' : 'AM';
    final h12 = local.hour > 12 ? local.hour - 12 : (local.hour == 0 ? 12 : local.hour);
    return '${h12.toString().padLeft(2, '0')}:$m $ampm';
  }

  String _describeAction(AuditLog log) {
    if (log.decision == 'BLOCK') return 'Action blocked due to high-risk operation.';
    if (log.decision == 'REQUIRE_APPROVAL') return 'Awaiting human approval.';
    if (log.executed) return 'Action executed successfully.';
    return 'Action allowed.';
  }
}
