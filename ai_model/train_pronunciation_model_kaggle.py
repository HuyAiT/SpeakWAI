"""
===================================================================================
🎤 PRONUNCIATION SCORING MODEL - FINE-TUNING WAVLM WITH SPEECHOCEAN762
===================================================================================
Designed for Vietnamese learners of English pronunciation assessment.

Model Architecture:
- Backbone: WavLM Base Plus (Microsoft's pre-trained speech model)
- Task Heads: Multi-task learning for:
  * Accuracy (pronunciation accuracy)
  * Fluency (how smooth the speech is)
  * Completeness (how complete the utterance is)
  * Prosody (intonation, stress, rhythm)
  * Total Score (overall pronunciation quality)
  * Phone-level Error Detection (specific phoneme mistakes)

Dataset: Speechocean762
- 5000 English utterances by 250 non-native speakers
- Annotations at utterance, word, and phone levels
- Scores range from 0-10 for various metrics

Usage on Kaggle:
1. Enable GPU (T4/P100 recommended)
2. Add Speechocean762 dataset
3. Run all cells

Author: SpeakWAI Team
===================================================================================
"""

# ===================================================================================
# SECTION 1: SETUP & INSTALLATION
# ===================================================================================
print("📦 Installing required packages...")

# Uncomment these lines when running on Kaggle
# !pip install -q transformers datasets librosa soundfile torchaudio
# !pip install -q accelerate evaluate jiwer
# !pip install -q tensorboard matplotlib seaborn

import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

import numpy as np
import pandas as pd
import librosa
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

# Transformers
from transformers import (
    Wav2Vec2FeatureExtractor,
    WavLMModel,
    get_linear_schedule_with_warmup
)

# For metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr, spearmanr

# Set device and detect multi-GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
n_gpu = torch.cuda.device_count()
print(f"🖥️ Using device: {device}")
if n_gpu > 1:
    print(f"🚀 Multi-GPU detected! Using {n_gpu} GPUs with DataParallel")

# ===================================================================================
# SECTION 2: CONFIGURATION
# ===================================================================================
@dataclass
class TrainingConfig:
    """Training configuration for the pronunciation model."""
    
    # Model
    model_name: str = "microsoft/wavlm-base-plus"
    hidden_size: int = 768  # WavLM Base Plus hidden size
    
    # Training
    num_epochs: int = 10  # Reduced for faster training
    batch_size: int = 8  # Per GPU batch size, will be multiplied by n_gpu
    gradient_accumulation_steps: int = 4
    learning_rate: float = 1e-4
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Audio
    sample_rate: int = 16000
    max_audio_length: int = 16  # seconds
    
    # Task weights for multi-task learning
    loss_weights: Dict[str, float] = None
    
    # Paths (Update these for your Kaggle environment)
    data_dir: str = "/kaggle/input/speechocean762"  # Kaggle dataset path
    output_dir: str = "/kaggle/working/pronunciation_model"
    
    # Features
    freeze_feature_extractor: bool = True
    freeze_encoder_layers: int = 8  # Freeze first N transformer layers
    
    # Seed
    seed: int = 42
    
    def __post_init__(self):
        if self.loss_weights is None:
            self.loss_weights = {
                'accuracy': 1.0,
                'fluency': 1.0,
                'completeness': 0.8,
                'prosodic': 0.8,  # Note: field is 'prosodic' in dataset
                'total': 1.5,
                'phone_error': 0.5
            }

config = TrainingConfig()

# Set seed for reproducibility
def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    import random
    random.seed(seed)
    torch.backends.cudnn.deterministic = True

set_seed(config.seed)

# ===================================================================================
# SECTION 3: DATASET PREPARATION
# ===================================================================================
class Speechocean762Dataset(Dataset):
    """
    Dataset class for Speechocean762.
    
    Kaggle structure:
    speechocean762/
    └── speechocean762/
        ├── WAVE/           (audio files: 000001.wav, 000002.wav, ...)
        ├── resource/
        │   ├── scores.json         (utterance-level scores)
        │   ├── scores-detail.json  (word & phone level scores)
        │   ├── text                (transcriptions)
        │   └── ...
        ├── train/
        │   └── wav.scp     (list of training utterance IDs)
        └── test/
            └── wav.scp     (list of test utterance IDs)
    
    Scores include:
    - accuracy: How well the phonemes are pronounced (0-10)
    - fluency: How smooth and natural flow is (0-10)
    - completeness: How complete the utterance is (0-10)
    - prosody: Rhythm, stress, intonation (0-10)
    - total: Overall pronunciation score (0-10)
    """
    
    def __init__(
        self,
        data_dir: str,
        split: str = 'train',
        processor: Wav2Vec2FeatureExtractor = None,
        max_audio_length: int = 16,
        sample_rate: int = 16000
    ):
        self.data_dir = Path(data_dir)
        self.split = split
        self.processor = processor
        self.max_audio_length = max_audio_length
        self.sample_rate = sample_rate
        
        # Handle nested folder structure on Kaggle
        # /kaggle/input/speechocean762/speechocean762/
        if (self.data_dir / 'speechocean762').exists():
            self.data_dir = self.data_dir / 'speechocean762'
            print(f"📁 Using nested path: {self.data_dir}")
        
        # Load annotations
        self.samples = self._load_annotations()
        print(f"📚 Loaded {len(self.samples)} samples for {split} split")
    
    def _load_annotations(self) -> List[Dict]:
        """Load and parse annotation files."""
        samples = []
        
        # 1. Load scores from resource/scores.json
        scores_file = self.data_dir / 'resource' / 'scores.json'
        detail_file = self.data_dir / 'resource' / 'scores-detail.json'
        
        scores_data = {}
        detail_data = {}
        
        if scores_file.exists():
            with open(scores_file, 'r', encoding='utf-8') as f:
                scores_data = json.load(f)
            print(f"✅ Loaded scores from {scores_file}")
        else:
            print(f"⚠️ Scores file not found: {scores_file}")
        
        if detail_file.exists():
            with open(detail_file, 'r', encoding='utf-8') as f:
                detail_data = json.load(f)
            print(f"✅ Loaded detail scores from {detail_file}")
        
        # 2. Load text transcriptions
        text_file = self.data_dir / 'resource' / 'text'
        text_data = {}
        if text_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        text_data[parts[0]] = parts[1]
        
        # 3. Build mapping from utt_id to audio file path
        # WAV files are in subfolders: WAVE/SPEAKER0001/000010011.WAV
        # Note: Files use uppercase .WAV extension!
        wav_dir = self.data_dir / 'WAVE'
        utt_to_path = {}
        
        if wav_dir.exists():
            # Scan all speaker folders for WAV files (both .wav and .WAV)
            for speaker_dir in wav_dir.iterdir():
                if speaker_dir.is_dir():
                    # Match both lowercase and uppercase extensions
                    for wav_file in list(speaker_dir.glob('*.wav')) + list(speaker_dir.glob('*.WAV')):
                        utt_id = wav_file.stem
                        utt_to_path[utt_id] = str(wav_file)
            print(f"📁 Found {len(utt_to_path)} WAV files in WAVE/*/")
        
        # 4. Get utterance IDs for this split from wav.scp
        wav_scp = self.data_dir / self.split / 'wav.scp'
        utt_ids = []
        
        if wav_scp.exists():
            with open(wav_scp, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        utt_id = parts[0]
                        # Some wav.scp formats have: utt_id /path/to/file.wav
                        if len(parts) >= 2 and parts[1].endswith('.wav'):
                            # Use the path from wav.scp if provided
                            utt_to_path[utt_id] = parts[1]
                        utt_ids.append(utt_id)
            print(f"✅ Found {len(utt_ids)} utterances in {wav_scp}")
        else:
            print(f"⚠️ wav.scp not found: {wav_scp}")
            # Use all discovered WAV files
            utt_ids = list(utt_to_path.keys())
        
        # 5. Build samples list
        found_count = 0
        missing_count = 0
        
        for utt_id in utt_ids:
            # Get audio path from our mapping
            if utt_id not in utt_to_path:
                missing_count += 1
                continue
            
            audio_path = utt_to_path[utt_id]
            found_count += 1
            
            # Get scores - handle different data formats
            if utt_id in scores_data:
                score_info = scores_data[utt_id]
                # scores.json might have different structure
                if isinstance(score_info, dict):
                    accuracy = score_info.get('accuracy', 5)
                    fluency = score_info.get('fluency', 5)
                    completeness = score_info.get('completeness', 5)
                    prosodic = score_info.get('prosodic', 5)  # Note: field is 'prosodic' not 'prosody'
                    total = score_info.get('total', 5)
                else:
                    # If it's just a number (total score only)
                    total = float(score_info) if score_info else 5
                    accuracy = fluency = completeness = prosodic = total
            else:
                accuracy = fluency = completeness = prosodic = total = 5
            
            # Get phone-level details
            phones = []
            if utt_id in detail_data:
                detail_info = detail_data[utt_id]
                phones = self._extract_phones(detail_info)
            
            sample = {
                'id': utt_id,
                'audio_path': audio_path,
                'text': text_data.get(utt_id, ''),
                'accuracy': accuracy / 10.0,  # Normalize to 0-1
                'fluency': fluency / 10.0,
                'completeness': completeness / 10.0,
                'prosodic': prosodic / 10.0,
                'total': total / 10.0,
                'phones': phones
            }
            samples.append(sample)
        
        return samples
    
    def _extract_phones(self, detail_info) -> List[Dict]:
        """Extract phone-level annotations from detail data."""
        phones = []
        
        # Handle different possible structures of scores-detail.json
        if isinstance(detail_info, dict):
            words = detail_info.get('words', [])
            if isinstance(words, list):
                for word in words:
                    if isinstance(word, dict):
                        for phone in word.get('phones', []):
                            if isinstance(phone, dict):
                                phones.append({
                                    'phone': phone.get('phone', ''),
                                    'accuracy': phone.get('accuracy', 5) / 10.0,
                                    'stress': phone.get('stress', 0),
                                    'error_type': phone.get('error_type', 'none')
                                })
        
        return phones
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict:
        sample = self.samples[idx]
        
        # Load and process audio
        audio, sr = librosa.load(
            sample['audio_path'],
            sr=self.sample_rate
        )
        
        # Truncate or pad audio
        max_samples = self.max_audio_length * self.sample_rate
        original_length = len(audio)
        
        if len(audio) > max_samples:
            audio = audio[:max_samples]
            original_length = max_samples
        
        # Process through Wav2Vec2FeatureExtractor
        if self.processor:
            inputs = self.processor(
                audio,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding="max_length",
                max_length=max_samples,
                truncation=True
            )
            input_values = inputs.input_values.squeeze(0)
            # Create attention mask manually (1 for real audio, 0 for padding)
            attention_mask = torch.zeros(max_samples)
            attention_mask[:original_length] = 1.0
        else:
            # Pad audio to max_samples
            if len(audio) < max_samples:
                audio = np.pad(audio, (0, max_samples - len(audio)), mode='constant')
            input_values = torch.tensor(audio, dtype=torch.float32)
            attention_mask = torch.zeros(max_samples)
            attention_mask[:original_length] = 1.0
        
        # Create phone error labels (simplified: average phone accuracy)
        phone_errors = [1.0 - p['accuracy'] for p in sample['phones']] if sample['phones'] else [0.0]
        avg_phone_error = np.mean(phone_errors)
        
        return {
            'input_values': input_values,
            'attention_mask': attention_mask,
            'accuracy': torch.tensor(sample['accuracy'], dtype=torch.float),
            'fluency': torch.tensor(sample['fluency'], dtype=torch.float),
            'completeness': torch.tensor(sample['completeness'], dtype=torch.float),
            'prosodic': torch.tensor(sample['prosodic'], dtype=torch.float),
            'total': torch.tensor(sample['total'], dtype=torch.float),
            'phone_error': torch.tensor(avg_phone_error, dtype=torch.float),
            'text': sample['text'],
            'id': sample['id']
        }


def collate_fn(batch: List[Dict]) -> Dict:
    """Custom collate function for DataLoader."""
    
    # Find max length in this batch
    max_len = max(item['input_values'].shape[0] for item in batch)
    
    # Pad sequences
    input_values = []
    attention_masks = []
    
    for item in batch:
        pad_len = max_len - item['input_values'].shape[0]
        if pad_len > 0:
            input_values.append(
                F.pad(item['input_values'], (0, pad_len), value=0)
            )
            attention_masks.append(
                F.pad(item['attention_mask'], (0, pad_len), value=0)
            )
        else:
            input_values.append(item['input_values'])
            attention_masks.append(item['attention_mask'])
    
    return {
        'input_values': torch.stack(input_values),
        'attention_mask': torch.stack(attention_masks),
        'accuracy': torch.stack([item['accuracy'] for item in batch]),
        'fluency': torch.stack([item['fluency'] for item in batch]),
        'completeness': torch.stack([item['completeness'] for item in batch]),
        'prosodic': torch.stack([item['prosodic'] for item in batch]),
        'total': torch.stack([item['total'] for item in batch]),
        'phone_error': torch.stack([item['phone_error'] for item in batch]),
        'text': [item['text'] for item in batch],
        'id': [item['id'] for item in batch]
    }


# ===================================================================================
# SECTION 4: MODEL ARCHITECTURE
# ===================================================================================
class PronunciationScoringModel(nn.Module):
    """
    Multi-task Pronunciation Scoring Model based on WavLM.
    
    Architecture:
    ┌─────────────────────────────────────────┐
    │           Raw Audio Waveform             │
    └─────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │    WavLM Base Plus (Feature Extractor)   │
    │         (Frozen/Partially Frozen)        │
    └─────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │      Weighted Layer Aggregation          │
    │   (Learn optimal layer combination)      │
    └─────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │      Temporal Attention Pooling          │
    │    (Attend to important time steps)      │
    └─────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼           ▼           ▼
    ┌───────────┐ ┌───────────┐ ┌───────────┐
    │  Accuracy │ │  Fluency  │ │  Prosody  │ ...
    │    Head   │ │   Head    │ │   Head    │
    └───────────┘ └───────────┘ └───────────┘
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/wavlm-base-plus",
        hidden_size: int = 768,
        freeze_feature_extractor: bool = True,
        freeze_encoder_layers: int = 8
    ):
        super().__init__()
        
        # Load pre-trained WavLM
        self.wavlm = WavLMModel.from_pretrained(model_name)
        
        # Freeze feature extractor
        if freeze_feature_extractor:
            for param in self.wavlm.feature_extractor.parameters():
                param.requires_grad = False
            for param in self.wavlm.feature_projection.parameters():
                param.requires_grad = False
        
        # Freeze first N encoder layers
        if freeze_encoder_layers > 0:
            for i in range(freeze_encoder_layers):
                for param in self.wavlm.encoder.layers[i].parameters():
                    param.requires_grad = False
        
        # Weighted layer aggregation
        num_layers = len(self.wavlm.encoder.layers) + 1  # +1 for embedding layer
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
            'prosodic': self._make_head(512, 1),  # Note: 'prosodic' not 'prosody'
            'total': self._make_head(512, 1),
            'phone_error': self._make_head(512, 1)  # Predicts average phone error rate
        })
    
    def _make_head(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create a prediction head."""
        return nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, output_dim),
            nn.Sigmoid()  # Output in [0, 1]
        )
    
    def forward(
        self,
        input_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            input_values: Raw audio waveform [batch, time]
            attention_mask: Attention mask [batch, time]
        
        Returns:
            Dictionary of predictions for each task
        """
        # Get all hidden states from WavLM
        outputs = self.wavlm(
            input_values,
            attention_mask=attention_mask,
            output_hidden_states=True,
            return_dict=True
        )
        
        # Weighted layer aggregation
        all_hidden_states = outputs.hidden_states  # Tuple of [batch, seq, hidden]
        stacked_hidden = torch.stack(all_hidden_states, dim=0)  # [num_layers, batch, seq, hidden]
        
        # Normalize weights with softmax
        weights = F.softmax(self.layer_weights, dim=0)
        weights = weights.view(-1, 1, 1, 1)
        
        # Weighted sum
        weighted_hidden = (stacked_hidden * weights).sum(dim=0)  # [batch, seq, hidden]
        
        # Temporal attention pooling
        if attention_mask is not None:
            # Create mask for pooling (account for WavLM's downsampling)
            output_lengths = self.wavlm._get_feat_extract_output_lengths(
                attention_mask.sum(dim=-1).long()
            )
            max_len = weighted_hidden.shape[1]
            pool_mask = torch.arange(max_len, device=weighted_hidden.device)
            pool_mask = pool_mask.unsqueeze(0) < output_lengths.unsqueeze(1)
        else:
            pool_mask = torch.ones(
                weighted_hidden.shape[:2],
                dtype=torch.bool,
                device=weighted_hidden.device
            )
        
        # Compute attention weights
        attn_scores = self.attention(weighted_hidden).squeeze(-1)  # [batch, seq]
        attn_scores = attn_scores.masked_fill(~pool_mask, float('-inf'))
        attn_weights = F.softmax(attn_scores, dim=-1)
        
        # Weighted sum for sentence-level representation
        sentence_repr = (weighted_hidden * attn_weights.unsqueeze(-1)).sum(dim=1)  # [batch, hidden]
        
        # Shared layer
        shared_repr = self.shared_layer(sentence_repr)
        
        # Task-specific predictions
        predictions = {}
        for task, head in self.heads.items():
            predictions[task] = head(shared_repr).squeeze(-1)
        
        return predictions


# ===================================================================================
# SECTION 5: TRAINING UTILITIES
# ===================================================================================
class PronunciationLoss(nn.Module):
    """Combined loss for multi-task pronunciation scoring."""
    
    def __init__(self, weights: Dict[str, float]):
        super().__init__()
        self.weights = weights
        self.mse = nn.MSELoss()
    
    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Compute weighted multi-task loss.
        
        Returns:
            total_loss: Weighted sum of all task losses
            task_losses: Dictionary of individual task losses
        """
        task_losses = {}
        total_loss = 0.0
        
        for task in predictions.keys():
            if task in targets:
                loss = self.mse(predictions[task], targets[task])
                task_losses[task] = loss
                total_loss += self.weights.get(task, 1.0) * loss
        
        return total_loss, task_losses


def compute_metrics(
    predictions: Dict[str, np.ndarray],
    targets: Dict[str, np.ndarray]
) -> Dict[str, float]:
    """Compute evaluation metrics."""
    metrics = {}
    
    for task in predictions.keys():
        if task in targets:
            pred = predictions[task]
            tgt = targets[task]
            
            # MSE and MAE
            mse = mean_squared_error(tgt, pred)
            mae = mean_absolute_error(tgt, pred)
            
            # Correlation coefficients
            pearson_r, _ = pearsonr(tgt, pred)
            spearman_r, _ = spearmanr(tgt, pred)
            
            metrics[f'{task}_mse'] = mse
            metrics[f'{task}_mae'] = mae
            metrics[f'{task}_pearson'] = pearson_r
            metrics[f'{task}_spearman'] = spearman_r
    
    return metrics


class EarlyStopping:
    """Early stopping callback."""
    
    def __init__(self, patience: int = 5, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False
    
    def __call__(self, score: float):
        if self.best_score is None:
            self.best_score = score
        elif score < self.best_score - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.counter = 0


# ===================================================================================
# SECTION 6: TRAINING LOOP
# ===================================================================================
def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler._LRScheduler,
    criterion: nn.Module,
    config: TrainingConfig,
    device: torch.device
) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    
    total_loss = 0.0
    task_losses = {task: 0.0 for task in config.loss_weights.keys()}
    num_batches = 0
    
    progress_bar = tqdm(dataloader, desc="Training")
    
    optimizer.zero_grad()
    
    for step, batch in enumerate(progress_bar):
        # Move to device
        input_values = batch['input_values'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        targets = {
            'accuracy': batch['accuracy'].to(device),
            'fluency': batch['fluency'].to(device),
            'completeness': batch['completeness'].to(device),
            'prosodic': batch['prosodic'].to(device),
            'total': batch['total'].to(device),
            'phone_error': batch['phone_error'].to(device)
        }
        
        # Forward pass
        predictions = model(input_values, attention_mask)
        
        # Compute loss
        loss, batch_task_losses = criterion(predictions, targets)
        loss = loss / config.gradient_accumulation_steps
        
        # Backward pass
        loss.backward()
        
        # Gradient accumulation
        if (step + 1) % config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        
        # Track losses
        total_loss += loss.item() * config.gradient_accumulation_steps
        for task, task_loss in batch_task_losses.items():
            task_losses[task] += task_loss.item()
        num_batches += 1
        
        # Update progress bar
        progress_bar.set_postfix({
            'loss': total_loss / num_batches,
            'lr': scheduler.get_last_lr()[0]
        })
    
    # Average losses
    avg_losses = {'total': total_loss / num_batches}
    for task in task_losses:
        avg_losses[task] = task_losses[task] / num_batches
    
    return avg_losses


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Evaluate model on validation/test set."""
    model.eval()
    
    all_predictions = {task: [] for task in ['accuracy', 'fluency', 'completeness', 'prosodic', 'total', 'phone_error']}
    all_targets = {task: [] for task in ['accuracy', 'fluency', 'completeness', 'prosodic', 'total', 'phone_error']}
    
    total_loss = 0.0
    num_batches = 0
    
    for batch in tqdm(dataloader, desc="Evaluating"):
        input_values = batch['input_values'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        targets = {
            'accuracy': batch['accuracy'].to(device),
            'fluency': batch['fluency'].to(device),
            'completeness': batch['completeness'].to(device),
            'prosodic': batch['prosodic'].to(device),
            'total': batch['total'].to(device),
            'phone_error': batch['phone_error'].to(device)
        }
        
        # Forward pass
        predictions = model(input_values, attention_mask)
        
        # Compute loss
        loss, _ = criterion(predictions, targets)
        total_loss += loss.item()
        num_batches += 1
        
        # Collect predictions and targets
        for task in all_predictions.keys():
            all_predictions[task].extend(predictions[task].cpu().numpy())
            all_targets[task].extend(targets[task].cpu().numpy())
    
    # Convert to numpy arrays
    for task in all_predictions.keys():
        all_predictions[task] = np.array(all_predictions[task])
        all_targets[task] = np.array(all_targets[task])
    
    # Compute metrics
    metrics = compute_metrics(all_predictions, all_targets)
    metrics['loss'] = total_loss / num_batches
    
    return metrics, all_predictions


def train(config: TrainingConfig):
    """Main training function."""
    
    print("=" * 80)
    print("🚀 STARTING PRONUNCIATION MODEL TRAINING")
    print("=" * 80)
    
    # Create output directory
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Load processor
    print("\n📥 Loading Wav2Vec2 Feature Extractor...")
    processor = Wav2Vec2FeatureExtractor.from_pretrained(config.model_name)
    
    # Create datasets
    print("\n📚 Loading Datasets...")
    train_dataset = Speechocean762Dataset(
        data_dir=config.data_dir,
        split='train',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    test_dataset = Speechocean762Dataset(
        data_dir=config.data_dir,
        split='test',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    # Create dataloaders
    # Scale batch size with number of GPUs
    effective_batch_size = config.batch_size * max(1, n_gpu)
    # Note: num_workers=0 to avoid multiprocessing issues on Kaggle notebooks
    effective_num_workers = 0  # Set to 0 to avoid forked process issues
    
    print(f"\n⚙️ DataLoader config: batch_size={effective_batch_size}, num_workers={effective_num_workers}")
    
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=effective_batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=effective_num_workers,
        pin_memory=True
    )
    
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=effective_batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=effective_num_workers,
        pin_memory=True
    )
    
    # Create model
    print("\n🏗️ Building Model...")
    model = PronunciationScoringModel(
        model_name=config.model_name,
        hidden_size=config.hidden_size,
        freeze_feature_extractor=config.freeze_feature_extractor,
        freeze_encoder_layers=config.freeze_encoder_layers
    )
    model = model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"📊 Total parameters: {total_params:,}")
    print(f"📊 Trainable parameters: {trainable_params:,}")
    
    # Multi-GPU with DataParallel
    if n_gpu > 1:
        print(f"\n🚀 Wrapping model with DataParallel for {n_gpu} GPUs")
        model = nn.DataParallel(model)
        # Effective batch size = batch_size * n_gpu
        effective_batch_size = config.batch_size * n_gpu
        print(f"📊 Effective batch size: {effective_batch_size} ({config.batch_size} x {n_gpu} GPUs)")
    
    # Create optimizer and scheduler
    optimizer = AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay
    )
    
    num_training_steps = len(train_dataloader) * config.num_epochs // config.gradient_accumulation_steps
    num_warmup_steps = int(num_training_steps * config.warmup_ratio)
    
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps
    )
    
    # Create loss function
    criterion = PronunciationLoss(config.loss_weights)
    
    # Early stopping
    early_stopping = EarlyStopping(patience=5)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_metrics': []
    }
    
    best_val_loss = float('inf')
    
    # Training loop
    print("\n" + "=" * 80)
    print("🏋️ TRAINING")
    print("=" * 80)
    
    for epoch in range(config.num_epochs):
        print(f"\n📅 Epoch {epoch + 1}/{config.num_epochs}")
        print("-" * 40)
        
        # Train
        train_losses = train_epoch(
            model, train_dataloader, optimizer, scheduler, criterion, config, device
        )
        history['train_loss'].append(train_losses['total'])
        
        # Evaluate
        val_metrics, _ = evaluate(model, test_dataloader, criterion, device)
        history['val_loss'].append(val_metrics['loss'])
        history['val_metrics'].append(val_metrics)
        
        # Print metrics
        print(f"\n📈 Results:")
        print(f"   Train Loss: {train_losses['total']:.4f}")
        print(f"   Val Loss: {val_metrics['loss']:.4f}")
        print(f"\n   Validation Metrics:")
        for task in ['accuracy', 'fluency', 'completeness', 'prosodic', 'total']:
            print(f"   {task.capitalize()}:")
            print(f"      MSE: {val_metrics[f'{task}_mse']:.4f}")
            print(f"      Pearson: {val_metrics[f'{task}_pearson']:.4f}")
        
        # Save best model
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            print(f"\n💾 Saving best model (val_loss: {best_val_loss:.4f})")
            
            # Handle DataParallel: save module.state_dict() so it can be loaded on single GPU
            model_to_save = model.module if hasattr(model, 'module') else model
            
            torch.save({
                'epoch': epoch,
                'model_state_dict': model_to_save.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'val_loss': best_val_loss,
                'val_metrics': val_metrics,
                'config': config.__dict__
            }, os.path.join(config.output_dir, 'best_model.pt'))
        
        # Early stopping check
        early_stopping(val_metrics['loss'])
        if early_stopping.early_stop:
            print("\n⚠️ Early stopping triggered!")
            break
    
    # Save final model
    print("\n💾 Saving final model...")
    model_to_save = model.module if hasattr(model, 'module') else model
    torch.save({
        'epoch': epoch,
        'model_state_dict': model_to_save.state_dict(),
        'config': config.__dict__
    }, os.path.join(config.output_dir, 'final_model.pt'))
    
    # Save training history
    with open(os.path.join(config.output_dir, 'training_history.json'), 'w') as f:
        # Convert numpy types to python types for JSON serialization
        def convert(o):
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.integer):
                return int(o)
            return o
        
        history_serializable = {
            'train_loss': history['train_loss'],
            'val_loss': history['val_loss'],
            'val_metrics': [
                {k: convert(v) for k, v in m.items()}
                for m in history['val_metrics']
            ]
        }
        json.dump(history_serializable, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print(f"📁 Model saved to: {config.output_dir}")
    print("=" * 80)
    
    return model, history


# ===================================================================================
# SECTION 7: INFERENCE & EXPORT
# ===================================================================================
class PronunciationScorer:
    """
    Inference class for pronunciation scoring.
    Use this class for deploying the model on your server.
    """
    
    def __init__(self, model_path: str, device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Load checkpoint (weights_only=False for PyTorch 2.6+)
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        config_dict = checkpoint['config']
        
        # Load feature extractor (not processor - WavLM doesn't have tokenizer)
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
    
    @torch.no_grad()
    def score(self, audio_path: str) -> Dict[str, float]:
        """
        Score pronunciation from an audio file.
        
        Args:
            audio_path: Path to audio file (WAV format recommended)
        
        Returns:
            Dictionary with scores:
            - accuracy: Pronunciation accuracy (0-100)
            - fluency: Speech fluency (0-100)
            - completeness: Utterance completeness (0-100)
            - prosody: Prosodic quality (0-100)
            - total: Overall score (0-100)
            - error_rate: Estimated phoneme error rate (0-1)
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Truncate if needed
        max_samples = self.max_audio_length * self.sample_rate
        if len(audio) > max_samples:
            audio = audio[:max_samples]
        
        # Process with feature extractor
        inputs = self.processor(
            audio,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        )
        input_values = inputs.input_values.to(self.device)
        # Create attention mask manually (all ones for real audio)
        attention_mask = torch.ones_like(input_values)
        
        # Predict
        predictions = self.model(input_values, attention_mask)
        
        # Convert to scores (0-100 scale)
        scores = {
            'accuracy': float(predictions['accuracy'].item() * 100),
            'fluency': float(predictions['fluency'].item() * 100),
            'completeness': float(predictions['completeness'].item() * 100),
            'prosodic': float(predictions['prosodic'].item() * 100),
            'total': float(predictions['total'].item() * 100),
            'error_rate': float(predictions['phone_error'].item())
        }
        
        return scores
    
    @torch.no_grad()
    def score_from_array(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """Score pronunciation from numpy array."""
        # Resample if needed
        if sample_rate != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=self.sample_rate)
        
        # Truncate if needed
        max_samples = self.max_audio_length * self.sample_rate
        if len(audio) > max_samples:
            audio = audio[:max_samples]
        
        # Process
        inputs = self.processor(
            audio,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        )
        input_values = inputs.input_values.to(self.device)
        attention_mask = inputs.attention_mask.to(self.device)
        
        # Predict
        predictions = self.model(input_values, attention_mask)
        
        # Convert to scores
        scores = {
            'accuracy': float(predictions['accuracy'].item() * 100),
            'fluency': float(predictions['fluency'].item() * 100),
            'completeness': float(predictions['completeness'].item() * 100),
            'prosodic': float(predictions['prosodic'].item() * 100),
            'total': float(predictions['total'].item() * 100),
            'error_rate': float(predictions['phone_error'].item())
        }
        
        return scores


def export_for_deployment(model_path: str, output_path: str):
    """
    Export model for deployment (ONNX format for faster inference).
    """
    print("📦 Exporting model for deployment...")
    
    checkpoint = torch.load(model_path, map_location='cpu')
    config_dict = checkpoint['config']
    
    # Load model
    model = PronunciationScoringModel(
        model_name=config_dict['model_name'],
        hidden_size=config_dict['hidden_size']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, 16000 * 5)  # 5 seconds of audio
    dummy_attention = torch.ones(1, 16000 * 5)
    
    # Export to ONNX
    try:
        torch.onnx.export(
            model,
            (dummy_input, dummy_attention),
            output_path,
            input_names=['audio', 'attention_mask'],
            output_names=['accuracy', 'fluency', 'completeness', 'prosodic', 'total', 'phone_error'],
            dynamic_axes={
                'audio': {0: 'batch_size', 1: 'audio_length'},
                'attention_mask': {0: 'batch_size', 1: 'audio_length'}
            },
            opset_version=12
        )
        print(f"✅ Model exported to {output_path}")
    except Exception as e:
        print(f"❌ ONNX export failed: {e}")
        print("💡 Using PyTorch format instead for deployment")
        
        # Save in a simpler format
        torch.save({
            'model_state_dict': model.state_dict(),
            'config': config_dict
        }, output_path.replace('.onnx', '.pt'))


# ===================================================================================
# SECTION 8: VISUALIZATION & ANALYSIS
# ===================================================================================
def plot_training_history(history: Dict, save_path: str = None):
    """Plot training curves."""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Loss curves
    ax1 = axes[0, 0]
    ax1.plot(history['train_loss'], label='Train Loss', marker='o')
    ax1.plot(history['val_loss'], label='Validation Loss', marker='o')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training & Validation Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Pearson correlation for each task
    ax2 = axes[0, 1]
    tasks = ['accuracy', 'fluency', 'completeness', 'prosodic', 'total']
    for task in tasks:
        pearsons = [m[f'{task}_pearson'] for m in history['val_metrics']]
        ax2.plot(pearsons, label=task.capitalize(), marker='o')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Pearson Correlation')
    ax2.set_title('Validation Pearson Correlation by Task')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # MSE for each task
    ax3 = axes[1, 0]
    for task in tasks:
        mses = [m[f'{task}_mse'] for m in history['val_metrics']]
        ax3.plot(mses, label=task.capitalize(), marker='o')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('MSE')
    ax3.set_title('Validation MSE by Task')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Final metrics bar chart
    ax4 = axes[1, 1]
    final_metrics = history['val_metrics'][-1]
    x = np.arange(len(tasks))
    width = 0.35
    
    pearsons = [final_metrics[f'{task}_pearson'] for task in tasks]
    mses = [final_metrics[f'{task}_mse'] for task in tasks]
    
    ax4.bar(x - width/2, pearsons, width, label='Pearson', color='steelblue')
    ax4_twin = ax4.twinx()
    ax4_twin.bar(x + width/2, mses, width, label='MSE', color='indianred', alpha=0.7)
    
    ax4.set_xlabel('Task')
    ax4.set_ylabel('Pearson Correlation', color='steelblue')
    ax4_twin.set_ylabel('MSE', color='indianred')
    ax4.set_xticks(x)
    ax4.set_xticklabels([t.capitalize() for t in tasks])
    ax4.set_title('Final Validation Metrics')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Training plot saved to {save_path}")
    
    plt.show()


# ===================================================================================
# SECTION 9: MAIN EXECUTION
# ===================================================================================
if __name__ == "__main__":
    # Print configuration
    print("\n" + "=" * 80)
    print("📋 CONFIGURATION")
    print("=" * 80)
    for key, value in config.__dict__.items():
        print(f"   {key}: {value}")
    
    # Check if data exists
    if not os.path.exists(config.data_dir):
        print(f"\n⚠️ Data directory not found: {config.data_dir}")
        print("   Please update config.data_dir to point to Speechocean762 dataset")
        print("\n   Expected structure:")
        print("   ├── WAVE/")
        print("   │   ├── utt_001.wav")
        print("   │   ├── utt_002.wav")
        print("   │   └── ...")
        print("   ├── train/")
        print("   │   └── all_info.json")
        print("   └── test/")
        print("       └── all_info.json")
    else:
        # Start training
        model, history = train(config)
        
        # Plot results
        plot_training_history(
            history,
            save_path=os.path.join(config.output_dir, 'training_curves.png')
        )
        
        # Test inference
        print("\n" + "=" * 80)
        print("🧪 TESTING INFERENCE")
        print("=" * 80)
        
        scorer = PronunciationScorer(
            os.path.join(config.output_dir, 'best_model.pt'),
            device='cuda'
        )
        
        # Test with a sample - handle nested folder structure
        data_path = Path(config.data_dir)
        if (data_path / 'speechocean762').exists():
            data_path = data_path / 'speechocean762'
        
        # Find WAV files (uppercase extension on Kaggle)
        test_files = list(data_path.glob('WAVE/**/*.WAV'))[:3]
        if not test_files:
            test_files = list(data_path.glob('WAVE/**/*.wav'))[:3]
        
        for audio_file in test_files:
            scores = scorer.score(str(audio_file))
            print(f"\n📝 {audio_file.name}:")
            for metric, value in scores.items():
                if metric == 'error_rate':
                    print(f"   {metric}: {value:.2%}")
                else:
                    print(f"   {metric}: {value:.1f}/100")


# ===================================================================================
# SECTION 10: QUICK START GUIDE FOR KAGGLE
# ===================================================================================
"""
===================================================================================
🚀 QUICK START GUIDE FOR KAGGLE
===================================================================================

1. CREATE NEW KAGGLE NOTEBOOK
   - Go to kaggle.com/code
   - Click "New Notebook"
   - Enable GPU: Settings > Accelerator > GPU T4 x2

2. ADD DATASET
   - Search for "speechocean762" in Add Data
   - Or upload your own version of the dataset

3. UPDATE DATA PATH
   - Change config.data_dir to match your Kaggle dataset path
   - Usually: "/kaggle/input/speechocean762"

4. RUN THE NOTEBOOK
   - Run all cells
   - Training takes ~2-4 hours on T4 GPU

5. DOWNLOAD TRAINED MODEL
   - After training, download from:
     /kaggle/working/pronunciation_model/best_model.pt

6. DEPLOY TO YOUR SERVER
   - Copy best_model.pt to your server
   - Use PronunciationScorer class for inference
   - See Section 7 for deployment code

===================================================================================
💡 TIPS FOR BETTER RESULTS
===================================================================================

1. INCREASE DATA
   - More data = better generalization
   - Consider augmenting with noise, speed changes

2. ADJUST HYPERPARAMETERS
   - Try different learning rates: [1e-5, 5e-5, 1e-4]
   - Increase epochs if model is still improving

3. UNFREEZE MORE LAYERS
   - Set freeze_encoder_layers=4 instead of 8
   - More trainable params = better but slower

4. USE LARGER MODEL
   - Try "microsoft/wavlm-large" for better accuracy
   - Requires more GPU memory

===================================================================================
📞 INTEGRATION WITH YOUR SPEAKWAI APP
===================================================================================

After training, you'll need to:

1. Set up a Python server (Flask/FastAPI) to serve the model
2. Create an API endpoint that accepts audio files
3. Return the scoring results to your Flutter app

Example Flask endpoint:

```python
from flask import Flask, request, jsonify
from pronunciation_scorer import PronunciationScorer

app = Flask(__name__)
scorer = PronunciationScorer('best_model.pt')

@app.route('/api/score-pronunciation', methods=['POST'])
def score_pronunciation():
    audio_file = request.files['audio']
    audio_file.save('temp.wav')
    
    scores = scorer.score('temp.wav')
    
    return jsonify({
        'success': True,
        'scores': scores
    })
```

===================================================================================
"""
