import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../utils/app_constants.dart';
import '../widgets/custom_button.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const _HomeTab(),
    const _LessonsTab(),
    const _ProfileTab(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppConstants.primaryColor,
        unselectedItemColor: AppConstants.textSecondary,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Trang chủ',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.school),
            label: 'Bài học',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Hồ sơ',
          ),
        ],
      ),
    );
  }
}

class _HomeTab extends StatelessWidget {
  const _HomeTab();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.spacingLarge),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Xin chào!',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      Text(
                        'Chào mừng đến với SpeakWAI',
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                    ],
                  ),
                ),
                CircleAvatar(
                  radius: 25,
                  backgroundColor: AppConstants.primaryColor,
                  child: const Icon(
                    Icons.person,
                    color: AppConstants.textOnPrimary,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: AppConstants.spacingXLarge),
            
            // Quick Stats
            Row(
              children: [
                Expanded(
                  child: _StatCard(
                    title: 'Ngày học',
                    value: '7',
                    icon: Icons.calendar_today,
                    color: AppConstants.primaryColor,
                  ),
                ),
                const SizedBox(width: AppConstants.spacingMedium),
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
            
            const SizedBox(height: AppConstants.spacingXLarge),
            
            // Main Features
            Text(
              'Chức năng chính',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            
            const SizedBox(height: AppConstants.spacingLarge),
            
            // Feature Cards
            _FeatureCard(
              title: 'Luyện nói',
              description: 'Cải thiện kỹ năng phát âm của bạn',
              icon: Icons.record_voice_over,
              color: AppConstants.secondaryColor,
              onTap: () {
                context.push('/home/speaking-practice');
              },
            ),
            
            const SizedBox(height: AppConstants.spacingMedium),
            
            _FeatureCard(
              title: 'Luyện từ vựng',
              description: 'Mở rộng vốn từ vựng tiếng Anh',
              icon: Icons.book,
              color: AppConstants.accentColor,
              onTap: () {
                // TODO: Navigate to vocabulary practice
              },
            ),
            
            const SizedBox(height: AppConstants.spacingMedium),
            
            _FeatureCard(
              title: 'Nghe hiểu',
              description: 'Luyện kỹ năng nghe hiểu tiếng Anh',
              icon: Icons.headphones,
              color: AppConstants.primaryColor,
              onTap: () {
                // TODO: Navigate to listening practice
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _LessonsTab extends StatelessWidget {
  const _LessonsTab();

  @override
  Widget build(BuildContext context) {
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
            
            // Lesson List (placeholder)
            Expanded(
              child: ListView.builder(
                itemCount: 5,
                itemBuilder: (context, index) {
                  return Card(
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppConstants.primaryColor,
                        child: Text(
                          '${index + 1}',
                          style: const TextStyle(
                            color: AppConstants.textOnPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      title: Text('Bài học ${index + 1}'),
                      subtitle: Text('Mô tả bài học ${index + 1}'),
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
        ),
      ),
    );
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
        padding: const EdgeInsets.all(AppConstants.spacingMedium),
        child: Column(
          children: [
            Icon(
              icon,
              color: color,
              size: 32,
            ),
            const SizedBox(height: AppConstants.spacingSmall),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppConstants.spacingSmall),
            Text(
              title,
              style: Theme.of(context).textTheme.bodyMedium,
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
          padding: const EdgeInsets.all(AppConstants.spacingMedium),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppConstants.borderRadiusMedium),
                ),
                child: Icon(
                  icon,
                  color: color,
                  size: 30,
                ),
              ),
              
              const SizedBox(width: AppConstants.spacingMedium),
              
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppConstants.spacingSmall),
                    Text(
                      description,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              
              const Icon(
                Icons.arrow_forward_ios,
                color: AppConstants.textSecondary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}