import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// Badge chip for displaying ALLOW / REQUIRE_APPROVAL / BLOCK decisions.
class DecisionChip extends StatelessWidget {
  const DecisionChip({
    super.key,
    required this.decision,
    this.compact = false,
  });

  final String decision;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final label = switch (decision.toUpperCase()) {
      'ALLOW' => 'ALLOW',
      'BLOCK' => 'BLOCK',
      'REQUIRE_APPROVAL' => 'PENDING',
      _ => decision.toUpperCase(),
    };

    final color = AppTheme.decisionColor(decision);
    final bg = AppTheme.decisionBgColor(decision);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 10,
        vertical: compact ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: compact ? 10 : 11,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
