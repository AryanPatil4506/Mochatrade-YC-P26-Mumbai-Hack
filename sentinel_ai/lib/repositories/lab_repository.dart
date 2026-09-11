import '../models/lab_scenario.dart';
import '../services/executor_service.dart';

class LabRepository {
  const LabRepository();

  Future<List<LabScenario>> listScenarios() async {
    final data = await ExecutorService.listScenarios();
    return data.map(LabScenario.fromJson).toList();
  }

  Future<LabResult> runScenario(String scenarioId, {Map<String, dynamic>? overrides}) async {
    final data = await ExecutorService.runScenario(scenarioId, overrides: overrides);
    return LabResult.fromJson(data);
  }
}
