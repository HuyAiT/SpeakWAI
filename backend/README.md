# SpeakWAI Backend API

Backend REST API cho ứng dụng SpeakWAI sử dụng Node.js, Express và MySQL.

## Cài đặt

### 1. Cài đặt Node.js
```bash
# Tải và cài đặt Node.js từ https://nodejs.org/
node --version
```

### 2. Cài đặt MySQL
```bash
# Sử dụng XAMPP, MAMP hoặc cài đặt MySQL trực tiếp
# Hoặc sử dụng Docker:
docker run --name mysql -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0
```

### 3. Cài đặt dependencies
```bash
cd backend
npm install
```

### 4. Cấu hình môi trường
```bash
# Sao chép file .env.example thành .env và cấu hình lại
cp .env.example .env
```

### 5. Tạo database
```bash
# Import file SQL vào MySQL
mysql -u root -p < database.sql
```

## Cấu trúc Project

```
backend/
├── package.json          # Dependencies và scripts
├── server.js            # Main server file
├── database.sql         # Database schema
├── .env                # Environment variables
└── README.md            # This file
```

## API Endpoints

### Authentication

#### POST /api/register
Đăng ký người dùng mới.

**Request Body:**
```json
{
  "username": "string",
  "email": "string", 
  "password": "string"
}
```

**Response:**
```json
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

#### POST /api/login
Đăng nhập người dùng.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
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

### Lessons

#### GET /api/lessons
Lấy danh sách bài học (cần JWT token).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
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

#### GET /api/profile
Lấy thông tin profile người dùng (cần JWT token).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## Chạy Server

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

Server sẽ chạy trên port 3000 (hoặc port được cấu hình trong .env).

## Bảo mật

- Password được hash sử dụng bcrypt
- JWT tokens có thời hạn 24 giờ
- CORS được cấu hình cho frontend
- Helmet được sử dụng cho security headers

## Database Schema

### Users Table
- `id` - Primary key, auto increment
- `username` - Unique username
- `email` - Unique email
- `password_hash` - Hashed password
- `created_at` - Timestamp khi tạo user

### Lessons Table
- `id` - Primary key, auto increment
- `title` - Tiêu đề bài học
- `content` - Nội dung bài học
- `difficulty_level` - beginner/intermediate/advanced
- `created_at` - Timestamp khi tạo bài học

## Testing

Sử dụng Postman hoặc Insomnia để test các API endpoints:

1. **Register:** POST http://localhost:3000/api/register
2. **Login:** POST http://localhost:3000/api/login  
3. **Get Lessons:** GET http://localhost:3000/api/lessons (với Authorization header)
4. **Get Profile:** GET http://localhost:3000/api/profile (với Authorization header)

## Environment Variables

Tạo file `.env` với các biến sau:
```
PORT=3000
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=speakwai_db
DB_PORT=3306
JWT_SECRET=your-secret-key
FRONTEND_URL=http://localhost:8080