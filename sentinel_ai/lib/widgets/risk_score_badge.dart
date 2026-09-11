import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// Circular risk score gauge (e.g. 91/100) as seen in the Request Details design.
class RiskScoreBadge extends StatelessWidget {
  const RiskScoreBadge({
    super.key,
    required this.score,
    this.size = 72,
    this.strokeWidth = 7,
  });

  final int score;
  final double size;
  final double strokeWidth;

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.riskScoreColor(score);
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        fit: StackFit.expand,
        children: [
          CircularProgressIndicator(
            value: score / 100,
            strokeWidth: strokeWidth,
            backgroundColor: AppTheme.surfaceVariant,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            strokeCap: StrokeCap.round,
          ),
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$score',
                  style: TextStyle(
                    color: color,
                    fontSize: size * 0.28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '/ 100',
                  style: TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: size * 0.13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
