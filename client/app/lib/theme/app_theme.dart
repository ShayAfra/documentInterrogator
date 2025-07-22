import 'package:flutter/material.dart';
import 'colors.dart';
import 'typography.dart';

/// Centralized ThemeData for the dark theme
final ThemeData darkTheme = ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: AppColors.clrDarkA0,
  primaryColor: AppColors.clrAccentA1,
  colorScheme: ColorScheme.dark(
    primary: AppColors.clrAccentA1,
    secondary: AppColors.clrAccentA2,
    error: AppColors.clrError,
    background: AppColors.clrDarkA0,
    surface: AppColors.clrDarkA2,
    onPrimary: AppColors.clrDarkA0,
    onSecondary: AppColors.clrDarkA0,
    onBackground: AppColors.clrLightA0,
    onSurface: AppColors.clrLightA0,
    onError: AppColors.clrDarkA0,
  ),
  textTheme: const TextTheme(
    headlineLarge: AppTypography.headlineLarge,
    headlineMedium: AppTypography.headlineMedium,
    bodyMedium: AppTypography.bodyMedium,
    labelLarge: AppTypography.labelLarge,
  ),
  cardColor: AppColors.clrDarkA2,
  errorColor: AppColors.clrError,
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.clrAccentA1,
      foregroundColor: AppColors.clrDarkA0,
      textStyle: AppTypography.labelLarge,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
    ),
  ),
  iconTheme: const IconThemeData(
    color: AppColors.clrLightA0,
  ),
  snackBarTheme: SnackBarThemeData(
    backgroundColor: AppColors.clrDarkA2,  // Your dark surface color (#1E1E1E)
    contentTextStyle: AppTypography.bodyMedium,  // Your 16px white text
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),  // Match your button radius
    ),
    behavior: SnackBarBehavior.floating,  // Optional: floating style
    elevation: 4,  // Optional: shadow depth
  ),
);
