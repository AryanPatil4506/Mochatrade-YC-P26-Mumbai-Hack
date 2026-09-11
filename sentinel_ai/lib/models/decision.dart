import 'package:equatable/equatable.dart';
import 'risk_factors.dart';

class Decision extends Equatable {
  const Decision({
    required this.requestId,
    required this.decision,
    required this.riskScore,
    required this.riskFactors,
    this.policyRuleTriggered,
    this.explanation,
    required this.requiresHumanApproval,
    this.capabilityToken,
    required this.timestamp,
    required this.auditLogId,
  });

  final String requestId;
  final String decision; // ALLOW | REQUIRE_APPROVAL | BLOCK
  final int riskScore;
  final RiskFactors riskFactors;
  final String? policyRuleTriggered;
  final String? explanation;
  final bool requiresHumanApproval;
  final String? capabilityToken;
  final DateTime timestamp;
  final String auditLogId;

  factory Decision.fromJson(Map<String, dynamic> json) => Decision(
        requestId: json['request_id'] as String,
        decision: json['decision'] as String,
        riskScore: json['risk_score'] as int,
        riskFactors: RiskFactors.fromJson(json['risk_factors'] as Map<String, dynamic>),
        policyRuleTriggered: json['policy_rule_triggered'] as String?,
        explanation: json['explanation'] as String?,
        requiresHumanApproval: json['requires_human_approval'] as bool? ?? false,
        capabilityToken: json['capability_token'] as String?,
        timestamp: DateTime.parse(json['timestamp'] as String),
        auditLogId: json['audit_log_id'] as String,
      );

  @override
  List<Object?> get props => [requestId, decision, riskScore, timestamp];
}
