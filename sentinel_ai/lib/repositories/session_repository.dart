import '../models/session.dart';
import '../services/agent_service.dart';

class SessionRepository {
  const SessionRepository();

  Future<AgentSession> createSession(String agentId) async {
    final data = await AgentService.createSession(agentId);
    return AgentSession(
      sessionId: data['session_id'] as String,
      agentId: data['agent_id'] as String,
    );
  }

  Future<void> sendMessage(String sessionId, String message) async {
    await AgentService.sendMessage(sessionId, message);
  }

  Future<AgentSession> getSession(String sessionId) async {
    final data = await AgentService.getSession(sessionId);
    return AgentSession.fromJson(data);
  }

  Future<Map<String, dynamic>> simulateCompromise() async {
    return AgentService.simulateCompromise();
  }
}
