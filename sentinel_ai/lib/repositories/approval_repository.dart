import '../models/approval_record.dart';
import '../services/gateway_service.dart';

class ApprovalRepository {
  const ApprovalRepository();

  Future<List<ApprovalRecord>> listApprovals({String? status}) async {
    final data = await GatewayService.listApprovals(status: status);
    return data.map(ApprovalRecord.fromJson).toList();
  }

  Future<Map<String, dynamic>> resolve(
    String approvalId, {
    required String status,
    String? approverId,
    String? reason,
  }) async {
    return GatewayService.resolveApproval(
      approvalId,
      status: status,
      approverId: approverId,
      reason: reason,
    );
  }
}
