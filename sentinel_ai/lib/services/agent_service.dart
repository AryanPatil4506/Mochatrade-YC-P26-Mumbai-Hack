import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../core/error/failures.dart';

/// Wraps all Agent Service (:8001) endpoints.
class AgentService {
  const AgentService._();

  static final _dio = ApiClient.agent;

  /// POST /v1/agent/sessions → {session_id, agent_id}
  static Future<Map<String, dynamic>> createSession(String agentId) async {
    try {
      final resp = await _dio.post('/v1/agent/sessions', data: {'agent_id': agentId});
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /v1/agent/messages → 202 accepted
  static Future<void> sendMessage(String sessionId, String userRequest) async {
    try {
      final resp = await _dio.post('/v1/agent/messages', data: {
        'session_id': sessionId,
        'user_request': userRequest,
      });
      _checkStatus(resp);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /v1/agent/sessions/{id} → transcript + taint ledger
  static Future<Map<String, dynamic>> getSession(String sessionId) async {
    try {
      final resp = await _dio.get('/v1/agent/sessions/$sessionId');
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /v1/agent/simulate-compromise
  static Future<Map<String, dynamic>> simulateCompromise() async {
    try {
      final resp = await _dio.post('/v1/agent/simulate-compromise');
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  static void _checkStatus(Response resp) {
    if (resp.statusCode != null && resp.statusCode! >= 400) {
      final detail = (resp.data is Map) ? (resp.data['detail'] ?? resp.statusMessage) : resp.statusMessage;
      if (resp.statusCode == 404) throw const NotFoundFailure();
      throw ServerFailure(detail?.toString() ?? 'Server error', statusCode: resp.statusCode);
    }
  }

  static Failure _mapDioError(DioException e) {
    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout) {
      return const NetworkFailure();
    }
    return ServerFailure(e.message ?? 'Unknown error', statusCode: e.response?.statusCode);
  }
}
