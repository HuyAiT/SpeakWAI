import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_constants.dart';

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppConstants.primaryColor,
        brightness: Brightness.light,
        primary: AppConstants.primaryColor,
        secondary: AppConstants.secondaryColor,
        surface: AppConstants.surfaceColor,
        background: AppConstants.backgroundColor,
        error: AppConstants.errorColor,
      ),
      
      // App Bar Theme
      appBarTheme: AppBarTheme(
        backgroundColor: AppConstants.primaryColor,
        foregroundColor: AppConstants.textOnPrimary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.nunito(
          color: AppConstants.textOnPrimary,
          fontSize: AppConstants.fontSizeLarge,
          fontWeight: FontWeight.w700,
        ),
      ),
      
      // Text Theme - More playful with Nunito
      textTheme: GoogleFonts.nunitoTextTheme().copyWith(
        displayLarge: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeXXLarge,
          fontWeight: FontWeight.w800,
          color: AppConstants.textPrimary,
        ),
        displayMedium: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeXLarge,
          fontWeight: FontWeight.w800,
          color: AppConstants.textPrimary,
        ),
        headlineLarge: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeXLarge,
          fontWeight: FontWeight.w700,
          color: AppConstants.textPrimary,
        ),
        headlineMedium: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeLarge,
          fontWeight: FontWeight.w700,
          color: AppConstants.textPrimary,
        ),
        bodyLarge: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeMedium,
          color: AppConstants.textPrimary,
        ),
        bodyMedium: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeMedium,
          color: AppConstants.textSecondary,
        ),
        labelLarge: GoogleFonts.nunito(
          fontSize: AppConstants.fontSizeMedium,
          fontWeight: FontWeight.w700,
          color: AppConstants.textOnPrimary,
        ),
      ),
      
      // Elevated Button Theme - More rounded and playful
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppConstants.primaryColor,
          foregroundColor: AppConstants.textOnPrimary,
          elevation: 3,
          shadowColor: AppConstants.primaryColor.withOpacity(0.3),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppConstants.spacingXLarge,
            vertical: AppConstants.spacingMedium,
          ),
          textStyle: GoogleFonts.nunito(
            fontSize: AppConstants.fontSizeMedium,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      
      // Outlined Button Theme
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppConstants.primaryColor,
          side: const BorderSide(color: AppConstants.primaryColor, width: 3),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppConstants.spacingXLarge,
            vertical: AppConstants.spacingMedium,
          ),
          textStyle: GoogleFonts.nunito(
            fontSize: AppConstants.fontSizeMedium,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      
      // Text Button Theme
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppConstants.primaryColor,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.borderRadiusMedium),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppConstants.spacingMedium,
            vertical: AppConstants.spacingSmall,
          ),
          textStyle: GoogleFonts.nunito(
            fontSize: AppConstants.fontSizeMedium,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      
      // Input Decoration Theme - More playful
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppConstants.surfaceColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          borderSide: BorderSide(color: AppConstants.textSecondary.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          borderSide: BorderSide(color: AppConstants.textSecondary.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          borderSide: const BorderSide(color: AppConstants.primaryColor, width: 3),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
          borderSide: const BorderSide(color: AppConstants.errorColor, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppConstants.spacingLarge,
          vertical: AppConstants.spacingMedium,
        ),
        hintStyle: GoogleFonts.nunito(
          color: AppConstants.textSecondary,
          fontSize: AppConstants.fontSizeMedium,
          fontWeight: FontWeight.w500,
        ),
        labelStyle: GoogleFonts.nunito(
          color: AppConstants.textSecondary,
          fontSize: AppConstants.fontSizeMedium,
          fontWeight: FontWeight.w600,
        ),
      ),
      
      // Card Theme - More rounded and colorful
      cardTheme: CardThemeData(
        color: AppConstants.surfaceColor,
        elevation: 4,
        shadowColor: Colors.black.withOpacity(0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
        ),
        margin: const EdgeInsets.all(AppConstants.spacingSmall),
      ),
      
      // Floating Action Button Theme
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: AppConstants.accentColor,
        foregroundColor: AppConstants.textOnPrimary,
        elevation: 6,
        shape: const CircleBorder(),
      ),
    );
  }
}