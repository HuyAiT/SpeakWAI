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

  final List<Widget> _screens = [
    const _HomeTab(),
    _LessonsTab(),
    const _ProfileTab(),
  ];

  @override
  void initState() {
    super.initState();
    _loadLessons();
  }

  Future<void> _loadLessons() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final token = await AuthService.getToken();
      if (token != null) {
        final response = await ApiService.getLessons(token);
        if (response['lessons'] != null) {
          setState(() {
            _lessons = response['lessons'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      debugPrint('Error loading lessons: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
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
}

class _HomeTab extends StatelessWidget {
  const _HomeTab();

  @override
  Widget build(BuildContext context) {
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
              borderRadius: BorderRadius.circular(AppConstants.borderRadiusMedium),
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

          const Row(
            children: [
              Expanded(
                child: _StatCard(
                  title: 'Ngày học',
                  value: '7',
                  icon: Icons.calendar_today,
                  color: AppConstants.primaryColor,
                ),
              ),
              SizedBox(width: AppConstants.spacingSmall),
              Expanded(
                child: _StatCard(
                  title: 'Bài hoàn thành',
                  value: '12',
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
              // TODO: Navigate
            },
          ),

          const SizedBox(height: AppConstants.spacingMedium),

          _FeatureCard(
            title: '🎧 Nghe hiểu',
            description: 'Luyện kỹ năng nghe hiểu tiếng Anh',
            icon: Icons.headphones,
            color: AppConstants.primaryColor,
            onTap: () {
              // TODO: Navigate
            },
          ),
          
          const SizedBox(height: AppConstants.spacingMedium),
        ],
      ),
    );
  }
}

class _LessonsTab extends StatelessWidget {
  const _LessonsTab();

  @override
  Widget build(BuildContext context) {
    final parentState = context.findAncestorStateOfType<_HomeScreenState>();
    final lessons = parentState?._lessons ?? [];
    final isLoading = parentState?._isLoading ?? false;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingLarge),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bài học',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            
            const SizedBox(height: AppConstants.spacingLarge),
            
            // Loading indicator
            if (isLoading) ...[
              const Center(
                child: CircularProgressIndicator(),
              ),
              const SizedBox(height: AppConstants.spacingMedium),
            ] else ...[
              // Lesson List
              Expanded(
                child: lessons.isEmpty
                    ? const Center(
                        child: Text('Chưa có bài học nào'),
                      )
                    : ListView.builder(
                        itemCount: lessons.length,
                        itemBuilder: (context, index) {
                          final lesson = lessons[index];
                          return Card(
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: _getDifficultyColor(lesson['difficulty_level']),
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
                                // TODO: Navigate to lesson detail
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
  const _ProfileTab();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingLarge),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Hồ sơ',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            
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
                      'Người dùng',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    
                    const SizedBox(height: AppConstants.spacingSmall),
                    
                    Text(
                      'user@example.com',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    
                    const SizedBox(height: AppConstants.spacingLarge),
                    
                    CustomButton(
                      text: 'Đăng xuất',
                      isOutlined: true,
                      onPressed: () {
                        // TODO: Implement logout
                        context.go('/login');
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
            Icon(
              icon,
              color: color,
              size: 24,
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              title,
              style: Theme.of(context).textTheme.bodySmall,
            ),
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
                  borderRadius: BorderRadius.circular(AppConstants.borderRadiusMedium),
                ),
                child: Icon(
                  icon,
                  color: color,
                  size: 24,
                ),
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