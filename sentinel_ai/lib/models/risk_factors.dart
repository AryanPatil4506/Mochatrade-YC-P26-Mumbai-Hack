import 'package:equatable/equatable.dart';

class RiskFactors extends Equatable {
  const RiskFactors({
    required this.toolSensitivity,
    required this.dataSensitivity,
    required this.privilegeLevel,
    required this.destinationRisk,
    required this.reversibility,
    required this.injectionSignal,
    required this.behavioralAnomaly,
  });

  final int toolSensitivity;
  final int dataSensitivity;
  final int privilegeLevel;
  final int destinationRisk;
  final int reversibility;
  final int injectionSignal;
  final int behavioralAnomaly;

  factory RiskFactors.fromJson(Map<String, dynamic> json) => RiskFactors(
        toolSensitivity: json['tool_sensitivity'] as int? ?? 0,
        dataSensitivity: json['data_sensitivity'] as int? ?? 0,
        privilegeLevel: json['privilege_level'] as int? ?? 0,
        destinationRisk: json['destination_risk'] as int? ?? 0,
        reversibility: json['reversibility'] as int? ?? 0,
        injectionSignal: json['injection_signal'] as int? ?? 0,
        behavioralAnomaly: json['behavioral_anomaly'] as int? ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'tool_sensitivity': toolSensitivity,
        'data_sensitivity': dataSensitivity,
        'privilege_level': privilegeLevel,
        'destination_risk': destinationRisk,
        'reversibility': reversibility,
        'injection_signal': injectionSignal,
        'behavioral_anomaly': behavioralAnomaly,
      };

  List<MapEntry<String, int>> get entries => [
        MapEntry('Tool Sensitivity', toolSensitivity),
        MapEntry('Data Sensitivity', dataSensitivity),
        MapEntry('Privilege Level', privilegeLevel),
        MapEntry('Destination Risk', destinationRisk),
        MapEntry('Reversibility', reversibility),
        MapEntry('Injection Signal', injectionSignal),
        MapEntry('Behavioral Anomaly', behavioralAnomaly),
      ];

  @override
  List<Object?> get props => [
        toolSensitivity, dataSensitivity, privilegeLevel,
        destinationRisk, reversibility, injectionSignal, behavioralAnomaly,
      ];
}
