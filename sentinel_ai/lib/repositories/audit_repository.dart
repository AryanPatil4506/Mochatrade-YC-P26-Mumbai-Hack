import '../models/audit_log.dart';
import '../services/executor_service.dart';

class AuditRepository {
  const AuditRepository();

  Future<List<AuditLog>> getTimeline({int limit = 50}) async {
    final data = await ExecutorService.getAuditTimeline(limit: limit);
    return data.map(AuditLog.fromJson).toList();
  }

  Future<AuditLog> getEntry(String requestId) async {
    final data = await ExecutorService.getAuditEntry(requestId);
    return AuditLog.fromJson(data);
  }
}
