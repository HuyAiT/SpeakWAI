# SpeakWAI - Ứng dụng học tiếng Anh thông minh

SpeakWAI là một ứng dụng di động học tiếng Anh được xây dựng với Flutter và Node.js backend, cung cấp các tính năng luyện nói, từ vựng và nghe hiểu một cách tương tác và vui nhộn.

## 📋 Mục lục

- [Tổng quan dự án](#tổng-quan-dự-án)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Tính năng chính](#tính-năng-chính)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
- [Cách hoạt động của code](#cách-hoạt-động-của-code)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)

## 🎯 Tổng quan dự án

SpeakWAI là một ứng dụng học tiếng Anh toàn diện với giao diện thân thiện, được thiết kế theo phong cách Duolingo với màu sắc tươi sáng và trải nghiệm học tập vui nhộn. Ứng dụng giúp người dùng cải thiện kỹ năng tiếng Anh qua các bài tập tương tác.

### Công nghệ sử dụng

**Frontend (Flutter):**
- Flutter 3.9.2+
- Go Router cho navigation
- Provider cho state management
- Speech to Text cho nhận dạng giọng nói
- Google Fonts cho typography

**Backend (Node.js):**
- Node.js 16.0.0+
- Express.js framework
- MySQL database
- JWT authentication
- Bcrypt cho password hashing

## 📁 Cấu trúc dự án

```
SpeakWAI/
├── speak_w_ai/                    # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart             # Entry point
│   │   ├── screens/              # UI screens
│   │   │   ├── login_screen.dart
│   │   │   ├── register_screen.dart
│   │   │   ├── home_screen.dart
│   │   │   └── speaking_practice_screen.dart
│   │   ├── widgets/              # Reusable widgets
│   │   │   ├── custom_button.dart
│   │   │   └── custom_text_field.dart
│   │   ├── services/             # Business logic
│   │   │   ├── api_service.dart
│   │   │   └── auth_service.dart
│   │   ├── utils/                # Utilities
│   │   │   ├── app_constants.dart
│   │   │   └── app_theme.dart
│   │   └── routes/               # Navigation
│   │       └── app_router.dart
│   ├── pubspec.yaml              # Flutter dependencies
│   └── android/                  # Android configuration
├── backend/                       # Node.js backend
│   ├── server.js                 # Main server file
│   ├── package.json              # Node.js dependencies
│   ├── requirements.txt          # Python-style requirements list
│   ├── database.sql              # Database schema
│   ├── .env                      # Environment variables
│   └── MYSQL_SETUP.md            # Database setup guide
└── README.md                     # This file
```

## ✨ Tính năng chính

### 🔐 Authentication
- Đăng ký tài khoản mới với email và password
- Đăng nhập với token JWT
- Lưu trạng thái đăng nhập локально

### 🏠 Home Screen
- Dashboard với thống kê học tập
- Truy cập nhanh các tính năng chính
- Navigation bar với 3 tab: Trang chủ, Bài học, Hồ sơ

### 🎤 Speaking Practice
- Luyện nói với các câu mẫu tiếng Anh
- Ghi âm và nhận dạng giọng nói (speech-to-text)
- Phản hồi ngay lập tức về phát âm
- Progress tracking qua các bài học

### 📚 Lesson Management
- Quản lý bài học theo 3 cấp độ: beginner, intermediate, advanced
- Load bài học từ server
- Display bài học với difficulty indicators

### 👤 User Profile
- Hiển thị thông tin người dùng
- Đăng xuất và xóa dữ liệu lokal

## 🚀 Hướng dẫn cài đặt

### Prerequisites
- Flutter SDK 3.9.2+
- Node.js 16.0.0+
- MySQL 8.0+
- Android Studio / Xcode cho mobile development

### Backend Setup

1. **Clone repository:**
```bash
git clone <repository-url>
cd SpeakWAI/backend
```

2. **Install dependencies:**
```bash
npm install
# Hoặc sử dụng requirements.txt
pip install -r requirements.txt  # (Chỉ để tham khảo)
```

3. **Database setup:**
```bash
# Tạo database và import schema
mysql -u root -p < database.sql
```

4. **Environment configuration:**
```bash
# Copy và edit .env file
cp .env.example .env
# Thay đổi các giá trị:
# DB_PASSWORD=your_mysql_password
# JWT_SECRET=your-secret-key
```

5. **Start server:**
```bash
npm run dev  # Development mode
npm start    # Production mode
```

### Flutter App Setup

1. **Navigate to Flutter directory:**
```bash
cd speak_w_ai
```

2. **Install dependencies:**
```bash
flutter pub get
```

3. **Update API URL:**
- Mở file `lib/utils/app_constants.dart`
- Thay đổi `baseUrl` thành IP address của server:
```dart
static const String baseUrl = 'http://YOUR_IP:3000/api';
```

4. **Run app:**
```bash
flutter run
```

## 🔄 Cách hoạt động của code

### 1. App Initialization & Navigation

**Main Entry Point ([`main.dart`](speak_w_ai/lib/main.dart:1)):**
```dart
void main() {
  runApp(const SpeakWAIApp());
}

class SpeakWAIApp extends StatelessWidget {
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
```

**Router Configuration ([`app_router.dart`](speak_w_ai/lib/routes/app_router.dart:1)):**
- Sử dụng Go Router cho navigation
- Định nghĩa routes: `/login`, `/register`, `/home`, `/speaking-practice`
- Error handling cho unknown routes

### 2. Authentication Flow

**Login Process ([`login_screen.dart`](speak_w_ai/lib/screens/login_screen.dart:30)):**
1. User nhập email và password
2. Form validation với regex cho email
3. Gọi `ApiService.login()` với HTTP request
4. Server validates và returns JWT token
5. `AuthService.saveToken()` lưu token locally
6. Navigate đến home screen

**API Service ([`api_service.dart`](speak_w_ai/lib/services/api_service.dart:9)):**
```dart
static Future<Map<String, dynamic>> login(String email, String password) async {
  final response = await http.post(
    Uri.parse('$_baseUrl${AppConstants.loginEndpoint}'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'email': email, 'password': password}),
  );
  // Handle response...
}
```

**Auth Service ([`auth_service.dart`](speak_w_ai/lib/services/auth_service.dart:8)):**
- Sử dụng SharedPreferences để lưu token và user data
- Cung cấp methods: `saveToken()`, `getToken()`, `isLoggedIn()`, `logout()`

### 3. Backend Server Architecture

**Server Setup ([`server.js`](backend/server.js:1)):**
```javascript
const express = require('express');
const mysql = require('mysql2');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const helmet = require('helmet');
```

**Database Connection:**
```javascript
const db = mysql.createConnection({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'speakwai_db',
  port: process.env.DB_PORT || 3306
});
```

**JWT Middleware:**
```javascript
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};
```

### 4. Speaking Practice Feature

**UI Components ([`speaking_practice_screen.dart`](speak_w_ai/lib/screens/speaking_practice_screen.dart:14)):**
- Progress indicator hiển thị tiến độ
- Card hiển thị câu cần đọc
- Microphone button với recording states
- Result display cho speech recognition

**Recording Logic:**
```dart
void _toggleRecording() {
  setState(() {
    if (_isRecording) {
      _isRecording = false;
      _isProcessing = true;
      _processRecording();
    } else {
      _isRecording = true;
      _userSpeech = '';
      // TODO: Start actual recording
    }
  });
}
```

**Speech Processing:**
- Simulated processing với 2-second delay
- Future implementation: integration with speech-to-text API
- Display kết quả và cho phép chuyển câu tiếp theo

### 5. Home Screen Architecture

**Tab Navigation ([`home_screen.dart`](speak_w_ai/lib/screens/home_screen.dart:16)):**
```dart
final List<Widget> _screens = [
  const _HomeTab(),
  _LessonsTab(),
  const _ProfileTab(),
];
```

**State Management:**
- Sử dụng StatefulWidget cho home screen
- Load lessons từ API khi khởi tạo
- Manage loading states và error handling

**Feature Cards:**
- Interactive cards cho các tính năng chính
- Navigation đến respective screens
- Consistent styling với gradients và shadows

## 🏗️ Kiến trúc hệ thống

### Frontend Architecture
- **MVVM Pattern**: Screens (View) -> Services (ViewModel) -> API (Model)
- **State Management**: Provider pattern cho local state
- **Navigation**: Go Router cho declarative routing
- **UI Components**: Reusable widgets với consistent styling

### Backend Architecture
- **RESTful API**: Standard HTTP methods và status codes
- **Authentication**: JWT tokens với middleware protection
- **Database**: Relational MySQL với proper indexing
- **Security**: Helmet, CORS, bcrypt password hashing

### Data Flow
1. **User Interaction** → Flutter Widget
2. **Event Handler** → Service Layer
3. **HTTP Request** → Express.js Server
4. **Business Logic** → Database Query
5. **Response** → JSON Data
6. **UI Update** → State Management

## 📡 API Documentation

### Authentication Endpoints

**POST /api/register**
```json
Request:
{
  "username": "string",
  "email": "string", 
  "password": "string"
}

Response:
{
  "message": "User registered successfully",
  "token": "jwt_token",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

**POST /api/login**
```json
Request:
{
  "email": "string",
  "password": "string"
}

Response:
{
  "message": "Login successful",
  "token": "jwt_token",
  "user": {
    "id": 1,
    "username": "string", 
    "email": "string"
  }
}
```

### Protected Endpoints (JWT Required)

**GET /api/lessons**
```json
Headers:
Authorization: Bearer <jwt_token>

Response:
{
  "lessons": [
    {
      "id": 1,
      "title": "Hello, how are you?",
      "content": "Learn basic greeting phrases",
      "difficulty_level": "beginner",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

**GET /api/profile**
```json
Headers:
Authorization: Bearer <jwt_token>

Response:
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## 🎨 Design System

### Color Palette (Duolingo Inspired)
- **Primary Green**: `#58CC02` 
- **Secondary Purple**: `#CE82FF`
- **Accent Orange**: `#FFFFAF00`
- **Blue**: `#1CB0F6`
- **Light Green**: `#89E219`

### Typography
- **Font**: Google Fonts (Nunito)
- **Weights**: 600 (Semi-bold), 800 (Bold)
- **Sizes**: Responsive scaling system

### Components
- **Custom Buttons**: Gradient backgrounds with shadows
- **Text Fields**: Consistent styling with validation
- **Cards**: Rounded corners with elevation
- **Progress Indicators**: Linear và circular variants

## 🔧 Development Guidelines

### Code Style
- **Dart**: Follow official Flutter style guide
- **JavaScript**: ESLint configuration with Airbnb style
- **Naming**: Descriptive variable và function names
- **Comments**: JSDoc cho JavaScript, DartDoc cho Dart

### Git Workflow
- **Branches**: feature/, bugfix/, hotfix/
- **Commits**: Conventional commit messages
- **Pull Requests**: Code review required

### Testing
- **Flutter**: Widget testing với flutter_test
- **Backend**: Unit testing với Jest
- **Integration**: API testing với Supertest

## 🚀 Future Enhancements

### Planned Features
- [ ] Advanced speech recognition with pronunciation scoring
- [ ] Gamification với points và streaks
- [ ] Social features (leaderboards, friends)
- [ ] Offline mode support
- [ ] Multi-language support
- [ ] AI-powered lesson recommendations

### Technical Improvements
- [ ] Real-time communication với WebSockets
- [ ] Caching strategy với Redis
- [ ] Microservices architecture
- [ ] CI/CD pipeline setup
- [ ] Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Development Team**: SpeakWAI Team
- **Design**: UI/UX inspired by modern language learning apps
- **Special Thanks**: Flutter và Node.js communities

## 📞 Contact

For support and questions:
- Email: support@speakwai.com
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)

---

**Happy Learning! 🎓🚀**