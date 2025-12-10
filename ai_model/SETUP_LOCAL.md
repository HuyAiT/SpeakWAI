# 🎤 SpeakWAI AI - Setup Guide

## Yêu cầu hệ thống

- **CPU**: Ryzen 7 4800H ✅
- **GPU**: GTX 1650 Ti (4GB VRAM) ✅
- **RAM**: 8GB+ recommended
- **Python**: 3.10+
- **CUDA**: 11.8+ (for GPU acceleration)

## 📦 Cài đặt

### 1. Setup môi trường Python

```powershell
# Tạo virtual environment
cd c:\Users\Huy\projects\doanchuyennganh\SpeakWAI\ai_model
python -m venv venv

# Kích hoạt venv
.\venv\Scripts\activate

# Cài đặt PyTorch với CUDA (cho GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Cài đặt các package khác
pip install -r requirements.txt
```

### 2. Đặt model file

1. Download `best_model.pt` từ Kaggle
2. Đặt vào thư mục `ai_model/`:
   ```
   ai_model/
   ├── best_model.pt  <-- Đặt file model ở đây
   ├── inference_server.py
   └── requirements.txt
   ```

### 3. Cài đặt thêm package cho backend Node.js

```powershell
cd c:\Users\Huy\projects\doanchuyennganh\SpeakWAI\backend
npm install multer axios form-data
```

## 🚀 Chạy servers

### Terminal 1: AI Server (Python)

```powershell
cd c:\Users\Huy\projects\doanchuyennganh\SpeakWAI\ai_model
.\venv\Scripts\activate
python inference_server.py
```

Output sẽ như này:
```
============================================================
🎤 SpeakWAI AI Inference Server
============================================================

📋 Endpoints:
   GET  /health     - Check server status
   POST /score      - Score audio file upload
   POST /score-base64 - Score base64-encoded audio

📂 Loading model from: ./best_model.pt
🖥️ Using device: cuda
✅ Model loaded successfully!

🚀 Starting server on http://0.0.0.0:8000
```

### Terminal 2: Node.js Backend

```powershell
cd c:\Users\Huy\projects\doanchuyennganh\SpeakWAI\backend
node server.js
```

### Terminal 3: Flutter App (nếu cần test)

```powershell
cd c:\Users\Huy\projects\doanchuyennganh\SpeakWAI\speak_w_ai
flutter run
```

## 🧪 Test API

### Check AI Server health

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok","model_loaded":true,"device":"cuda"}
```

### Check via Node.js backend

```powershell
curl http://localhost:3000/api/ai/health
```

Expected response:
```json
{"ai_server":"connected","model_loaded":true,"device":"cuda"}
```

### Test scoring (cần file audio)

```powershell
curl -X POST http://localhost:8000/score \
  -F "audio=@test.wav" \
  -F "text=Hello, how are you"
```

## 📱 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/health` | GET | Check AI server status |
| `/api/ai/score` | POST | Score audio file (multipart/form-data) |
| `/api/ai/score-base64` | POST | Score base64-encoded audio |

### Request format cho `/api/ai/score`

```
Content-Type: multipart/form-data
Authorization: Bearer <jwt_token>

Fields:
- audio: File (audio/wav, audio/mp3, etc.)
- text: String (optional - expected text)
```

### Request format cho `/api/ai/score-base64`

```json
{
  "audio": "base64_encoded_audio_data",
  "text": "Hello, how are you" // optional
}
```

### Response format

```json
{
  "success": true,
  "user_id": 1,
  "scores": {
    "accuracy": 85.5,
    "fluency": 78.2,
    "completeness": 90.0,
    "prosodic": 72.3,
    "total": 81.5,
    "error_rate": 0.12
  },
  "feedback": {
    "accuracy": "Tốt! Phát âm khá chuẩn, còn một số lỗi nhỏ.",
    "fluency": "Khá lưu loát, ít ngập ngừng.",
    "prosodic": "Ngữ điệu tốt, cần chú ý thêm trọng âm.",
    "overall": "👍 Tốt lắm! Tiếp tục phát huy!"
  },
  "expected_text": "Hello, how are you"
}
```

## 🔧 Troubleshooting

### CUDA not available

Nếu model chạy trên CPU thay vì GPU:
1. Kiểm tra CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
2. Nếu False, cài lại PyTorch với CUDA:
   ```
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

### Model not found

Đảm bảo file `best_model.pt` nằm trong thư mục `ai_model/`

### AI server connection refused

1. Kiểm tra AI server đang chạy: `curl http://localhost:8000/health`
2. Nếu đang chạy mà vẫn lỗi, kiểm tra firewall Windows

### Audio too short

Audio cần ít nhất 0.1 giây để scoring
