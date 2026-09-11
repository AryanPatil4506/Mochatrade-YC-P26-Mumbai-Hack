import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Sentinel AI dark theme — matches the reference screenshots.
/// Primary brand: deep dark background + amber accent.
class AppTheme {
  AppTheme._();

  // --- Palette ---
  static const Color background = Color(0xFF0A0C10);
  static const Color surface = Color(0xFF12151C);
  static const Color surfaceVariant = Color(0xFF1A1E28);
  static const Color surfaceElevated = Color(0xFF1F2433);
  static const Color border = Color(0xFF252A36);

  static const Color amber = Color(0xFFF59E0B);
  static const Color amberDim = Color(0xFF92610A);
  static const Color amberLight = Color(0xFFFBBF24);

  static const Color green = Color(0xFF10B981);
  static const Color greenDim = Color(0xFF064E3B);

  static const Color red = Color(0xFFEF4444);
  static const Color redDim = Color(0xFF7F1D1D);

  static const Color orange = Color(0xFFF97316);
  static const Color orangeDim = Color(0xFF7C2D12);

  static const Color cyan = Color(0xFF06B6D4);
  static const Color cyanDim = Color(0xFF164E63);

  static const Color textPrimary = Color(0xFFF1F5F9);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF475569);

  static ThemeData get darkTheme => dark;

  // --- Decision color helpers ---
  static Color decisionColor(String decision) => switch (decision.toUpperCase()) {
        'ALLOW' => green,
        'BLOCK' => red,
        'REQUIRE_APPROVAL' => orange,
        _ => textSecondary,
      };

  static Color decisionBgColor(String decision) => switch (decision.toUpperCase()) {
        'ALLOW' => greenDim,
        'BLOCK' => redDim,
        'REQUIRE_APPROVAL' => orangeDim,
        _ => surfaceVariant,
      };

  static Color riskScoreColor(int score) {
    if (score < 30) return green;
    if (score < 60) return amber;
    if (score < 80) return orange;
    return red;
  }

  static ThemeData get dark {
    final base = ThemeData.dark(useMaterial3: true);
    final textTheme = GoogleFonts.interTextTheme(base.textTheme).copyWith(
      displayLarge: GoogleFonts.inter(color: textPrimary, fontSize: 32, fontWeight: FontWeight.bold),
      headlineLarge: GoogleFonts.inter(color: textPrimary, fontSize: 24, fontWeight: FontWeight.bold),
      headlineMedium: GoogleFonts.inter(color: textPrimary, fontSize: 20, fontWeight: FontWeight.w600),
      titleLarge: GoogleFonts.inter(color: textPrimary, fontSize: 17, fontWeight: FontWeight.w600),
      titleMedium: GoogleFonts.inter(color: textPrimary, fontSize: 15, fontWeight: FontWeight.w500),
      titleSmall: GoogleFonts.inter(color: textSecondary, fontSize: 13, fontWeight: FontWeight.w500),
      bodyLarge: GoogleFonts.inter(color: textPrimary, fontSize: 15),
      bodyMedium: GoogleFonts.inter(color: textSecondary, fontSize: 13),
      bodySmall: GoogleFonts.inter(color: textMuted, fontSize: 11),
      labelLarge: GoogleFonts.inter(color: textPrimary, fontSize: 13, fontWeight: FontWeight.w600),
      labelMedium: GoogleFonts.inter(color: textSecondary, fontSize: 11, fontWeight: FontWeight.w500),
    );

    return base.copyWith(
      colorScheme: const ColorScheme.dark(
        brightness: Brightness.dark,
        primary: amber,
        onPrimary: Color(0xFF000000),
        secondary: amberLight,
        surface: surface,
        onSurface: textPrimary,
        error: red,
        outline: border,
      ),
      scaffoldBackgroundColor: background,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: surface,
        foregroundColor: textPrimary,
        elevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: GoogleFonts.inter(
          color: textPrimary,
          fontSize: 17,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: const IconThemeData(color: textSecondary),
      ),
      drawerTheme: const DrawerThemeData(
        backgroundColor: surface,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: surface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: border, width: 1),
        ),
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 0),
      ),
      dividerTheme: const DividerThemeData(color: border, thickness: 1),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceVariant,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: amber, width: 1.5),
        ),
        hintStyle: GoogleFonts.inter(color: textMuted, fontSize: 14),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: amber,
          foregroundColor: Colors.black,
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: amber,
          side: const BorderSide(color: amber),
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: amber,
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 14),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: surfaceVariant,
        selectedColor: amberDim,
        labelStyle: GoogleFonts.inter(color: textSecondary, fontSize: 12),
        side: const BorderSide(color: border),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      ),
      listTileTheme: const ListTileThemeData(
        tileColor: Colors.transparent,
        textColor: textPrimary,
        iconColor: textSecondary,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: amber,
        unselectedItemColor: textMuted,
        elevation: 0,
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(color: amber),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: amber,
        foregroundColor: Colors.black,
      ),
    );
  }
}
