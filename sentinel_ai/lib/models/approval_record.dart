import 'package:equatable/equatable.dart';

class ApprovalRecord extends Equatable {
  const ApprovalRecord({
    required this.approvalId,
    required this.requestId,
    required this.status,
    this.approverId,
    this.reason,
    this.resolvedAt,
    this.riskScore,
    this.riskFactors,
    this.agentId,
    this.toolName,
    this.operation,
    this.createdAt,
  });

  final String approvalId;
  final String requestId;
  final String status; // PENDING | APPROVED | REJECTED
  final String? approverId;
  final String? reason;
  final DateTime? resolvedAt;

  // Enriched from audit log (joined in repository)
  final int? riskScore;
  final Map<String, dynamic>? riskFactors;
  final String? agentId;
  final String? toolName;
  final String? operation;
  final DateTime? createdAt;

  factory ApprovalRecord.fromJson(Map<String, dynamic> json) => ApprovalRecord(
        approvalId: json['approval_id'] as String,
        requestId: json['request_id'] as String,
        status: json['status'] as String,
        approverId: json['approver_id'] as String?,
        reason: json['reason'] as String?,
        resolvedAt: json['resolved_at'] != null
            ? DateTime.tryParse(json['resolved_at'] as String)
            : null,
        riskScore: json['risk_score'] as int?,
        riskFactors: json['risk_factors'] as Map<String, dynamic>?,
        agentId: json['agent_id'] as String?,
        toolName: json['tool_name'] as String?,
        operation: json['operation'] as String?,
        createdAt: json['created_at'] != null
            ? DateTime.tryParse(json['created_at'] as String)
            : null,
      );

  @override
  List<Object?> get props => [approvalId, status];
}
