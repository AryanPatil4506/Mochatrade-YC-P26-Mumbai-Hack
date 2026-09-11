import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sentinel_ai/main.dart';
import 'package:sentinel_ai/features/dashboard/dashboard_provider.dart';

void main() {
  testWidgets('Sentinel AI app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          globalEventsProvider.overrideWith((ref) => Stream.value({'type': 'init'})),
          auditTimelineProvider.overrideWith((ref) async => []),
        ],
        child: const SentinelApp(),
      ),
    );
    // Pump frames to complete the build without looping on infinite animation
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(SentinelApp), findsOneWidget);
  });
}
