import 'package:flutter/material.dart';
import 'utils/app_constants.dart';
import 'utils/app_theme.dart';
import 'routes/app_router.dart';

void main() {
  runApp(const SpeakWAIApp());
}

class SpeakWAIApp extends StatelessWidget {
  const SpeakWAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: AppConstants.appName,
      theme: AppTheme.lightTheme,
      routerConfig: AppRouter.router,
      debugShowCheckedModeBanner: false,
    );
  }
}
