import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/app_constants.dart';

class ApiService {
  static const String _baseUrl = AppConstants.baseUrl;

  // Login
  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl${AppConstants.loginEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Login failed');
      }
    } catch (e) {
      throw Exception('Login error: $e');
    }
  }

  // Register
  static Future<Map<String, dynamic>> register(
    String username,
    String email,
    String password,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl${AppConstants.registerEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 201) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Registration failed');
      }
    } catch (e) {
      throw Exception('Registration error: $e');
    }
  }

  // Forgot Password
  static Future<Map<String, dynamic>> forgotPassword(String email) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/forgot-password'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to send reset email');
      }
    } catch (e) {
      throw Exception('Forgot password error: $e');
    }
  }

  // Get Lessons
  static Future<Map<String, dynamic>> getLessons(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl${AppConstants.lessonsEndpoint}'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get lessons: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Get lessons error: $e');
    }
  }

  // Get Lesson Detail
  static Future<Map<String, dynamic>> getLessonDetail(
    String token,
    int lessonId,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl${AppConstants.lessonsEndpoint}/$lessonId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get lesson: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Get lesson detail error: $e');
    }
  }

  // Get Profile
  static Future<Map<String, dynamic>> getProfile(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl${AppConstants.profileEndpoint}'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get profile: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Get profile error: $e');
    }
  }

  // Get User Stats
  static Future<Map<String, dynamic>> getUserStats(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/user/stats'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        // Return default stats if API fails
        return {
          'stats': {
            'lessons_completed': 0,
            'practice_days': 0,
            'vocabulary_learned': 0,
            'listening_completed': 0,
          },
        };
      }
    } catch (e) {
      // Return default stats on error
      return {
        'stats': {
          'lessons_completed': 0,
          'practice_days': 0,
          'vocabulary_learned': 0,
          'listening_completed': 0,
        },
      };
    }
  }

  // Update User Progress
  static Future<Map<String, dynamic>> updateProgress(
    String token, {
    int lessonCompleted = 0,
    int vocabularyLearned = 0,
    int listeningCompleted = 0,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/user/progress'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'lesson_completed': lessonCompleted,
          'vocabulary_learned': vocabularyLearned,
          'listening_completed': listeningCompleted,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to update progress: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Update progress error: $e');
    }
  }

  // Check AI Server Health
  static Future<Map<String, dynamic>> checkAIHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/ai/health'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {
          'ai_server': 'disconnected',
          'error': 'Status ${response.statusCode}',
        };
      }
    } catch (e) {
      return {'ai_server': 'disconnected', 'error': e.toString()};
    }
  }

  // Score Pronunciation (base64 audio)
  static Future<Map<String, dynamic>> scorePronunciation(
    String token,
    String audioBase64, {
    String? expectedText,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/ai/score-base64'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'audio': audioBase64, 'text': expectedText ?? ''}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 503) {
        throw Exception('AI server đang offline. Vui lòng thử lại sau.');
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['message'] ?? 'Scoring failed');
      }
    } catch (e) {
      throw Exception('Lỗi chấm điểm: $e');
    }
  }
}
