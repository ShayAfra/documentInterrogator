import 'package:flutter/material.dart';
import 'colors.dart';

/// Centralized text styles for the dark theme
class AppTypography {
  static const TextStyle headlineLarge = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    color: AppColors.clrLightA0,
  );
  static const TextStyle headlineMedium = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: AppColors.clrLightA0,
  );
  static const TextStyle bodyMedium = TextStyle(
    fontSize: 16,
    color: AppColors.clrLightA0,
  );
  static const TextStyle labelLarge = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    color: AppColors.clrAccentA1,
  );
}
