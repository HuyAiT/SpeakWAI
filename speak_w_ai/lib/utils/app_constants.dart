import 'package:flutter/material.dart';

class AppConstants {
  // App Information
  static const String appName = 'SpeakWAI';
  static const String appVersion = '1.0.0';

  // Colors - Duolingo inspired palette
  static const Color primaryColor = Color(0xFF58CC02); // Duolingo green
  static const Color secondaryColor = Color(0xFFCE82FF); // Purple accent
  static const Color accentColor = Color(0xFFFFAF00); // Orange/yellow accent
  static const Color backgroundColor = Color(0xFFF7F7F7); // Light gray background
  static const Color surfaceColor = Colors.white;
  static const Color errorColor = Color(0xFFEA4335); // Red
  static const Color successColor = Color(0xFF58CC02); // Same as primary
  static const Color warningColor = Color(0xFFFFAF00); // Same as accent
  
  // Additional Duolingo colors
  static const Color blueColor = Color(0xFF1CB0F6); // Duolingo blue
  static const Color lightGreenColor = Color(0xFF89E219); // Light green
  static const Color darkGreenColor = Color(0xFF58A700); // Dark green
  static const Color pinkColor = Color(0xFFFF9600); // Pink/orange
  
  // Text Colors
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color textOnPrimary = Colors.white;

  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primaryColor, lightGreenColor],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient funGradient = LinearGradient(
    colors: [blueColor, secondaryColor],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient warmGradient = LinearGradient(
    colors: [accentColor, pinkColor],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Border Radius
  static const double borderRadiusSmall = 8.0;
  static const double borderRadiusMedium = 12.0;
  static const double borderRadiusLarge = 16.0;

  // Spacing
  static const double spacingSmall = 8.0;
  static const double spacingMedium = 16.0;
  static const double spacingLarge = 24.0;
  static const double spacingXLarge = 32.0;

  // Font Sizes
  static const double fontSizeSmall = 14.0;
  static const double fontSizeMedium = 16.0;
  static const double fontSizeLarge = 18.0;
  static const double fontSizeXLarge = 24.0;
  static const double fontSizeXXLarge = 32.0;

  // API Routes
  static const String baseUrl = 'http://192.168.1.100:3000/api'; // Thay đổi IP máy của bạn
  static const String loginEndpoint = '/login';
  static const String registerEndpoint = '/register';
  static const String lessonsEndpoint = '/lessons';

  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String onboardingKey = 'onboarding_completed';
}