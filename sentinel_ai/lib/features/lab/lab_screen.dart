import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../models/lab_scenario.dart';
import '../../repositories/lab_repository.dart';
import '../../services/executor_service.dart';
import '../../widgets/sentinel_drawer.dart';

const _labRepo = LabRepository();

final labScenariosProvider = FutureProvider.autoDispose<List<LabScenario>>((ref) async {
  return _labRepo.listScenarios();
});

class LabScreen extends ConsumerStatefulWidget {
  const LabScreen({super.key});

  @override
  ConsumerState<LabScreen> createState() => _LabScreenState();
}

class _LabScreenState extends ConsumerState<LabScreen> {
  String? _runningScenarioId;
  Map<String, dynamic>? _lastResult;

  Future<void> _runScenario(String scenarioId) async {
    setState(() {
      _runningScenarioId = scenarioId;
      _lastResult = null;
    });

    try {
      final res = await ExecutorService.runScenario(scenarioId);
      if (mounted) {
        setState(() => _lastResult = res);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Scenario $scenarioId completed.'),
            backgroundColor: AppTheme.amber,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Simulation error: $e'), backgroundColor: AppTheme.red),
        );
      }
    } finally {
      if (mounted) setState(() => _runningScenarioId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scenariosAsync = ref.watch(labScenariosProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      drawer: const SentinelDrawer(currentRoute: '/lab'),
      appBar: AppBar(
        title: const Text('Attack Simulation Lab'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(labScenariosProvider),
          ),
        ],
      ),
      body: scenariosAsync.when(
        data: (scenarios) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.border),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.science_outlined, color: AppTheme.red, size: 28),
                    SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Adversarial Benchmark Suite',
                            style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Inject synthetic multi-turn attacks to verify policy enforcement and gatekeeping.',
                            style: TextStyle(color: AppTheme.textMuted, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              if (_lastResult != null) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceVariant,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.amber.withValues(alpha: 0.5)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.assessment, color: AppTheme.amber, size: 18),
                          SizedBox(width: 8),
                          Text('Simulation Output', style: TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _lastResult.toString(),
                        style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              Text('Available Scenarios', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              if (scenarios.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(
                    child: Text('No attack scenarios registered on Executor (:8003)', style: TextStyle(color: AppTheme.textMuted)),
                  ),
                )
              else
                ...scenarios.map((s) {
                  final isRunning = _runningScenarioId == s.id;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppTheme.border),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(s.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                              const SizedBox(height: 4),
                              Text(s.description, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isRunning ? AppTheme.surfaceVariant : AppTheme.red,
                            foregroundColor: Colors.white,
                          ),
                          onPressed: isRunning ? null : () => _runScenario(s.id),
                          child: isRunning
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Text('Execute'),
                        ),
                      ],
                    ),
                  );
                }),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.amber)),
        error: (err, _) => Center(child: Text('Error: $err', style: const TextStyle(color: AppTheme.red))),
      ),
    );
  }
}
