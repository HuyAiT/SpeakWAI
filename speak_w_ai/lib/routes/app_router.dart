import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../screens/login_screen.dart';
import '../screens/register_screen.dart';
import '../screens/home_screen.dart';
import '../screens/speaking_practice_screen.dart';
import '../screens/lesson_detail_screen.dart';
import '../screens/vocabulary_screen.dart';
import '../screens/listening_screen.dart';

class AppRouter {
  static const String login = '/login';
  static const String register = '/register';
  static const String home = '/home';
  static const String speakingPractice = '/speaking-practice';
  static const String lessonDetail = '/lesson';
  static const String vocabulary = '/vocabulary';
  static const String listening = '/listening';

  static final GoRouter router = GoRouter(
    initialLocation: login,
    routes: [
      // Login Screen
      GoRoute(
        path: login,
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),

      // Register Screen
      GoRoute(
        path: register,
        name: 'register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Home Screen
      GoRoute(
        path: home,
        name: 'home',
        builder: (context, state) => const HomeScreen(),
        routes: [
          // Speaking Practice Screen (nested under home)
          GoRoute(
            path: speakingPractice,
            name: 'speaking-practice',
            builder: (context, state) => const SpeakingPracticeScreen(),
          ),
          // Lesson Detail Screen
          GoRoute(
            path: 'lesson/:id',
            name: 'lesson-detail',
            builder: (context, state) {
              final lessonId = state.pathParameters['id'] ?? '0';
              return LessonDetailScreen(lessonId: lessonId);
            },
          ),
          // Vocabulary Screen
          GoRoute(
            path: vocabulary,
            name: 'vocabulary',
            builder: (context, state) => const VocabularyScreen(),
          ),
          // Listening Screen
          GoRoute(
            path: listening,
            name: 'listening',
            builder: (context, state) => const ListeningScreen(),
          ),
        ],
      ),
    ],

    // Error handling
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Page not found',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'The requested page could not be found.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(login),
              child: const Text('Go to Login'),
            ),
          ],
        ),
      ),
    ),
  );
}
