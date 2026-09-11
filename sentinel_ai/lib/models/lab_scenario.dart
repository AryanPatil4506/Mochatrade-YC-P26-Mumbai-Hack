import 'package:equatable/equatable.dart';

class LabScenario extends Equatable {
  const LabScenario({
    required this.id,
    required this.name,
    required this.category,
    required this.description,
    required this.expectedDecision,
  });

  final String id;
  final String name;
  final String category;
  final String description;
  final String expectedDecision;

  factory LabScenario.fromJson(Map<String, dynamic> json) => LabScenario(
        id: json['id'] as String,
        name: json['name'] as String,
        category: json['category'] as String,
        description: json['description'] as String,
        expectedDecision: json['expected_decision'] as String,
      );

  @override
  List<Object?> get props => [id];
}

class LabResult extends Equatable {
  const LabResult({
    required this.scenario,
    required this.proposedAction,
    required this.decision,
    this.execution,
    required this.executed,
  });

  final String scenario;
  final Map<String, dynamic> proposedAction;
  final Map<String, dynamic> decision;
  final Map<String, dynamic>? execution;
  final bool executed;

  String get decisionValue => decision['decision'] as String? ?? 'UNKNOWN';
  int get riskScore => decision['risk_score'] as int? ?? 0;

  factory LabResult.fromJson(Map<String, dynamic> json) => LabResult(
        scenario: json['scenario'] as String,
        proposedAction: json['proposed_action'] as Map<String, dynamic>,
        decision: json['decision'] as Map<String, dynamic>,
        execution: json['execution'] as Map<String, dynamic>?,
        executed: json['executed'] as bool? ?? false,
      );

  @override
  List<Object?> get props => [scenario, decisionValue];
}
