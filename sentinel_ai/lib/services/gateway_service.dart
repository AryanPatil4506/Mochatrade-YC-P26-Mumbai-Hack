import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../core/error/failures.dart';

/// Wraps all Gateway Service (:8002) endpoints.
class GatewayService {
  const GatewayService._();

  static final _dio = ApiClient.gateway;

  /// GET /v1/approvals?status=... → list of approval records
  static Future<List<Map<String, dynamic>>> listApprovals({String? status}) async {
    try {
      final resp = await _dio.get(
        '/v1/approvals',
        queryParameters: status != null ? {'status': status} : null,
      );
      _checkStatus(resp);
      return (resp.data as List).cast<Map<String, dynamic>>();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /v1/approvals/{id}/resolve → {approval, capability_token}
  static Future<Map<String, dynamic>> resolveApproval(
    String approvalId, {
    required String status, // 'APPROVED' | 'REJECTED'
    String? approverId,
    String? reason,
  }) async {
    try {
      final resp = await _dio.post(
        '/v1/approvals/$approvalId/resolve',
        data: {
          'status': status,
          if (approverId != null) 'approver_id': approverId,
          if (reason != null) 'reason': reason,
        },
      );
      _checkStatus(resp);
      return resp.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /v1/policy → {weights, thresholds, escalation_floors}
  static Future<Map<String, dynamic>> getPolicy() async {
    try {
      final resp = await _dio.get('/v1/policy');
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
      if (resp.statusCode == 409) throw ConflictFailure(detail?.toString() ?? 'Conflict');
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
