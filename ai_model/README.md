# 🎤 SpeakWAI - Pronunciation Scoring AI Model

## Tổng Quan

Model AI để chấm điểm phát âm tiếng Anh cho người Việt học ngoại ngữ.

### Kiến Trúc
- **Backbone**: WavLM Base Plus (Microsoft)
- **Dataset**: Speechocean762
- **Tasks**: Multi-task learning cho 5 metrics

### Output Scores (0-100)
| Metric | Mô tả |
|--------|-------|
| **Accuracy** | Độ chính xác phát âm từng âm |
| **Fluency** | Độ trôi chảy, tự nhiên |
| **Completeness** | Độ đầy đủ của câu |
| **Prosody** | Ngữ điệu, nhịp điệu |
| **Total** | Điểm tổng hợp |

---

## 🚀 Hướng Dẫn Training trên Kaggle

### Bước 1: Tạo Notebook Mới
1. Vào [kaggle.com/code](https://kaggle.com/code)
2. Click **"New Notebook"**
3. Đổi tên thành "SpeakWAI Pronunciation Model"

### Bước 2: Enable GPU
1. Click vào **Settings** (icon bánh răng)
2. Chọn **Accelerator** → **GPU T4 x2**
3. Turn on **Internet**

### Bước 3: Thêm Dataset
1. Click **"Add Data"**
2. Tìm kiếm **"speechocean762"**
3. Add dataset vào notebook

### Bước 4: Upload Code
Copy toàn bộ nội dung từ `train_pronunciation_model_kaggle.py` vào notebook.

### Bước 5: Cập Nhật Data Path
```python
# Tìm dòng này trong config
data_dir: str = "/kaggle/input/speechocean762"

# Update theo path thực tế của dataset trên Kaggle
# Click vào dataset bên phải để xem path chính xác
```

### Bước 6: Chạy Training
- Run All cells
- Training time: ~2-4 giờ với GPU T4

### Bước 7: Download Model
Sau khi train xong, download file từ:
```
/kaggle/working/pronunciation_model/best_model.pt
```

---

## 📦 Deploy Model lên Server

### Requirements
```bash
pip install torch torchaudio transformers librosa
pip install fastapi uvicorn python-multipart
```

### Chạy Server
```bash
# Set đường dẫn model
export MODEL_PATH=/path/to/best_model.pt

# Chạy server
python inference_server.py
```

Server sẽ chạy ở `http://localhost:8000`

### API Endpoints

#### 1. Score từ Audio File
```bash
curl -X POST "http://localhost:8000/api/score-pronunciation" \
     -F "audio=@recording.wav"
```

#### 2. Score từ Base64
```bash
curl -X POST "http://localhost:8000/api/score-pronunciation-base64" \
     -F "audio_base64=<base64_string>"
```

#### Response Format
```json
{
    "success": true,
    "scores": {
        "accuracy": 78.5,
        "fluency": 82.3,
        "completeness": 90.1,
        "prosody": 75.2,
        "total": 81.5,
        "error_rate": 0.12,
        "feedback": {
            "accuracy": "Phát âm khá tốt...",
            "fluency": "Nói rất trôi chảy...",
            "prosody": "Ngữ điệu khá ổn...",
            "overall": "Tốt! Tiếp tục..."
        }
    }
}
```

---

## 🔗 Tích Hợp với Flutter App

### Option 1: Qua Node.js Backend (Recommended)

Thêm vào `backend/routes/api.js`:

```javascript
const axios = require('axios');
const FormData = require('form-data');
const multer = require('multer');

const upload = multer({ storage: multer.memoryStorage() });

router.post('/score-pronunciation', 
    authMiddleware, 
    upload.single('audio'), 
    async (req, res) => {
        try {
            const form = new FormData();
            form.append('audio', req.file.buffer, {
                filename: 'audio.wav',
                contentType: req.file.mimetype
            });
            
            // Call Python AI server
            const response = await axios.post(
                process.env.AI_SERVER_URL + '/api/score-pronunciation',
                form,
                { headers: form.getHeaders() }
            );
            
            // Save score to database
            await db.query(
                `INSERT INTO pronunciation_scores 
                 (user_id, accuracy, fluency, completeness, prosody, total_score)
                 VALUES (?, ?, ?, ?, ?, ?)`,
                [
                    req.user.id,
                    response.data.scores.accuracy,
                    response.data.scores.fluency,
                    response.data.scores.completeness,
                    response.data.scores.prosody,
                    response.data.scores.total
                ]
            );
            
            res.json(response.data);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }
);
```

### Option 2: Direct từ Flutter

```dart
// lib/services/pronunciation_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class PronunciationService {
  static const String aiServerUrl = 'http://your-ai-server:8000';
  
  static Future<Map<String, dynamic>> scorePronunciation(String audioPath) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$aiServerUrl/api/score-pronunciation'),
    );
    
    request.files.add(
      await http.MultipartFile.fromPath('audio', audioPath),
    );
    
    var response = await request.send();
    var responseBody = await response.stream.bytesToString();
    return json.decode(responseBody);
  }
}
```

---

## 📊 Kết Quả Mong Đợi

Sau training với Speechocean762, model nên đạt:

| Metric | Pearson Correlation | MSE |
|--------|---------------------|-----|
| Accuracy | ~0.70-0.75 | <0.02 |
| Fluency | ~0.65-0.70 | <0.02 |
| Prosody | ~0.60-0.65 | <0.03 |
| Total | ~0.75-0.80 | <0.015 |

---

## 🔧 Tips Cải Thiện

### 1. Tăng Dữ Liệu
- Augment với noise, speed changes
- Thu thập thêm data từ người Việt

### 2. Điều Chỉnh Hyperparameters
```python
# Thử các learning rate khác nhau
learning_rate: float = 5e-5  # hoặc 1e-5

# Tăng epochs nếu model vẫn đang improve
num_epochs: int = 50

# Unfreeze thêm layers
freeze_encoder_layers: int = 4  # thay vì 8
```

### 3. Sử Dụng Model Lớn Hơn
```python
model_name: str = "microsoft/wavlm-large"  # 316M params
hidden_size: int = 1024
```

---

## 📁 Cấu Trúc Files

```
ai_model/
├── train_pronunciation_model_kaggle.py  # Training script cho Kaggle
├── inference_server.py                   # FastAPI server
├── README.md                             # Hướng dẫn này
└── models/                               # Folder chứa trained models
    └── best_model.pt                     # Model sau khi train
```

---

## ❓ FAQ

**Q: Cần GPU gì để training?**
A: GPU T4 (free trên Kaggle) là đủ. Training ~2-4 giờ.

**Q: Model size sau training?**
A: ~350MB (WavLM Base Plus + heads)

**Q: Có thể chạy inference trên CPU?**
A: Có, nhưng chậm hơn (~1-2s/sample thay vì ~100ms)

**Q: Làm sao để improve accuracy?**
A: Thu thập thêm data người Việt, fine-tune thêm epochs, hoặc dùng WavLM Large.
