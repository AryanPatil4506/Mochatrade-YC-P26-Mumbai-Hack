import 'package:equatable/equatable.dart';

/// Maps the AuditLog.to_dict() response from GET /v1/audit/timeline
/// and GET /v1/audit/{request_id}.
class AuditLog extends Equatable {
  const AuditLog({
    required this.auditLogId,
    required this.requestId,
    required this.agentId,
    required this.toolName,
    required this.operation,
    required this.riskScore,
    required this.decision,
    this.approvalId,
    required this.executed,
    required this.createdAt,
    this.resolvedAt,
  });

  final String auditLogId;
  final String requestId;
  final String agentId;
  final String toolName;
  final String operation;
  final int riskScore;
  final String decision;
  final String? approvalId;
  final bool executed;
  final DateTime createdAt;
  final DateTime? resolvedAt;

  factory AuditLog.fromJson(Map<String, dynamic> json) => AuditLog(
        auditLogId: json['audit_log_id'] as String,
        requestId: json['request_id'] as String,
        agentId: json['agent_id'] as String,
        toolName: json['tool_name'] as String,
        operation: json['operation'] as String,
        riskScore: json['risk_score'] as int,
        decision: json['decision'] as String,
        approvalId: json['approval_id'] as String?,
        executed: json['executed'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
        resolvedAt: json['resolved_at'] != null
            ? DateTime.tryParse(json['resolved_at'] as String)
            : null,
      );

  /// Derive status string for display (same logic as design #4/#8).
  String get displayStatus {
    if (decision == 'BLOCK') return 'Blocked';
    if (decision == 'REQUIRE_APPROVAL') {
      if (resolvedAt != null) return 'Approved';
      return 'Pending';
    }
    if (executed) return 'Executed';
    return 'Allowed';
  }

  @override
  List<Object?> get props => [auditLogId, requestId, decision, executed];
}
