"""
🎤 SpeakWAI AI Inference Server
================================
FastAPI server for pronunciation scoring using trained WavLM model.

Requirements:
    pip install fastapi uvicorn python-multipart torch transformers librosa

Run:
    python inference_server.py
    
Or with uvicorn:
    uvicorn inference_server:app --host 0.0.0.0 --port 8000
"""

import os
import io
import torch
import torch.nn as nn
import numpy as np
import librosa
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from transformers import WavLMModel, Wav2Vec2FeatureExtractor

# =============================================================================
# MODEL DEFINITION (must match training model)
# =============================================================================
class PronunciationScoringModel(nn.Module):
    """Multi-task Pronunciation Scoring Model based on WavLM."""
    
    def __init__(
        self,
        model_name: str = "microsoft/wavlm-base-plus",
        hidden_size: int = 768,
        freeze_feature_extractor: bool = True,
        freeze_encoder_layers: int = 8
    ):
        super().__init__()
        
        self.wavlm = WavLMModel.from_pretrained(model_name)
        
        # Freeze layers (not needed for inference, but keep structure)
        if freeze_feature_extractor:
            for param in self.wavlm.feature_extractor.parameters():
                param.requires_grad = False
            for param in self.wavlm.feature_projection.parameters():
                param.requires_grad = False
        
        if freeze_encoder_layers > 0:
            for i in range(freeze_encoder_layers):
                for param in self.wavlm.encoder.layers[i].parameters():
                    param.requires_grad = False
        
        # Weighted layer aggregation
        num_layers = len(self.wavlm.encoder.layers) + 1
        self.layer_weights = nn.Parameter(torch.ones(num_layers) / num_layers)
        
        # Temporal attention pooling
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.Tanh(),
            nn.Linear(256, 1)
        )
        
        # Shared representation layer
        self.shared_layer = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(0.1)
        )
        
        # Task-specific prediction heads
        self.heads = nn.ModuleDict({
            'accuracy': self._make_head(512, 1),
            'fluency': self._make_head(512, 1),
            'completeness': self._make_head(512, 1),
            'prosodic': self._make_head(512, 1),
            'total': self._make_head(512, 1),
            'phone_error': self._make_head(512, 1)
        })
    
    def _make_head(self, input_dim: int, output_dim: int) -> nn.Module:
        return nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, output_dim),
            nn.Sigmoid()
        )
    
    def forward(self, input_values: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        outputs = self.wavlm(
            input_values,
            attention_mask=attention_mask,
            output_hidden_states=True,
            return_dict=True
        )
        
        hidden_states = outputs.hidden_states
        
        # Weighted aggregation
        weights = torch.softmax(self.layer_weights, dim=0)
        weighted_hidden = sum(w * h for w, h in zip(weights, hidden_states))
        
        # Attention pooling
        attn_weights = torch.softmax(self.attention(weighted_hidden).squeeze(-1), dim=-1)
        pooled = (weighted_hidden * attn_weights.unsqueeze(-1)).sum(dim=1)
        
        # Shared layer
        shared = self.shared_layer(pooled)
        
        # Predictions
        predictions = {task: head(shared).squeeze(-1) for task, head in self.heads.items()}
        
        return predictions


# =============================================================================
# SCORER CLASS
# =============================================================================
class PronunciationScorer:
    """Pronunciation scoring inference."""
    
    def __init__(self, model_path: str, device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        print(f"🖥️ Using device: {self.device}")
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        config_dict = checkpoint['config']
        
        # Load feature extractor
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(config_dict['model_name'])
        self.sample_rate = config_dict['sample_rate']
        self.max_audio_length = config_dict['max_audio_length']
        
        # Load model
        self.model = PronunciationScoringModel(
            model_name=config_dict['model_name'],
            hidden_size=config_dict['hidden_size']
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print("✅ Model loaded successfully!")
    
    @torch.no_grad()
    def score(self, audio_data: np.ndarray, sr: int = 16000) -> Dict[str, float]:
        """Score pronunciation from audio array."""
        
        # Resample if needed
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
        
        # Truncate if too long
        max_samples = self.max_audio_length * self.sample_rate
        if len(audio_data) > max_samples:
            audio_data = audio_data[:max_samples]
        
        # Process
        inputs = self.processor(
            audio_data,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        )
        input_values = inputs.input_values.to(self.device)
        attention_mask = torch.ones_like(input_values)
        
        # Predict
        predictions = self.model(input_values, attention_mask)
        
        # Return scores (0-100 scale)
        return {
            'accuracy': round(float(predictions['accuracy'].item() * 100), 1),
            'fluency': round(float(predictions['fluency'].item() * 100), 1),
            'completeness': round(float(predictions['completeness'].item() * 100), 1),
            'prosodic': round(float(predictions['prosodic'].item() * 100), 1),
            'total': round(float(predictions['total'].item() * 100), 1),
            'error_rate': round(float(predictions['phone_error'].item()), 3)
        }
    
    def score_file(self, audio_path: str) -> Dict[str, float]:
        """Score pronunciation from audio file."""
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        return self.score(audio, sr)


# =============================================================================
# FASTAPI SERVER
# =============================================================================
app = FastAPI(
    title="SpeakWAI AI Server",
    description="Pronunciation scoring API using WavLM model",
    version="1.0.0"
)

# CORS - allow requests from Flutter app and Node.js backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scorer
scorer: Optional[PronunciationScorer] = None

# Response models
class ScoringResponse(BaseModel):
    success: bool
    scores: Dict[str, float]
    feedback: Dict[str, str]
    text: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str


def generate_feedback(scores: Dict[str, float]) -> Dict[str, str]:
    """Generate text feedback based on scores."""
    feedback = {}
    
    # Accuracy feedback
    acc = scores['accuracy']
    if acc >= 85:
        feedback['accuracy'] = "Xuất sắc! Phát âm rất chuẩn xác."
    elif acc >= 70:
        feedback['accuracy'] = "Tốt! Phát âm khá chuẩn, còn một số lỗi nhỏ."
    elif acc >= 50:
        feedback['accuracy'] = "Khá tốt. Cần luyện tập thêm một số âm."
    else:
        feedback['accuracy'] = "Cần cải thiện. Hãy nghe và lặp lại nhiều hơn."
    
    # Fluency feedback
    flu = scores['fluency']
    if flu >= 85:
        feedback['fluency'] = "Nói rất lưu loát và tự nhiên!"
    elif flu >= 70:
        feedback['fluency'] = "Khá lưu loát, ít ngập ngừng."
    elif flu >= 50:
        feedback['fluency'] = "Cần nói trôi chảy hơn, giảm ngập ngừng."
    else:
        feedback['fluency'] = "Hãy luyện nói chậm rãi và đều hơn."
    
    # Prosody feedback
    pro = scores['prosodic']
    if pro >= 85:
        feedback['prosodic'] = "Ngữ điệu tuyệt vời, như người bản xứ!"
    elif pro >= 70:
        feedback['prosodic'] = "Ngữ điệu tốt, cần chú ý thêm trọng âm."
    elif pro >= 50:
        feedback['prosodic'] = "Cần cải thiện ngữ điệu và nhịp điệu."
    else:
        feedback['prosodic'] = "Hãy nghe nhiều và bắt chước ngữ điệu."
    
    # Overall feedback
    total = scores['total']
    if total >= 85:
        feedback['overall'] = "🌟 Tuyệt vời! Bạn nói rất tốt!"
    elif total >= 70:
        feedback['overall'] = "👍 Tốt lắm! Tiếp tục phát huy!"
    elif total >= 50:
        feedback['overall'] = "💪 Khá tốt! Cần luyện tập thêm."
    else:
        feedback['overall'] = "📚 Hãy kiên trì luyện tập nhé!"
    
    return feedback


@app.on_event("startup")
async def load_model():
    """Load model on server startup."""
    global scorer
    
    # Find model file
    model_paths = [
        "./best_model.pt",
        "./models/best_model.pt",
        "../models/best_model.pt",
        os.path.join(os.path.dirname(__file__), "best_model.pt"),
    ]
    
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if model_path:
        print(f"📂 Loading model from: {model_path}")
        scorer = PronunciationScorer(model_path, device='cuda')
    else:
        print("⚠️ Model not found! Please place best_model.pt in the server directory.")
        print(f"   Searched paths: {model_paths}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check server health and model status."""
    return HealthResponse(
        status="ok",
        model_loaded=scorer is not None,
        device=str(scorer.device) if scorer else "none"
    )


@app.post("/score", response_model=ScoringResponse)
async def score_pronunciation(
    audio: UploadFile = File(...),
    text: Optional[str] = Form(None)
):
    """
    Score pronunciation from uploaded audio file.
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        text: Optional expected text for reference
    
    Returns:
        Pronunciation scores and feedback
    """
    if scorer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Read audio file
        content = await audio.read()
        audio_data, sr = librosa.load(io.BytesIO(content), sr=16000)
        
        # Check audio length
        if len(audio_data) < 1600:  # Less than 0.1 seconds
            raise HTTPException(status_code=400, detail="Audio too short")
        
        # Score
        scores = scorer.score(audio_data, sr)
        feedback = generate_feedback(scores)
        
        return ScoringResponse(
            success=True,
            scores=scores,
            feedback=feedback,
            text=text
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@app.post("/score-base64")
async def score_pronunciation_base64(data: Dict[str, Any]):
    """
    Score pronunciation from base64-encoded audio.
    
    Args:
        data: {"audio": "base64_string", "text": "optional text"}
    
    Returns:
        Pronunciation scores and feedback
    """
    import base64
    
    if scorer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Decode base64 audio
        audio_b64 = data.get('audio', '')
        if not audio_b64:
            raise HTTPException(status_code=400, detail="No audio data")
        
        audio_bytes = base64.b64decode(audio_b64)
        audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        
        # Check audio length
        if len(audio_data) < 1600:
            raise HTTPException(status_code=400, detail="Audio too short")
        
        # Score
        scores = scorer.score(audio_data, sr)
        feedback = generate_feedback(scores)
        text = data.get('text')
        
        return {
            "success": True,
            "scores": scores,
            "feedback": feedback,
            "text": text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎤 SpeakWAI AI Inference Server")
    print("=" * 60)
    print()
    print("📋 Endpoints:")
    print("   GET  /health     - Check server status")
    print("   POST /score      - Score audio file upload")
    print("   POST /score-base64 - Score base64-encoded audio")
    print()
    print("🚀 Starting server on http://0.0.0.0:8000")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
