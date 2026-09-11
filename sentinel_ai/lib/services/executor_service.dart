import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../core/error/failures.dart';

/// Wraps all Executor Service (:8003) endpoints.
class ExecutorService {
  const ExecutorService._();

  static final _dio = ApiClient.executor;

  /// GET /v1/audit/timeline?limit=N → list of audit log entries
  static Future<List<Map<String, dynamic>>> getAuditTimeline({int limit = 50}) async {
    try {
      final resp = await _dio.get('/v1/audit/timeline', queryParameters: {'limit': limit});
      _checkStatus(resp);
      return (resp.data as List).cast<Map<String, dynamic>>();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /v1/audit/{request_id} → single audit log entry
  static Future<Map<String, dynamic>> getAuditEntry(String requestId) async {
    try {
      final resp = await _dio.get('/v1/audit/$requestId');
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /v1/lab/scenarios → list of attack scenarios
  static Future<List<Map<String, dynamic>>> listScenarios() async {
    try {
      final resp = await _dio.get('/v1/lab/scenarios');
      _checkStatus(resp);
      return (resp.data as List).cast<Map<String, dynamic>>();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /v1/lab/run/{scenario_id} → simulation result
  static Future<Map<String, dynamic>> runScenario(
    String scenarioId, {
    Map<String, dynamic>? overrides,
  }) async {
    try {
      final resp = await _dio.post(
        '/v1/lab/run/$scenarioId',
        data: overrides,
        options: Options(receiveTimeout: const Duration(seconds: 60)),
      );
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /health
  static Future<bool> healthCheck() async {
    try {
      final resp = await _dio.get('/health');
      return resp.statusCode == 200;
    } catch (_) {
      return false;
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
