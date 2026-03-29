"""
===================================================================================
🎤 PHONE-LEVEL PRONUNCIATION SCORING MODEL
===================================================================================
Fine-tuning WavLM for phone-level pronunciation assessment.

Key Features:
- Frame-level predictions (score each audio frame)
- Phone-level aggregation (average scores per phoneme)  
- Word-level and utterance-level scores
- Uses Speechocean762 phone-level annotations

Output Example:
{
    "total": 72.5,
    "words": [
        {"word": "hello", "score": 78, "phones": [
            {"phone": "HH", "score": 85},
            {"phone": "AH", "score": 62},
            {"phone": "L", "score": 78},
            {"phone": "OW", "score": 82}
        ]}
    ]
}

Author: SpeakWAI Team
===================================================================================
"""

# ===================================================================================
# SECTION 1: SETUP & INSTALLATION
# ===================================================================================
print("📦 Installing required packages...")

# Uncomment on Kaggle:
# !pip install -q transformers datasets librosa soundfile torchaudio
# !pip install -q accelerate g2p-en  # g2p-en for grapheme-to-phoneme

# Download NLTK data for g2p_en
import nltk
try:
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
    nltk.download('cmudict', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass

import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW

import numpy as np
import librosa
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

from transformers import (
    Wav2Vec2FeatureExtractor,
    WavLMModel,
    get_linear_schedule_with_warmup
)

from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr

# Set device and detect multi-GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
n_gpu = torch.cuda.device_count()
print(f"🖥️ Using device: {device}")
if n_gpu > 1:
    print(f"🚀 Multi-GPU detected! Using {n_gpu} GPUs")

# ===================================================================================
# SECTION 2: CONFIGURATION
# ===================================================================================
@dataclass
class TrainingConfig:
    """Training configuration."""
    
    # Model
    model_name: str = "microsoft/wavlm-base-plus"
    hidden_size: int = 768
    
    # Training
    num_epochs: int = 10
    batch_size: int = 4  # Smaller batch for phone-level (more memory)
    gradient_accumulation_steps: int = 8
    learning_rate: float = 5e-5  # Lower LR for fine-tuning
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Audio
    sample_rate: int = 16000
    max_audio_length: int = 10  # seconds (shorter for phone-level)
    
    # Loss weights
    utterance_weight: float = 1.0
    phone_weight: float = 2.0  # Weight phone-level higher
    
    # Paths
    data_dir: str = "/kaggle/input/speechocean762"
    output_dir: str = "/kaggle/working/phone_pronunciation_model"
    
    # Features
    freeze_feature_extractor: bool = True
    freeze_encoder_layers: int = 6  # Less frozen layers for phone-level
    
    seed: int = 42

config = TrainingConfig()

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    import random
    random.seed(seed)

set_seed(config.seed)

# ===================================================================================
# SECTION 3: PHONE SET & MAPPING
# ===================================================================================
# ARPAbet phoneme set (used by Speechocean762)
PHONE_SET = [
    'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'B', 'CH', 'D', 'DH',
    'EH', 'ER', 'EY', 'F', 'G', 'HH', 'IH', 'IY', 'JH', 'K',
    'L', 'M', 'N', 'NG', 'OW', 'OY', 'P', 'R', 'S', 'SH',
    'T', 'TH', 'UH', 'UW', 'V', 'W', 'Y', 'Z', 'ZH',
    'SIL', 'SPN'  # silence and spoken noise
]

PHONE_TO_IDX = {p: i for i, p in enumerate(PHONE_SET)}
IDX_TO_PHONE = {i: p for i, p in enumerate(PHONE_SET)}
NUM_PHONES = len(PHONE_SET)

# ===================================================================================
# SECTION 4: DATASET
# ===================================================================================
class PhoneLevelDataset(Dataset):
    """
    Dataset with phone-level annotations from Speechocean762.
    """
    
    def __init__(
        self,
        data_dir: str,
        split: str = 'train',
        processor: Wav2Vec2FeatureExtractor = None,
        max_audio_length: int = 10,
        sample_rate: int = 16000
    ):
        self.data_dir = Path(data_dir)
        self.split = split
        self.processor = processor
        self.max_audio_length = max_audio_length
        self.sample_rate = sample_rate
        self.max_samples = max_audio_length * sample_rate
        
        # Handle nested folder structure
        if (self.data_dir / 'speechocean762').exists():
            self.data_dir = self.data_dir / 'speechocean762'
        
        # Load data
        self.samples = self._load_data()
        print(f"📚 Loaded {len(self.samples)} samples for {split}")
    
    def _load_data(self) -> List[Dict]:
        samples = []
        
        # Load scores.json (has phones-accuracy array, unlike scores-detail.json)
        scores_file = self.data_dir / 'resource' / 'scores.json'
        if not scores_file.exists():
            # Try alternate paths
            scores_file = self.data_dir / 'scores.json'
        if not scores_file.exists():
            print(f"⚠️ Scores file not found")
            return samples
        
        with open(scores_file, 'r', encoding='utf-8') as f:
            scores_data = json.load(f)
        print(f"✅ Loaded {len(scores_data)} entries from scores.json")
        
        # Build WAV file mapping
        wav_dir = self.data_dir / 'WAVE'
        utt_to_path = {}
        if wav_dir.exists():
            for speaker_dir in wav_dir.iterdir():
                if speaker_dir.is_dir():
                    for wav_file in list(speaker_dir.glob('*.wav')) + list(speaker_dir.glob('*.WAV')):
                        utt_to_path[wav_file.stem] = str(wav_file)
        print(f"📁 Found {len(utt_to_path)} WAV files")
        
        # Get split utterances
        wav_scp = self.data_dir / self.split / 'wav.scp'
        if wav_scp.exists():
            with open(wav_scp, 'r') as f:
                utt_ids = [line.strip().split()[0] for line in f if line.strip()]
        else:
            utt_ids = list(utt_to_path.keys())
        
        # Build samples with phone-level info
        for utt_id in utt_ids:
            if utt_id not in utt_to_path:
                continue
            if utt_id not in scores_data:
                continue
            
            detail = scores_data[utt_id]
            
            # Extract phone-level scores
            # Format: "phones": "W IY0", "phones-accuracy": [2.0, 2.0]
            phone_scores = []
            words_data = []
            
            if 'words' in detail:
                for word_info in detail['words']:
                    word_text = word_info.get('text', '')
                    
                    # Handle accuracy - might be list (from 5 experts) or single value
                    word_acc = word_info.get('accuracy', 5)
                    if isinstance(word_acc, list):
                        word_score = np.mean(word_acc)
                    else:
                        word_score = word_acc
                    
                    word_phones = []
                    
                    # Get phones string and accuracy array
                    phones_str = word_info.get('phones', '')
                    phones_acc = word_info.get('phones-accuracy', [])
                    
                    # Handle case where phones_str might be a list (from 5 experts)
                    if isinstance(phones_str, list):
                        phones_str = phones_str[0] if phones_str else ''
                    
                    # Parse phones string: "W IY0" -> ["W", "IY0"]
                    if phones_str and isinstance(phones_str, str):
                        phone_list = phones_str.split()
                        
                        # Match with accuracy scores
                        for i, phone in enumerate(phone_list):
                            # Remove stress markers and clean
                            phone_clean = ''.join(c for c in phone if not c.isdigit())
                            phone_clean = phone_clean.upper()
                            
                            # Remove special markers {} () []
                            phone_clean = phone_clean.replace('{', '').replace('}', '')
                            phone_clean = phone_clean.replace('(', '').replace(')', '')
                            phone_clean = phone_clean.replace('[', '').replace(']', '')
                            
                            if phone_clean and phone_clean in PHONE_TO_IDX:
                                # Get accuracy score (0-2 scale in dataset)
                                if i < len(phones_acc):
                                    score = phones_acc[i]
                                else:
                                    score = 2.0  # Default to good
                                
                                # Normalize from 0-2 to 0-1
                                normalized_score = score / 2.0
                                
                                phone_scores.append({
                                    'phone': phone_clean,
                                    'phone_idx': PHONE_TO_IDX[phone_clean],
                                    'score': normalized_score
                                })
                                word_phones.append({
                                    'phone': phone_clean,
                                    'score': normalized_score
                                })
                    
                    words_data.append({
                        'text': word_text,
                        'score': word_score / 10.0,
                        'phones': word_phones
                    })
            
            if len(phone_scores) == 0:
                continue
            
            # Debug: print first sample's phone scores
            if len(samples) == 0:
                print(f"📊 Sample phone scores: {[p['score'] for p in phone_scores[:5]]}...")            
            # Handle prosodic (might be list from 5 experts)
            prosodic = detail.get('prosodic', 5)
            if isinstance(prosodic, list):
                prosodic = np.mean(prosodic)
            
            accuracy = detail.get('accuracy', 5)
            if isinstance(accuracy, list):
                accuracy = np.mean(accuracy)
            
            fluency = detail.get('fluency', 5)
            if isinstance(fluency, list):
                fluency = np.mean(fluency)
                
            completeness = detail.get('completeness', 1.0)
            if isinstance(completeness, list):
                completeness = np.mean(completeness)
            
            total = detail.get('total', 5)
            if isinstance(total, list):
                total = np.mean(total)
            
            samples.append({
                'id': utt_id,
                'audio_path': utt_to_path[utt_id],
                'text': detail.get('text', ''),
                'accuracy': accuracy / 10.0,
                'fluency': fluency / 10.0,
                'completeness': completeness if completeness <= 1.0 else completeness / 10.0,
                'prosodic': prosodic / 10.0,
                'total': total / 10.0,
                'phone_scores': phone_scores,
                'words': words_data,
                'num_phones': len(phone_scores)
            })
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict:
        sample = self.samples[idx]
        
        # Load audio
        audio, sr = librosa.load(sample['audio_path'], sr=self.sample_rate)
        
        # Truncate
        if len(audio) > self.max_samples:
            audio = audio[:self.max_samples]
        
        audio_length = len(audio)
        
        # Process with feature extractor
        if self.processor:
            inputs = self.processor(
                audio,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding="max_length",
                max_length=self.max_samples,
                truncation=True
            )
            input_values = inputs.input_values.squeeze(0)
        else:
            if len(audio) < self.max_samples:
                audio = np.pad(audio, (0, self.max_samples - len(audio)))
            input_values = torch.tensor(audio, dtype=torch.float32)
        
        # Create attention mask
        attention_mask = torch.zeros(self.max_samples)
        attention_mask[:audio_length] = 1.0
        
        # Phone-level targets
        # We'll create a simplified target: average phone score for the utterance
        phone_scores_list = [p['score'] for p in sample['phone_scores']]
        avg_phone_score = np.mean(phone_scores_list)
        
        # Create per-phone scores tensor (for detailed training)
        max_phones = 50  # Max phones per utterance
        phone_targets = torch.zeros(max_phones)
        phone_mask = torch.zeros(max_phones)
        
        for i, p in enumerate(sample['phone_scores'][:max_phones]):
            phone_targets[i] = p['score']
            phone_mask[i] = 1.0
        
        return {
            'input_values': input_values,
            'attention_mask': attention_mask,
            'audio_length': audio_length,
            # Utterance-level targets
            'accuracy': torch.tensor(sample['accuracy'], dtype=torch.float),
            'fluency': torch.tensor(sample['fluency'], dtype=torch.float),
            'completeness': torch.tensor(sample['completeness'], dtype=torch.float),
            'prosodic': torch.tensor(sample['prosodic'], dtype=torch.float),
            'total': torch.tensor(sample['total'], dtype=torch.float),
            # Phone-level targets
            'phone_targets': phone_targets,
            'phone_mask': phone_mask,
            'avg_phone_score': torch.tensor(avg_phone_score, dtype=torch.float),
            'num_phones': sample['num_phones'],
            # Metadata
            'text': sample['text'],
            'id': sample['id']
        }


def collate_fn(batch: List[Dict]) -> Dict:
    """Collate with dynamic padding."""
    max_len = max(item['input_values'].shape[0] for item in batch)
    
    input_values = []
    attention_masks = []
    
    for item in batch:
        pad_len = max_len - item['input_values'].shape[0]
        if pad_len > 0:
            input_values.append(F.pad(item['input_values'], (0, pad_len)))
            attention_masks.append(F.pad(item['attention_mask'], (0, pad_len)))
        else:
            input_values.append(item['input_values'])
            attention_masks.append(item['attention_mask'])
    
    return {
        'input_values': torch.stack(input_values),
        'attention_mask': torch.stack(attention_masks),
        'audio_length': torch.tensor([item['audio_length'] for item in batch]),
        'accuracy': torch.stack([item['accuracy'] for item in batch]),
        'fluency': torch.stack([item['fluency'] for item in batch]),
        'completeness': torch.stack([item['completeness'] for item in batch]),
        'prosodic': torch.stack([item['prosodic'] for item in batch]),
        'total': torch.stack([item['total'] for item in batch]),
        'phone_targets': torch.stack([item['phone_targets'] for item in batch]),
        'phone_mask': torch.stack([item['phone_mask'] for item in batch]),
        'avg_phone_score': torch.stack([item['avg_phone_score'] for item in batch]),
        'num_phones': [item['num_phones'] for item in batch],
        'text': [item['text'] for item in batch],
        'id': [item['id'] for item in batch]
    }


# ===================================================================================
# SECTION 5: MODEL
# ===================================================================================
class PhoneLevelScoringModel(nn.Module):
    """
    Phone-level pronunciation scoring model.
    
    Architecture:
    - WavLM backbone (frame-level features)
    - Frame-level scoring head (scores each frame)
    - Utterance-level heads (aggregate scores)
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/wavlm-base-plus",
        hidden_size: int = 768,
        freeze_feature_extractor: bool = True,
        freeze_encoder_layers: int = 6
    ):
        super().__init__()
        
        # Load WavLM
        self.wavlm = WavLMModel.from_pretrained(model_name)
        
        # Freeze layers
        if freeze_feature_extractor:
            for param in self.wavlm.feature_extractor.parameters():
                param.requires_grad = False
            for param in self.wavlm.feature_projection.parameters():
                param.requires_grad = False
        
        if freeze_encoder_layers > 0:
            for i in range(min(freeze_encoder_layers, len(self.wavlm.encoder.layers))):
                for param in self.wavlm.encoder.layers[i].parameters():
                    param.requires_grad = False
        
        # Frame-level scoring head (output score for each frame)
        self.frame_scorer = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        
        # Attention pooling for utterance-level
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.Tanh(),
            nn.Linear(256, 1)
        )
        
        # Utterance-level heads
        self.utterance_heads = nn.ModuleDict({
            'accuracy': self._make_head(hidden_size),
            'fluency': self._make_head(hidden_size),
            'completeness': self._make_head(hidden_size),
            'prosodic': self._make_head(hidden_size),
            'total': self._make_head(hidden_size)
        })
    
    def _make_head(self, input_dim: int) -> nn.Module:
        return nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        input_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Returns:
            frame_scores: [batch, seq_len] - Score for each frame
            utterance_scores: Dict of utterance-level scores
        """
        # Get frame features from WavLM
        outputs = self.wavlm(
            input_values,
            attention_mask=attention_mask,
            output_hidden_states=False,
            return_dict=True
        )
        
        hidden_states = outputs.last_hidden_state  # [batch, seq_len, hidden]
        
        # Frame-level scores
        frame_scores = self.frame_scorer(hidden_states).squeeze(-1)  # [batch, seq_len]
        
        # Create mask for valid frames
        if attention_mask is not None:
            output_lengths = self.wavlm._get_feat_extract_output_lengths(
                attention_mask.sum(dim=-1).long()
            )
            seq_len = hidden_states.shape[1]
            frame_mask = torch.arange(seq_len, device=hidden_states.device)
            frame_mask = frame_mask.unsqueeze(0) < output_lengths.unsqueeze(1)
        else:
            frame_mask = torch.ones(hidden_states.shape[:2], dtype=torch.bool, device=hidden_states.device)
        
        # Attention pooling for utterance representation
        attn_scores = self.attention(hidden_states).squeeze(-1)
        attn_scores = attn_scores.masked_fill(~frame_mask, float('-inf'))
        attn_weights = F.softmax(attn_scores, dim=-1)
        
        utterance_repr = (hidden_states * attn_weights.unsqueeze(-1)).sum(dim=1)
        
        # Utterance-level predictions
        utterance_scores = {}
        for task, head in self.utterance_heads.items():
            utterance_scores[task] = head(utterance_repr).squeeze(-1)
        
        # Average frame score (as proxy for phone score)
        masked_frame_scores = frame_scores.masked_fill(~frame_mask, 0)
        avg_frame_score = masked_frame_scores.sum(dim=1) / frame_mask.sum(dim=1).float()
        
        return {
            'frame_scores': frame_scores,
            'frame_mask': frame_mask,
            'avg_frame_score': avg_frame_score,
            **utterance_scores
        }


# ===================================================================================
# SECTION 6: TRAINING
# ===================================================================================
def train_epoch(model, dataloader, optimizer, scheduler, config, device):
    model.train()
    total_loss = 0
    num_batches = 0
    
    pbar = tqdm(dataloader, desc="Training")
    optimizer.zero_grad()
    
    for step, batch in enumerate(pbar):
        input_values = batch['input_values'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        # Targets
        targets = {
            'accuracy': batch['accuracy'].to(device),
            'fluency': batch['fluency'].to(device),
            'completeness': batch['completeness'].to(device),
            'prosodic': batch['prosodic'].to(device),
            'total': batch['total'].to(device),
            'avg_phone_score': batch['avg_phone_score'].to(device)
        }
        
        # Forward
        outputs = model(input_values, attention_mask)
        
        # Loss: Utterance-level + Phone-level
        mse = nn.MSELoss()
        
        # Utterance losses
        utt_loss = 0
        for task in ['accuracy', 'fluency', 'completeness', 'prosodic', 'total']:
            utt_loss += mse(outputs[task], targets[task])
        utt_loss /= 5
        
        # Phone-level loss (using avg_frame_score as proxy)
        phone_loss = mse(outputs['avg_frame_score'], targets['avg_phone_score'])
        
        # Combined loss
        loss = config.utterance_weight * utt_loss + config.phone_weight * phone_loss
        loss = loss / config.gradient_accumulation_steps
        
        loss.backward()
        
        if (step + 1) % config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        
        total_loss += loss.item() * config.gradient_accumulation_steps
        num_batches += 1
        
        pbar.set_postfix({'loss': total_loss / num_batches})
    
    return total_loss / num_batches


@torch.no_grad()
def evaluate(model, dataloader, device):
    model.eval()
    
    all_preds = {k: [] for k in ['accuracy', 'fluency', 'total', 'avg_frame_score']}
    all_targets = {k: [] for k in ['accuracy', 'fluency', 'total', 'avg_phone_score']}
    
    for batch in tqdm(dataloader, desc="Evaluating"):
        input_values = batch['input_values'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        outputs = model(input_values, attention_mask)
        
        for task in ['accuracy', 'fluency', 'total']:
            all_preds[task].extend(outputs[task].cpu().numpy())
            all_targets[task].extend(batch[task].numpy())
        
        all_preds['avg_frame_score'].extend(outputs['avg_frame_score'].cpu().numpy())
        all_targets['avg_phone_score'].extend(batch['avg_phone_score'].numpy())
    
    # Compute metrics
    metrics = {}
    for task in ['accuracy', 'fluency', 'total']:
        preds = np.array(all_preds[task])
        targets = np.array(all_targets[task])
        metrics[f'{task}_mse'] = mean_squared_error(targets, preds)
        metrics[f'{task}_pearson'], _ = pearsonr(targets, preds)
    
    # Phone-level metrics
    preds = np.array(all_preds['avg_frame_score'])
    targets = np.array(all_targets['avg_phone_score'])
    metrics['phone_mse'] = mean_squared_error(targets, preds)
    metrics['phone_pearson'], _ = pearsonr(targets, preds)
    
    return metrics


def train(config: TrainingConfig):
    print("=" * 80)
    print("🚀 PHONE-LEVEL PRONUNCIATION MODEL TRAINING")
    print("=" * 80)
    
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Load processor
    print("\n📥 Loading Feature Extractor...")
    processor = Wav2Vec2FeatureExtractor.from_pretrained(config.model_name)
    
    # Create datasets
    print("\n📚 Loading Datasets...")
    train_dataset = PhoneLevelDataset(
        data_dir=config.data_dir,
        split='train',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    test_dataset = PhoneLevelDataset(
        data_dir=config.data_dir,
        split='test',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    # DataLoaders - num_workers=0 to avoid multiprocessing issues on Kaggle
    effective_batch = config.batch_size * max(1, n_gpu)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=effective_batch,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=effective_batch,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=True
    )
    
    # Model
    print("\n🏗️ Building Model...")
    model = PhoneLevelScoringModel(
        model_name=config.model_name,
        hidden_size=config.hidden_size,
        freeze_feature_extractor=config.freeze_feature_extractor,
        freeze_encoder_layers=config.freeze_encoder_layers
    )
    model = model.to(device)
    
    if n_gpu > 1:
        print(f"🚀 Using DataParallel with {n_gpu} GPUs")
        model = nn.DataParallel(model)
    
    # Optimizer
    optimizer = AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    
    num_steps = len(train_loader) * config.num_epochs // config.gradient_accumulation_steps
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(num_steps * config.warmup_ratio),
        num_training_steps=num_steps
    )
    
    # Training loop
    best_val_loss = float('inf')
    
    for epoch in range(config.num_epochs):
        print(f"\n📅 Epoch {epoch + 1}/{config.num_epochs}")
        
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, config, device)
        metrics = evaluate(model, test_loader, device)
        
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val - Accuracy Pearson: {metrics['accuracy_pearson']:.4f}")
        print(f"Val - Phone Pearson: {metrics['phone_pearson']:.4f}")
        
        val_loss = metrics['accuracy_mse'] + metrics['phone_mse']
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            print(f"💾 Saving best model...")
            
            model_to_save = model.module if hasattr(model, 'module') else model
            torch.save({
                'model_state_dict': model_to_save.state_dict(),
                'config': config.__dict__,
                'metrics': metrics
            }, os.path.join(config.output_dir, 'best_phone_model.pt'))
    
    print("\n✅ Training Complete!")
    return model


# ===================================================================================
# SECTION 7: INFERENCE
# ===================================================================================
class PhoneLevelScorer:
    """
    Inference class with phone-level scoring.
    
    Usage:
        scorer = PhoneLevelScorer('best_phone_model.pt')
        result = scorer.score(audio_path, text="hello world")
    """
    
    def __init__(self, model_path: str, device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        config = checkpoint['config']
        
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(config['model_name'])
        self.sample_rate = config['sample_rate']
        self.max_audio_length = config['max_audio_length']
        
        self.model = PhoneLevelScoringModel(
            model_name=config['model_name'],
            hidden_size=config['hidden_size']
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Try to load g2p for text-to-phoneme
        try:
            from g2p_en import G2p
            self.g2p = G2p()
        except:
            self.g2p = None
            print("⚠️ g2p_en not available. Install with: pip install g2p-en")
    
    def text_to_phones(self, text: str) -> List[str]:
        """Convert text to phone sequence."""
        if self.g2p is None:
            return []
        
        phones = self.g2p(text)
        # Clean: remove punctuation and numbers
        cleaned = []
        for p in phones:
            if p.isalpha():
                cleaned.append(p.upper())
            elif any(c.isalpha() for c in p):
                cleaned.append(''.join(c for c in p if c.isalpha()).upper())
        return cleaned
    
    @torch.no_grad()
    def score(self, audio_path: str, text: str = None) -> Dict[str, Any]:
        """
        Score pronunciation with phone-level detail.
        
        Args:
            audio_path: Path to audio file
            text: Expected text (e.g., "hello world")
        
        Returns:
            {
                "total": 75.5,
                "accuracy": 72.0,
                "fluency": 78.0,
                "phones": [
                    {"phone": "HH", "score": 85},
                    {"phone": "AH", "score": 62},
                    ...
                ]
            }
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        max_samples = self.max_audio_length * self.sample_rate
        if len(audio) > max_samples:
            audio = audio[:max_samples]
        
        # Process
        inputs = self.processor(audio, sampling_rate=self.sample_rate, return_tensors="pt")
        input_values = inputs.input_values.to(self.device)
        attention_mask = torch.ones_like(input_values)
        
        # Inference
        outputs = self.model(input_values, attention_mask)
        
        # Get utterance scores
        result = {
            'accuracy': round(float(outputs['accuracy'].item() * 100), 1),
            'fluency': round(float(outputs['fluency'].item() * 100), 1),
            'completeness': round(float(outputs['completeness'].item() * 100), 1),
            'prosodic': round(float(outputs['prosodic'].item() * 100), 1),
            'total': round(float(outputs['total'].item() * 100), 1),
        }
        
        # Get frame scores
        frame_scores = outputs['frame_scores'][0].cpu().numpy()
        frame_mask = outputs['frame_mask'][0].cpu().numpy()
        valid_scores = frame_scores[frame_mask]
        
        # If text provided, map to phones
        if text and self.g2p:
            phones = self.text_to_phones(text)
            num_phones = len(phones)
            
            if num_phones > 0:
                # Divide frames among phones (simple uniform mapping)
                frames_per_phone = len(valid_scores) // num_phones
                phone_results = []
                
                for i, phone in enumerate(phones):
                    start = i * frames_per_phone
                    end = start + frames_per_phone if i < num_phones - 1 else len(valid_scores)
                    
                    if start < len(valid_scores):
                        phone_score = np.mean(valid_scores[start:end]) * 100
                        phone_results.append({
                            'phone': phone,
                            'score': round(float(phone_score), 1),
                            'status': 'good' if phone_score >= 70 else 'needs_work'
                        })
                
                result['phones'] = phone_results
        else:
            # No text, just return average
            result['avg_phone_score'] = round(float(np.mean(valid_scores) * 100), 1)
        
        return result


# ===================================================================================
# SECTION 8: MAIN
# ===================================================================================
if __name__ == "__main__":
    print("\n📋 Configuration:")
    for k, v in config.__dict__.items():
        print(f"   {k}: {v}")
    
    if not os.path.exists(config.data_dir):
        print(f"\n⚠️ Data not found: {config.data_dir}")
    else:
        model = train(config)
        
        print("\n🧪 Testing inference...")
        scorer = PhoneLevelScorer(
            os.path.join(config.output_dir, 'best_phone_model.pt')
        )
        
        # Test
        test_files = list(Path(config.data_dir).rglob('*.WAV'))[:3]
        for f in test_files:
            result = scorer.score(str(f), text="hello world")
            print(f"\n{f.name}: {result}")
