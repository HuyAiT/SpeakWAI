# SpeakWAI

SpeakWAI is an English pronunciation learning application designed for Vietnamese learners. The system uses a fine-tuned WavLM deep learning model to evaluate and score user pronunciation in real time, providing detailed feedback across multiple speech dimensions.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [AI Model](#ai-model)
- [Database Schema](#database-schema)
- [License](#license)

## Overview

The application consists of four main components:

- **Mobile App** (Flutter) -- cross-platform client for learners
- **Backend API** (Node.js / Express) -- RESTful API server handling authentication, lesson management, and user progress
- **Admin Panel** (React / Vite) -- web-based dashboard for content and user administration
- **AI Inference Server** (Python / FastAPI) -- pronunciation scoring service powered by a fine-tuned WavLM model

## System Architecture

```
+---------------------------+         +---------------------------+
|     Flutter Mobile App    |         |    React Admin Panel      |
|       (Android / iOS)     |         |     (Vite, port 5173)     |
+------------+--------------+         +------------+--------------+
             |  REST / JSON                        |  REST / JSON
             v                                     v
+--------------------------------------------------------------+
|               Node.js Express Backend (port 3000)            |
|                                                              |
|   Middleware: helmet, CORS, JWT auth, multer                 |
|   Routes: /api/register, /api/login, /api/lessons,           |
|           /api/profile, /api/user/*, /api/admin/*,           |
|           /api/ai/*                                          |
+---------------------+--------------------+-------------------+
                      |                    |
                      v                    v
        +-------------+------+   +---------+---------+
        |   MySQL Database   |   | Python AI Server  |
        |    (port 3306)     |   | FastAPI (port 8000)|
        |                    |   |                    |
        | Tables:            |   | WavLM Base Plus   |
        |  - users           |   | + scoring heads   |
        |  - lessons         |   | (best_model.pt)   |
        |  - user_progress   |   |                    |
        +--------------------+   +--------------------+
```

## Technology Stack

### Mobile App

| Component         | Technology              | Version   |
|-------------------|-------------------------|-----------|
| Framework         | Flutter / Dart           | SDK 3.9.2+|
| Navigation        | go_router                | 14.8.1    |
| State Management  | Provider                 | 6.1.2     |
| Audio Recording   | record                   | 6.0.0     |
| Audio Playback    | audioplayers             | 6.1.0     |
| HTTP Client       | http                     | 1.2.1     |
| Local Storage     | shared_preferences       | 2.2.3     |
| Permissions       | permission_handler       | 12.0.1    |
| Typography        | google_fonts (Nunito)    | 6.2.1     |

### Backend API

| Component         | Technology               | Version   |
|-------------------|--------------------------|-----------|
| Runtime           | Node.js                  | 16.0.0+   |
| Framework         | Express.js               | 4.18.2    |
| Database Driver   | mysql2                   | 3.6.5     |
| Authentication    | jsonwebtoken             | 9.0.2     |
| Password Hashing  | bcryptjs                 | 2.4.3     |
| Security Headers  | helmet                   | 7.1.0     |
| File Upload       | multer                   | 2.0.2     |
| HTTP Client       | axios                    | 1.13.2    |

### Admin Panel

| Component         | Technology               | Version   |
|-------------------|--------------------------|-----------|
| UI Library        | React                    | 19.2.0    |
| Routing           | react-router-dom         | 7.10.1    |
| Build Tool        | Vite                     | 7.2.4     |

### AI Inference Server

| Component         | Technology               | Version   |
|-------------------|--------------------------|-----------|
| Framework         | FastAPI                  | 0.100.0+  |
| ASGI Server       | uvicorn                  | 0.22.0+   |
| Deep Learning     | PyTorch                  | 2.0.0+    |
| Model Backbone    | WavLM Base Plus (HuggingFace Transformers) | 4.30.0+ |
| Audio Processing  | librosa                  | 0.10.0+   |

### Database

| Component         | Technology               | Version   |
|-------------------|--------------------------|-----------|
| RDBMS             | MySQL                    | 8.0+      |

## Project Structure

```
SpeakWAI/
|
|-- speak_w_ai/                          # Flutter mobile application
|   |-- lib/
|   |   |-- main.dart                    # Application entry point
|   |   |-- routes/
|   |   |   +-- app_router.dart          # GoRouter route definitions
|   |   |-- screens/
|   |   |   |-- login_screen.dart        # Login with forgot-password dialog
|   |   |   |-- register_screen.dart     # User registration
|   |   |   |-- home_screen.dart         # Main tabbed interface (Home/Lessons/Profile)
|   |   |   |-- speaking_practice_screen.dart  # Pronunciation recording and scoring
|   |   |   |-- lesson_detail_screen.dart      # Individual lesson view
|   |   |   |-- vocabulary_screen.dart         # Vocabulary practice
|   |   |   +-- listening_screen.dart          # Listening comprehension
|   |   |-- services/
|   |   |   |-- api_service.dart         # HTTP API client
|   |   |   +-- auth_service.dart        # Token and session management
|   |   |-- widgets/
|   |   |   |-- custom_button.dart       # Reusable button component
|   |   |   +-- custom_text_field.dart   # Reusable text input component
|   |   +-- utils/
|   |       |-- app_constants.dart       # Colors, URLs, constants
|   |       +-- app_theme.dart           # Material 3 theme configuration
|   +-- pubspec.yaml                     # Dart/Flutter dependencies
|
|-- backend/                             # Node.js API server
|   |-- server.js                        # Express server (routes, middleware, DB)
|   |-- package.json                     # Node.js dependencies
|   |-- database.sql                     # SQL schema and seed data
|   |-- MYSQL_SETUP.md                   # Database setup instructions
|   +-- admin-panel/                     # React admin web application
|       |-- src/
|       |   |-- main.jsx                 # React entry point
|       |   |-- App.jsx                  # Router and auth guard
|       |   |-- components/
|       |   |   +-- Layout.jsx           # Sidebar navigation shell
|       |   |-- pages/
|       |   |   |-- LoginPage.jsx        # Admin login
|       |   |   |-- DashboardPage.jsx    # Statistics overview
|       |   |   |-- LessonsPage.jsx      # Lesson list management
|       |   |   |-- LessonFormPage.jsx   # Create/edit lesson form
|       |   |   +-- UsersPage.jsx        # User management
|       |   +-- services/
|       |       +-- api.js               # Admin API client
|       |-- package.json
|       +-- vite.config.js
|
+-- ai_model/                            # Python AI/ML server
    |-- inference_server.py              # FastAPI scoring endpoint
    |-- train_pronunciation_model_kaggle.py   # Kaggle training script
    |-- train_phone_level_model.py       # Phone-level training v1
    |-- train_phone_level_v2.py          # Phone-level training v2
    |-- requirements.txt                 # Python dependencies
    +-- README.md                        # AI model documentation
```

## Prerequisites

- Flutter SDK 3.9.2 or later
- Node.js 16.0.0 or later
- MySQL 8.0 or later
- Python 3.9 or later (for the AI server)
- Android Studio or Xcode (for mobile development)
- A trained model checkpoint (`best_model.pt`) for pronunciation scoring

## Installation

### 1. Database

```bash
cd backend
mysql -u root -p < database.sql
```

Refer to `backend/MYSQL_SETUP.md` for detailed setup instructions.

### 2. Backend API

```bash
cd backend
npm install
```

Create a `.env` file in the `backend/` directory:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=speakwai_db
DB_PORT=3306
JWT_SECRET=your_jwt_secret
AI_SERVER_URL=http://localhost:8000
```

Start the server:

```bash
npm run dev      # development mode with nodemon
npm start        # production mode
```

The server runs on port 3000. On first start, a default admin account is created automatically (`admin@speakwai.com` / `admin123`).

### 3. Admin Panel

```bash
cd backend/admin-panel
npm install
npm run dev
```

The admin panel runs on port 5173. Log in with the default admin credentials.

### 4. AI Inference Server

```bash
cd ai_model
pip install -r requirements.txt
```

Place the trained model file (`best_model.pt`) in the `ai_model/` directory, then start the server:

```bash
python inference_server.py
```

The AI server runs on port 8000. Refer to `ai_model/README.md` and `ai_model/SETUP_LOCAL.md` for training and deployment details.

### 5. Flutter Mobile App

```bash
cd speak_w_ai
flutter pub get
```

Update the API base URL in `lib/utils/app_constants.dart`:

```dart
static const String baseUrl = 'http://10.0.2.2:3000/api';   // Android emulator
// static const String baseUrl = 'http://localhost:3000/api'; // iOS simulator
// static const String baseUrl = 'http://YOUR_IP:3000/api';  // Physical device
```

Run the app:

```bash
flutter run
```

## Configuration

| Variable          | Location                              | Description                          |
|-------------------|---------------------------------------|--------------------------------------|
| `DB_HOST`         | `backend/.env`                        | MySQL host address                   |
| `DB_USER`         | `backend/.env`                        | MySQL username                       |
| `DB_PASSWORD`     | `backend/.env`                        | MySQL password                       |
| `DB_NAME`         | `backend/.env`                        | Database name (default: speakwai_db) |
| `DB_PORT`         | `backend/.env`                        | MySQL port (default: 3306)           |
| `JWT_SECRET`      | `backend/.env`                        | Secret key for JWT signing           |
| `AI_SERVER_URL`   | `backend/.env`                        | Python AI server URL                 |
| `baseUrl`         | `speak_w_ai/lib/utils/app_constants.dart` | Backend API URL for the mobile app |

## API Reference

All endpoints return JSON. Protected routes require an `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint              | Auth     | Description                  |
|--------|-----------------------|----------|------------------------------|
| POST   | `/api/register`       | None     | Create a new user account    |
| POST   | `/api/login`          | None     | Authenticate and receive JWT |
| POST   | `/api/forgot-password`| None     | Request password reset       |

**POST /api/register**

```json
// Request
{ "username": "string", "email": "string", "password": "string" }

// Response (201)
{
  "message": "User registered successfully",
  "token": "jwt_token",
  "user": { "id": 1, "username": "string", "email": "string" }
}
```

**POST /api/login**

```json
// Request
{ "email": "string", "password": "string" }

// Response (200)
{
  "message": "Login successful",
  "token": "jwt_token",
  "user": { "id": 1, "username": "string", "email": "string", "role": "user" }
}
```

### Lessons

| Method | Endpoint              | Auth     | Description                  |
|--------|-----------------------|----------|------------------------------|
| GET    | `/api/lessons`        | User     | List all lessons             |
| GET    | `/api/lessons/:id`    | User     | Get a single lesson          |
| POST   | `/api/lessons`        | Admin    | Create a new lesson          |
| PUT    | `/api/lessons/:id`    | Admin    | Update an existing lesson    |
| DELETE | `/api/lessons/:id`    | Admin    | Delete a lesson              |

### User

| Method | Endpoint              | Auth     | Description                  |
|--------|-----------------------|----------|------------------------------|
| GET    | `/api/profile`        | User     | Get current user profile     |
| GET    | `/api/user/stats`     | User     | Get learning statistics      |
| POST   | `/api/user/progress`  | User     | Update daily progress        |

### AI Scoring

| Method | Endpoint              | Auth     | Description                          |
|--------|-----------------------|----------|--------------------------------------|
| GET    | `/api/ai/health`      | User     | Check AI server availability         |
| POST   | `/api/ai/score`       | User     | Score pronunciation (multipart file) |
| POST   | `/api/ai/score-base64`| User     | Score pronunciation (base64 string)  |

**POST /api/ai/score-base64**

```json
// Request
{ "audio": "base64_encoded_wav", "text": "reference sentence" }

// Response (200)
{
  "scores": {
    "accuracy": 82.5,
    "fluency": 78.3,
    "completeness": 90.0,
    "prosodic": 75.1,
    "total": 81.2
  },
  "feedback": {
    "accuracy": "Good pronunciation!",
    "fluency": "Good rhythm and flow!",
    "completeness": "Excellent! All words were spoken clearly.",
    "prosodic": "Good intonation and stress patterns!",
    "total": "Good overall performance!"
  }
}
```

### Administration

| Method | Endpoint                            | Auth  | Description                  |
|--------|-------------------------------------|-------|------------------------------|
| GET    | `/api/admin/stats`                  | Admin | Dashboard statistics         |
| GET    | `/api/admin/users`                  | Admin | List all users               |
| DELETE | `/api/admin/users/:id`              | Admin | Delete a user                |
| PUT    | `/api/admin/users/:id/status`       | Admin | Lock or unlock a user        |
| PUT    | `/api/admin/users/:id/role`         | Admin | Change user role             |
| PUT    | `/api/admin/users/:id/reset-password`| Admin | Reset user password          |
| GET    | `/api/admin/users/:id/progress`     | Admin | View user progress history   |

## AI Model

### Architecture

The pronunciation scoring model is built on top of **WavLM Base Plus** (Microsoft), a self-supervised speech representation model. The architecture includes:

1. **Weighted layer aggregation** -- learned weights across all 13 transformer layers
2. **Temporal attention pooling** -- attention mechanism over time steps to produce a fixed-size embedding
3. **Shared representation layer** -- Linear(768, 512) with LayerNorm, GELU activation, and dropout
4. **Six task-specific prediction heads**, each outputting a score between 0 and 100:
   - Accuracy (phoneme-level correctness)
   - Fluency (speech smoothness and rhythm)
   - Completeness (utterance coverage)
   - Prosody (intonation and stress patterns)
   - Total (overall pronunciation quality)
   - Phone error rate (0 to 1 scale)

### Training

- **Dataset**: [Speechocean762](https://huggingface.co/datasets/speechocean762)
- **Platform**: Kaggle (GPU T4 x2)
- **Training time**: approximately 2--4 hours
- **Output**: `best_model.pt` (approximately 350 MB)

Refer to `ai_model/README.md` for full training instructions.

### Inference Pipeline

1. The Flutter app records audio in WAV format (16 kHz, mono) and encodes it as base64.
2. The encoded audio is sent to the Node.js backend via `POST /api/ai/score-base64`.
3. The backend proxies the request to the Python FastAPI server at `POST /score-base64`.
4. The AI server decodes the audio, resamples to 16 kHz, extracts features using `Wav2Vec2FeatureExtractor`, and runs inference through the model.
5. Scores and Vietnamese-language feedback are returned through the chain back to the client.

### Feedback Thresholds

| Score Range | Feedback (Vietnamese)      | Translation        |
|-------------|----------------------------|--------------------|
| 85 -- 100   | Xuat sac!                  | Excellent          |
| 70 -- 84    | Tot!                       | Good               |
| 50 -- 69    | Kha tot                    | Fairly good        |
| 0 -- 49     | Can cai thien              | Needs improvement  |

## Database Schema

### users

| Column        | Type                            | Constraints                  |
|---------------|---------------------------------|------------------------------|
| id            | INT                             | PRIMARY KEY, AUTO_INCREMENT  |
| username      | VARCHAR(50)                     | UNIQUE, NOT NULL             |
| email         | VARCHAR(100)                    | UNIQUE, NOT NULL             |
| password_hash | VARCHAR(255)                    | NOT NULL                     |
| role          | ENUM('user', 'admin')           | DEFAULT 'user'               |
| status        | ENUM('active', 'locked')        | DEFAULT 'active'             |
| created_at    | TIMESTAMP                       | DEFAULT CURRENT_TIMESTAMP    |

### lessons

| Column           | Type                                           | Constraints                  |
|------------------|------------------------------------------------|------------------------------|
| id               | INT                                            | PRIMARY KEY, AUTO_INCREMENT  |
| title            | VARCHAR(200)                                   | NOT NULL                     |
| content          | TEXT                                           | NOT NULL                     |
| difficulty_level | ENUM('beginner', 'intermediate', 'advanced')   | DEFAULT 'beginner'           |
| created_at       | TIMESTAMP                                      | DEFAULT CURRENT_TIMESTAMP    |

Indexes on `difficulty_level` and `created_at`.

### user_progress

| Column             | Type      | Constraints                          |
|--------------------|-----------|--------------------------------------|
| id                 | INT       | PRIMARY KEY, AUTO_INCREMENT          |
| user_id            | INT       | FOREIGN KEY -> users(id) ON DELETE CASCADE |
| lessons_completed  | INT       | DEFAULT 0                            |
| vocabulary_learned | INT       | DEFAULT 0                            |
| listening_completed| INT       | DEFAULT 0                            |
| practice_days      | INT       | DEFAULT 0                            |
| created_at         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP            |

One record per user per day (upsert logic on the server side).

### Seed Data

On first server start:
- 5 sample lessons are inserted if the `lessons` table is empty.
- A default admin account (`admin@speakwai.com` / `admin123`) is created if no admin user exists.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
