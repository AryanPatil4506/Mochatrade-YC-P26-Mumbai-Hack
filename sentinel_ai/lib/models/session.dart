import 'package:equatable/equatable.dart';

class AgentSession extends Equatable {
  const AgentSession({
    required this.sessionId,
    required this.agentId,
    this.transcript = const [],
  });

  final String sessionId;
  final String agentId;
  final List<Map<String, dynamic>> transcript;

  factory AgentSession.fromJson(Map<String, dynamic> json) => AgentSession(
        sessionId: json['session_id'] as String,
        agentId: json['agent_id'] as String,
        transcript: (json['transcript'] as List<dynamic>?)
                ?.cast<Map<String, dynamic>>() ??
            const [],
      );

  @override
  List<Object?> get props => [sessionId, agentId];
}

class ChatMessage extends Equatable {
  const ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
    this.eventType,
    this.metadata,
  });

  final String role; // 'user' | 'agent' | 'system' | 'event'
  final String content;
  final DateTime timestamp;
  final String? eventType;
  final Map<String, dynamic>? metadata;

  @override
  List<Object?> get props => [role, content, timestamp];
}
