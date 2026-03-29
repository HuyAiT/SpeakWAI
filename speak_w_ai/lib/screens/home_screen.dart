import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/app_constants.dart';
import '../widgets/custom_button.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;
  List<dynamic> _lessons = [];
  bool _isLoading = false;
  Map<String, dynamic>? _userProfile;
  Map<String, dynamic>? _userStats;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final token = await AuthService.getToken();
      if (token != null) {
        // Load lessons
        final lessonsResponse = await ApiService.getLessons(token);
        if (lessonsResponse['lessons'] != null) {
          _lessons = lessonsResponse['lessons'];
        }

        // Load profile
        try {
          final profileResponse = await ApiService.getProfile(token);
          if (profileResponse['user'] != null) {
            _userProfile = profileResponse['user'];
          }
        } catch (e) {
          debugPrint('Error loading profile: $e');
        }

        // Load stats
        try {
          final statsResponse = await ApiService.getUserStats(token);
          if (statsResponse['stats'] != null) {
            _userStats = statsResponse['stats'];
          }
        } catch (e) {
          debugPrint('Error loading stats: $e');
        }
      }
    } catch (e) {
      debugPrint('Error loading data: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: [
          _HomeTab(
            lessons: _lessons,
            userStats: _userStats,
            isLoading: _isLoading,
          ),
          _LessonsTab(lessons: _lessons, isLoading: _isLoading),
          _ProfileTab(userProfile: _userProfile, onLogout: _handleLogout),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _selectedIndex,
          onTap: (index) {
            setState(() {
              _selectedIndex = index;
            });
          },
          type: BottomNavigationBarType.fixed,
          selectedItemColor: AppConstants.primaryColor,
          unselectedItemColor: AppConstants.textSecondary,
          selectedLabelStyle: GoogleFonts.nunito(
            fontWeight: FontWeight.w800,
            fontSize: 12,
          ),
          unselectedLabelStyle: GoogleFonts.nunito(
            fontWeight: FontWeight.w600,
            fontSize: 12,
          ),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home),
              activeIcon: Icon(Icons.home_filled),
              label: 'Trang chủ',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.school),
              activeIcon: Icon(Icons.school),
              label: 'Bài học',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person),
              activeIcon: Icon(Icons.person),
              label: 'Hồ sơ',
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogout() async {
    await AuthService.logout();
    if (mounted) {
      context.go('/login');
    }
  }
}

class _HomeTab extends StatelessWidget {
  final List<dynamic> lessons;
  final Map<String, dynamic>? userStats;
  final bool isLoading;

  const _HomeTab({
    required this.lessons,
    this.userStats,
    required this.isLoading,
  });

  @override
  Widget build(BuildContext context) {
    final practiceDays = userStats?['practice_days'] ?? 0;
    final lessonsCompleted = userStats?['lessons_completed'] ?? 0;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.symmetric(
          horizontal: AppConstants.spacingMedium,
          vertical: AppConstants.spacingSmall,
        ),
        children: [
          // --- Header ---
          Container(
            padding: const EdgeInsets.all(AppConstants.spacingSmall),
            decoration: BoxDecoration(
              gradient: AppConstants.funGradient,
              borderRadius: BorderRadius.circular(
                AppConstants.borderRadiusMedium,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppConstants.secondaryColor.withOpacity(0.15),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '🎉 Xin chào!',
                        style: GoogleFonts.nunito(
                          fontSize: AppConstants.fontSizeMedium,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Học tiếng Anh vui mỗi ngày!',
                        style: GoogleFonts.nunito(
                          fontSize: AppConstants.fontSizeSmall,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 2,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.emoji_emotions,
                    color: AppConstants.primaryColor,
                    size: 18,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: AppConstants.spacingMedium),

          // Stats cards with real data
          Row(
            children: [
              Expanded(
                child: _StatCard(
                  title: 'Ngày học',
                  value: practiceDays.toString(),
                  icon: Icons.calendar_today,
                  color: AppConstants.primaryColor,
                ),
              ),
              const SizedBox(width: AppConstants.spacingSmall),
              Expanded(
                child: _StatCard(
                  title: 'Bài hoàn thành',
                  value: lessonsCompleted.toString(),
                  icon: Icons.check_circle,
                  color: AppConstants.successColor,
                ),
              ),
            ],
          ),

          const SizedBox(height: AppConstants.spacingSmall),

          Text(
            'Chức năng chính',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontSize: AppConstants.fontSizeLarge,
            ),
          ),

          const SizedBox(height: AppConstants.spacingLarge),

          // --- Feature Cards ---
          _FeatureCard(
            title: '🎤 Luyện nói',
            description: 'Cải thiện kỹ năng phát âm của bạn',
            icon: Icons.record_voice_over,
            color: AppConstants.secondaryColor,
            onTap: () {
              context.push('/home/speaking-practice');
            },
          ),

          const SizedBox(height: AppConstants.spacingMedium),

          _FeatureCard(
            title: '📚 Luyện từ vựng',
            description: 'Mở rộng vốn từ vựng tiếng Anh',
            icon: Icons.book,
            color: AppConstants.accentColor,
            onTap: () {
              context.push('/home/vocabulary');
            },
          ),

          const SizedBox(height: AppConstants.spacingMedium),

          _FeatureCard(
            title: '🎧 Nghe hiểu',
            description: 'Luyện kỹ năng nghe hiểu tiếng Anh',
            icon: Icons.headphones,
            color: AppConstants.primaryColor,
            onTap: () {
              context.push('/home/listening');
            },
          ),

          const SizedBox(height: AppConstants.spacingMedium),
        ],
      ),
    );
  }
}

class _LessonsTab extends StatelessWidget {
  final List<dynamic> lessons;
  final bool isLoading;

  const _LessonsTab({required this.lessons, required this.isLoading});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingLarge),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Bài học', style: Theme.of(context).textTheme.headlineMedium),

            const SizedBox(height: AppConstants.spacingLarge),

            // Loading indicator
            if (isLoading) ...[
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: AppConstants.spacingMedium),
            ] else ...[
              // Lesson List
              Expanded(
                child: lessons.isEmpty
                    ? const Center(child: Text('Chưa có bài học nào'))
                    : ListView.builder(
                        itemCount: lessons.length,
                        itemBuilder: (context, index) {
                          final lesson = lessons[index];
                          return Card(
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: _getDifficultyColor(
                                  lesson['difficulty_level'],
                                ),
                                child: Text(
                                  '${index + 1}',
                                  style: const TextStyle(
                                    color: AppConstants.textOnPrimary,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              title: Text(lesson['title']),
                              subtitle: Text(
                                _getDifficultyText(lesson['difficulty_level']),
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                              trailing: const Icon(Icons.arrow_forward_ios),
                              onTap: () {
                                context.push('/home/lesson/${lesson['id']}');
                              },
                            ),
                          );
                        },
                      ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getDifficultyColor(String difficulty) {
    switch (difficulty) {
      case 'beginner':
        return AppConstants.successColor;
      case 'intermediate':
        return AppConstants.accentColor;
      case 'advanced':
        return AppConstants.primaryColor;
      default:
        return AppConstants.textSecondary;
    }
  }

  String _getDifficultyText(String difficulty) {
    switch (difficulty) {
      case 'beginner':
        return 'Sơ cấp';
      case 'intermediate':
        return 'Trung cấp';
      case 'advanced':
        return 'Nâng cao';
      default:
        return 'Không xác định';
    }
  }
}

class _ProfileTab extends StatelessWidget {
  final Map<String, dynamic>? userProfile;
  final VoidCallback onLogout;

  const _ProfileTab({this.userProfile, required this.onLogout});

  @override
  Widget build(BuildContext context) {
    final username = userProfile?['username'] ?? 'Người dùng';
    final email = userProfile?['email'] ?? '';
    final createdAt = userProfile?['created_at'];

    String joinDate = '';
    if (createdAt != null) {
      try {
        final date = DateTime.parse(createdAt);
        joinDate = 'Tham gia: ${date.day}/${date.month}/${date.year}';
      } catch (_) {}
    }

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingLarge),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Hồ sơ', style: Theme.of(context).textTheme.headlineMedium),

            const SizedBox(height: AppConstants.spacingLarge),

            // Profile Information
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppConstants.spacingMedium),
                child: Column(
                  children: [
                    const CircleAvatar(
                      radius: 50,
                      backgroundColor: AppConstants.primaryColor,
                      child: Icon(
                        Icons.person,
                        size: 50,
                        color: AppConstants.textOnPrimary,
                      ),
                    ),

                    const SizedBox(height: AppConstants.spacingMedium),

                    Text(
                      username,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),

                    const SizedBox(height: AppConstants.spacingSmall),

                    Text(
                      email,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppConstants.textSecondary,
                      ),
                    ),

                    if (joinDate.isNotEmpty) ...[
                      const SizedBox(height: AppConstants.spacingSmall),
                      Text(
                        joinDate,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppConstants.textSecondary,
                        ),
                      ),
                    ],

                    const SizedBox(height: AppConstants.spacingLarge),

                    CustomButton(
                      text: 'Đăng xuất',
                      isOutlined: true,
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Đăng xuất'),
                            content: const Text(
                              'Bạn có chắc chắn muốn đăng xuất?',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(context),
                                child: const Text('Hủy'),
                              ),
                              ElevatedButton(
                                onPressed: () {
                                  Navigator.pop(context);
                                  onLogout();
                                },
                                child: const Text('Đăng xuất'),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingSmall),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 2),
            Text(
              value,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(title, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _FeatureCard({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.borderRadiusMedium),
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.spacingSmall),
          child: Row(
            children: [
              Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(
                    AppConstants.borderRadiusMedium,
                  ),
                ),
                child: Icon(icon, color: color, size: 24),
              ),

              const SizedBox(width: AppConstants.spacingSmall),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                        fontSize: AppConstants.fontSizeMedium,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      description,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontSize: AppConstants.fontSizeSmall,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              const Icon(
                Icons.arrow_forward_ios,
                color: AppConstants.textSecondary,
                size: 16,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
