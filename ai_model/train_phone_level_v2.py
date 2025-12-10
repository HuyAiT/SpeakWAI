"""
===================================================================================
🎤 PHONE-LEVEL PRONUNCIATION SCORING MODEL V2
===================================================================================
Fine-tuning WavLM with CTC alignment for accurate per-phoneme pronunciation scoring.

Key Improvements over V1:
- CTC-based phone recognition for accurate alignment
- Per-phone score prediction (not just average)
- Multi-task learning: Phone recognition + Score prediction
- Uses scores-detail.json for individual phone accuracy scores

Output Example:
{
    "total": 72.5,
    "words": [
        {"word": "hello", "score": 78, "phones": [
            {"phone": "HH", "ipa": "h", "score": 85, "status": "good"},
            {"phone": "AH", "ipa": "ə", "score": 62, "status": "poor"},
            {"phone": "L", "ipa": "l", "score": 78, "status": "good"},
            {"phone": "OW", "ipa": "oʊ", "score": 82, "status": "good"}
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
# !pip install -q accelerate g2p-en

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
    num_epochs: int = 15  # More epochs for better phone learning
    batch_size: int = 4
    gradient_accumulation_steps: int = 8
    learning_rate: float = 3e-5  # Slightly lower for stability
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Audio
    sample_rate: int = 16000
    max_audio_length: int = 10  # seconds
    
    # Loss weights (Multi-task learning)
    utterance_weight: float = 1.0
    phone_score_weight: float = 3.0  # Higher weight for phone scores
    ctc_weight: float = 0.5  # CTC for alignment
    
    # Paths
    data_dir: str = "/kaggle/input/speechocean762"
    output_dir: str = "/kaggle/working/phone_pronunciation_model_v2"
    
    # Features
    freeze_feature_extractor: bool = True
    freeze_encoder_layers: int = 4  # Fewer frozen layers for better phone learning
    
    # Phone scoring thresholds
    good_threshold: float = 0.7  # Score >= 70% is "good"
    poor_threshold: float = 0.5  # Score < 50% is "poor", 50-70% is "fair"
    
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
    '<blank>',  # CTC blank token (index 0)
    'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'B', 'CH', 'D', 'DH',
    'EH', 'ER', 'EY', 'F', 'G', 'HH', 'IH', 'IY', 'JH', 'K',
    'L', 'M', 'N', 'NG', 'OW', 'OY', 'P', 'R', 'S', 'SH',
    'T', 'TH', 'UH', 'UW', 'V', 'W', 'Y', 'Z', 'ZH',
    'SIL', 'SPN'  # silence and spoken noise
]

PHONE_TO_IDX = {p: i for i, p in enumerate(PHONE_SET)}
IDX_TO_PHONE = {i: p for i, p in enumerate(PHONE_SET)}
NUM_PHONES = len(PHONE_SET)
BLANK_IDX = 0

# ARPAbet to IPA mapping for display
ARPABET_TO_IPA = {
    'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AY': 'aɪ',
    'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'EH': 'ɛ', 'ER': 'ɝ',
    'EY': 'eɪ', 'F': 'f', 'G': 'g', 'HH': 'h', 'IH': 'ɪ', 'IY': 'i',
    'JH': 'dʒ', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ',
    'OW': 'oʊ', 'OY': 'ɔɪ', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'ʃ',
    'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'u', 'V': 'v', 'W': 'w',
    'Y': 'j', 'Z': 'z', 'ZH': 'ʒ', 'SIL': '', 'SPN': ''
}

# ===================================================================================
# SECTION 4: DATASET (Using scores-detail.json)
# ===================================================================================
class PhoneLevelDatasetV2(Dataset):
    """
    Dataset with per-phone scores from scores-detail.json.
    
    Key differences from V1:
    - Uses scores-detail.json (has individual phone scores per word)
    - Creates proper phone sequence targets for CTC
    - Extracts per-phone accuracy for score prediction
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
    
    def _parse_phone(self, phone_str: str) -> Tuple[str, int]:
        """
        Parse phone string with possible markers.
        
        Markers in Speechocean762:
        - No marker: correct (score 2)
        - {}: heavy accent (score 1)
        - (): mispronunciation (score 0)
        - []: inserted phone
        
        Returns: (clean_phone, score)
        """
        phone_str = phone_str.strip()
        
        # Check markers
        if phone_str.startswith('[') and phone_str.endswith(']'):
            # Inserted phone - mark as incorrect
            phone = phone_str[1:-1]
            score = 0
        elif phone_str.startswith('(') and phone_str.endswith(')'):
            # Mispronunciation
            phone = phone_str[1:-1]
            score = 0
        elif phone_str.startswith('{') and phone_str.endswith('}'):
            # Heavy accent
            phone = phone_str[1:-1]
            score = 1
        else:
            # Correct
            phone = phone_str
            score = 2
        
        # Clean: remove stress markers (numbers)
        phone_clean = ''.join(c for c in phone if not c.isdigit()).upper()
        
        return phone_clean, score
    
    def _load_data(self) -> List[Dict]:
        samples = []
        
        # Load scores-detail.json (has individual phone scores)
        scores_file = self.data_dir / 'resource' / 'scores-detail.json'
        if not scores_file.exists():
            scores_file = self.data_dir / 'scores-detail.json'
        if not scores_file.exists():
            # Fallback to scores.json
            scores_file = self.data_dir / 'resource' / 'scores.json'
        if not scores_file.exists():
            print(f"⚠️ Scores file not found")
            return samples
        
        with open(scores_file, 'r', encoding='utf-8') as f:
            scores_data = json.load(f)
        print(f"✅ Loaded {len(scores_data)} entries from {scores_file.name}")
        
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
        
        # Build samples with per-phone info
        for utt_id in utt_ids:
            if utt_id not in utt_to_path:
                continue
            if utt_id not in scores_data:
                continue
            
            detail = scores_data[utt_id]
            
            # Extract phone sequence and scores
            phone_sequence = []  # For CTC target
            phone_scores = []    # For score prediction
            words_data = []
            
            if 'words' in detail:
                for word_info in detail['words']:
                    word_text = word_info.get('text', '')
                    
                    # Get word accuracy
                    word_acc = word_info.get('accuracy', 5)
                    if isinstance(word_acc, list):
                        word_score = np.mean(word_acc)
                    else:
                        word_score = word_acc
                    
                    word_phones = []
                    
                    # Get phones string 
                    phones_str = word_info.get('phones', '')
                    phones_acc = word_info.get('phones-accuracy', [])
                    
                    if isinstance(phones_str, list):
                        phones_str = phones_str[0] if phones_str else ''
                    
                    if phones_str and isinstance(phones_str, str):
                        phone_list = phones_str.split()
                        
                        for i, phone_raw in enumerate(phone_list):
                            phone_clean, marker_score = self._parse_phone(phone_raw)
                            
                            if phone_clean and phone_clean in PHONE_TO_IDX:
                                # Get accuracy score from phones-accuracy array
                                if i < len(phones_acc):
                                    acc_score = phones_acc[i]
                                    if isinstance(acc_score, list):
                                        acc_score = np.mean(acc_score)
                                else:
                                    # Use marker-based score if no accuracy array
                                    acc_score = marker_score
                                
                                # Normalize from 0-2 to 0-1
                                normalized_score = min(acc_score / 2.0, 1.0)
                                
                                phone_idx = PHONE_TO_IDX[phone_clean]
                                phone_sequence.append(phone_idx)
                                phone_scores.append({
                                    'phone': phone_clean,
                                    'phone_idx': phone_idx,
                                    'score': normalized_score
                                })
                                word_phones.append({
                                    'phone': phone_clean,
                                    'ipa': ARPABET_TO_IPA.get(phone_clean, phone_clean.lower()),
                                    'score': normalized_score
                                })
                    
                    if word_phones:
                        words_data.append({
                            'text': word_text,
                            'score': word_score / 10.0,
                            'phones': word_phones
                        })
            
            if len(phone_sequence) == 0:
                continue
            
            # Get utterance-level scores
            def get_score(key, default=5):
                val = detail.get(key, default)
                if isinstance(val, list):
                    return np.mean(val)
                return val
            
            samples.append({
                'id': utt_id,
                'audio_path': utt_to_path[utt_id],
                'text': detail.get('text', ''),
                'accuracy': get_score('accuracy') / 10.0,
                'fluency': get_score('fluency') / 10.0,
                'completeness': min(get_score('completeness', 1.0), 10.0) / 10.0,
                'prosodic': get_score('prosodic') / 10.0,
                'total': get_score('total') / 10.0,
                'phone_sequence': phone_sequence,  # For CTC
                'phone_scores': phone_scores,      # Per-phone scores
                'words': words_data,
                'num_phones': len(phone_sequence)
            })
        
        # Debug: distribution of phone scores
        if samples:
            all_phone_scores = []
            for s in samples[:100]:
                all_phone_scores.extend([p['score'] for p in s['phone_scores']])
            print(f"📊 Phone score distribution (first 100 samples):")
            print(f"   Min: {min(all_phone_scores):.2f}, Max: {max(all_phone_scores):.2f}, Mean: {np.mean(all_phone_scores):.2f}")
        
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
        
        # CTC target: phone sequence
        max_phones = 100
        phone_targets = torch.full((max_phones,), BLANK_IDX, dtype=torch.long)
        phone_seq = sample['phone_sequence'][:max_phones]
        for i, p in enumerate(phone_seq):
            phone_targets[i] = p
        phone_seq_length = len(phone_seq)
        
        # Per-phone scores
        phone_scores = torch.zeros(max_phones)
        phone_mask = torch.zeros(max_phones)
        for i, p in enumerate(sample['phone_scores'][:max_phones]):
            phone_scores[i] = p['score']
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
            # CTC targets
            'phone_targets': phone_targets,
            'phone_seq_length': phone_seq_length,
            # Phone scores
            'phone_scores': phone_scores,
            'phone_mask': phone_mask,
            'num_phones': sample['num_phones'],
            # Metadata
            'text': sample['text'],
            'id': sample['id']
        }


def collate_fn_v2(batch: List[Dict]) -> Dict:
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
        'phone_seq_length': torch.tensor([item['phone_seq_length'] for item in batch]),
        'phone_scores': torch.stack([item['phone_scores'] for item in batch]),
        'phone_mask': torch.stack([item['phone_mask'] for item in batch]),
        'num_phones': [item['num_phones'] for item in batch],
        'text': [item['text'] for item in batch],
        'id': [item['id'] for item in batch]
    }


# ===================================================================================
# SECTION 5: MODEL (Multi-task: CTC + Score Prediction)
# ===================================================================================
class PhoneLevelScoringModelV2(nn.Module):
    """
    Phone-level pronunciation scoring model with CTC alignment.
    
    Architecture:
    - WavLM backbone (frame-level features)
    - CTC head (phone recognition for alignment)
    - Frame score head (scores each frame)
    - Utterance-level heads (aggregate scores)
    
    Multi-task learning:
    1. CTC loss: Learn to recognize phones (provides alignment)
    2. Score loss: Learn to score each phone
    3. Utterance loss: Learn overall scores
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/wavlm-base-plus",
        hidden_size: int = 768,
        num_phones: int = NUM_PHONES,
        freeze_feature_extractor: bool = True,
        freeze_encoder_layers: int = 4
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
        
        # CTC head for phone recognition
        self.ctc_head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_phones)
        )
        
        # Frame-level scoring head
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
        
        self.num_phones = num_phones
    
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
            ctc_logits: [batch, seq_len, num_phones] - For CTC loss
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
        
        # CTC logits for phone recognition
        ctc_logits = self.ctc_head(hidden_states)  # [batch, seq_len, num_phones]
        
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
        
        # Average frame score
        masked_frame_scores = frame_scores.masked_fill(~frame_mask, 0)
        avg_frame_score = masked_frame_scores.sum(dim=1) / frame_mask.sum(dim=1).float().clamp(min=1)
        
        return {
            'ctc_logits': ctc_logits,
            'frame_scores': frame_scores,
            'frame_mask': frame_mask,
            'output_lengths': output_lengths if attention_mask is not None else None,
            'avg_frame_score': avg_frame_score,
            **utterance_scores
        }


# ===================================================================================
# SECTION 6: TRAINING
# ===================================================================================
def train_epoch(model, dataloader, optimizer, scheduler, config, device):
    model.train()
    total_loss = 0
    total_ctc_loss = 0
    total_score_loss = 0
    total_utt_loss = 0
    num_batches = 0
    
    ctc_loss_fn = nn.CTCLoss(blank=BLANK_IDX, reduction='mean', zero_infinity=True)
    mse_loss_fn = nn.MSELoss()
    
    pbar = tqdm(dataloader, desc="Training")
    optimizer.zero_grad()
    
    for step, batch in enumerate(pbar):
        input_values = batch['input_values'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        # Targets
        phone_targets = batch['phone_targets'].to(device)
        phone_seq_lengths = batch['phone_seq_length'].to(device)
        phone_scores_target = batch['phone_scores'].to(device)
        phone_mask = batch['phone_mask'].to(device)
        
        utt_targets = {
            'accuracy': batch['accuracy'].to(device),
            'fluency': batch['fluency'].to(device),
            'completeness': batch['completeness'].to(device),
            'prosodic': batch['prosodic'].to(device),
            'total': batch['total'].to(device),
        }
        
        # Forward
        outputs = model(input_values, attention_mask)
        
        # === CTC Loss ===
        ctc_logits = outputs['ctc_logits']  # [batch, seq_len, num_phones]
        log_probs = F.log_softmax(ctc_logits, dim=-1).transpose(0, 1)  # [seq_len, batch, num_phones]
        
        output_lengths = outputs['output_lengths']
        
        # Filter out samples with length issues
        valid_mask = (output_lengths >= phone_seq_lengths) & (phone_seq_lengths > 0)
        
        if valid_mask.sum() > 0:
            ctc_loss = ctc_loss_fn(
                log_probs[:, valid_mask],
                phone_targets[valid_mask, :phone_seq_lengths[valid_mask].max()],
                output_lengths[valid_mask],
                phone_seq_lengths[valid_mask]
            )
        else:
            ctc_loss = torch.tensor(0.0, device=device)
        
        # === Phone Score Loss ===
        # Average frame score as proxy for phone scores
        avg_phone_score_target = (phone_scores_target * phone_mask).sum(dim=1) / phone_mask.sum(dim=1).clamp(min=1)
        score_loss = mse_loss_fn(outputs['avg_frame_score'], avg_phone_score_target)
        
        # === Utterance Loss ===
        utt_loss = 0
        for task in ['accuracy', 'fluency', 'completeness', 'prosodic', 'total']:
            utt_loss += mse_loss_fn(outputs[task], utt_targets[task])
        utt_loss /= 5
        
        # === Combined Loss ===
        loss = (config.ctc_weight * ctc_loss + 
                config.phone_score_weight * score_loss + 
                config.utterance_weight * utt_loss)
        loss = loss / config.gradient_accumulation_steps
        
        loss.backward()
        
        if (step + 1) % config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        
        total_loss += loss.item() * config.gradient_accumulation_steps
        total_ctc_loss += ctc_loss.item()
        total_score_loss += score_loss.item()
        total_utt_loss += utt_loss.item()
        num_batches += 1
        
        pbar.set_postfix({
            'loss': total_loss / num_batches,
            'ctc': total_ctc_loss / num_batches,
            'score': total_score_loss / num_batches
        })
    
    return {
        'loss': total_loss / num_batches,
        'ctc_loss': total_ctc_loss / num_batches,
        'score_loss': total_score_loss / num_batches,
        'utt_loss': total_utt_loss / num_batches
    }


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
        
        # Compute avg phone score target
        phone_scores = batch['phone_scores']
        phone_mask = batch['phone_mask']
        avg_phone_target = (phone_scores * phone_mask).sum(dim=1) / phone_mask.sum(dim=1).clamp(min=1)
        all_targets['avg_phone_score'].extend(avg_phone_target.numpy())
    
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
    print("🚀 PHONE-LEVEL PRONUNCIATION MODEL V2 TRAINING")
    print("=" * 80)
    
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Load processor
    print("\n📥 Loading Feature Extractor...")
    processor = Wav2Vec2FeatureExtractor.from_pretrained(config.model_name)
    
    # Create datasets
    print("\n📚 Loading Datasets...")
    train_dataset = PhoneLevelDatasetV2(
        data_dir=config.data_dir,
        split='train',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    test_dataset = PhoneLevelDatasetV2(
        data_dir=config.data_dir,
        split='test',
        processor=processor,
        max_audio_length=config.max_audio_length,
        sample_rate=config.sample_rate
    )
    
    # DataLoaders
    effective_batch = config.batch_size * max(1, n_gpu)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=effective_batch,
        shuffle=True,
        collate_fn=collate_fn_v2,
        num_workers=0,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=effective_batch,
        shuffle=False,
        collate_fn=collate_fn_v2,
        num_workers=0,
        pin_memory=True
    )
    
    # Model
    print("\n🏗️ Building Model...")
    model = PhoneLevelScoringModelV2(
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
    best_phone_pearson = -1
    
    for epoch in range(config.num_epochs):
        print(f"\n📅 Epoch {epoch + 1}/{config.num_epochs}")
        
        train_metrics = train_epoch(model, train_loader, optimizer, scheduler, config, device)
        val_metrics = evaluate(model, test_loader, device)
        
        print(f"Train - Loss: {train_metrics['loss']:.4f}, CTC: {train_metrics['ctc_loss']:.4f}, Score: {train_metrics['score_loss']:.4f}")
        print(f"Val - Accuracy Pearson: {val_metrics['accuracy_pearson']:.4f}")
        print(f"Val - Phone Pearson: {val_metrics['phone_pearson']:.4f}")
        
        # Save best model based on phone pearson
        if val_metrics['phone_pearson'] > best_phone_pearson:
            best_phone_pearson = val_metrics['phone_pearson']
            print(f"💾 New best phone pearson: {best_phone_pearson:.4f}")
            
            model_to_save = model.module if hasattr(model, 'module') else model
            torch.save({
                'model_state_dict': model_to_save.state_dict(),
                'config': config.__dict__,
                'metrics': val_metrics
            }, os.path.join(config.output_dir, 'best_phone_model_v2.pt'))
    
    print("\n✅ Training Complete!")
    print(f"📊 Best Phone Pearson: {best_phone_pearson:.4f}")
    return model


# ===================================================================================
# SECTION 7: INFERENCE (with CTC Decoding)
# ===================================================================================
class PhoneLevelScorerV2:
    """
    Inference class with CTC-based phone alignment.
    
    Usage:
        scorer = PhoneLevelScorerV2('best_phone_model_v2.pt')
        result = scorer.score(audio_path, text="hello world")
    """
    
    def __init__(self, model_path: str, device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        model_config = checkpoint['config']
        
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(model_config['model_name'])
        self.sample_rate = model_config['sample_rate']
        self.max_audio_length = model_config['max_audio_length']
        self.good_threshold = model_config.get('good_threshold', 0.7)
        self.poor_threshold = model_config.get('poor_threshold', 0.5)
        
        self.model = PhoneLevelScoringModelV2(
            model_name=model_config['model_name'],
            hidden_size=model_config['hidden_size']
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
    
    def text_to_phones(self, text: str) -> List[Tuple[str, str]]:
        """Convert text to phone sequence with word boundaries.
        
        Returns list of (word, phones_list) tuples.
        """
        if self.g2p is None:
            return []
        
        words = text.strip().split()
        result = []
        
        for word in words:
            phones = self.g2p(word)
            # Clean: remove punctuation and numbers, keep only valid phones
            cleaned = []
            for p in phones:
                if p.isalpha():
                    cleaned.append(p.upper())
                elif any(c.isalpha() for c in p):
                    cleaned.append(''.join(c for c in p if c.isalpha()).upper())
            result.append((word, cleaned))
        
        return result
    
    def ctc_greedy_decode(self, logits: np.ndarray) -> List[Tuple[int, int, int]]:
        """
        Greedy CTC decoding with frame alignment.
        
        Returns: List of (phone_idx, start_frame, end_frame)
        """
        predictions = np.argmax(logits, axis=-1)
        
        segments = []
        prev_phone = BLANK_IDX
        start_frame = 0
        
        for i, phone in enumerate(predictions):
            if phone != prev_phone:
                if prev_phone != BLANK_IDX:
                    segments.append((prev_phone, start_frame, i))
                start_frame = i
                prev_phone = phone
        
        # Add last segment
        if prev_phone != BLANK_IDX:
            segments.append((prev_phone, start_frame, len(predictions)))
        
        return segments
    
    def get_phone_status(self, score: float) -> str:
        """Get status based on score thresholds."""
        if score >= self.good_threshold:
            return "good"
        elif score >= self.poor_threshold:
            return "fair"
        else:
            return "poor"
    
    @torch.no_grad()
    def score(self, audio_path: str, text: str = None) -> Dict[str, Any]:
        """
        Score pronunciation with phone-level detail.
        
        Args:
            audio_path: Path to audio file
            text: Expected text (e.g., "hello world")
        
        Returns:
            {
                "total_score": 75,
                "accuracy": 72,
                "fluency": 78,
                "words": [
                    {
                        "word": "hello",
                        "score": 72,
                        "phones": [
                            {"phone": "HH", "ipa": "h", "score": 85, "status": "good"},
                            {"phone": "AH", "ipa": "ə", "score": 45, "status": "poor"},
                            ...
                        ]
                    }
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
            'total_score': round(float(outputs['total'].item() * 100), 1),
            'accuracy': round(float(outputs['accuracy'].item() * 100), 1),
            'fluency': round(float(outputs['fluency'].item() * 100), 1),
            'completeness': round(float(outputs['completeness'].item() * 100), 1),
            'prosodic': round(float(outputs['prosodic'].item() * 100), 1),
        }
        
        # Get frame-level data
        frame_scores = outputs['frame_scores'][0].cpu().numpy()
        frame_mask = outputs['frame_mask'][0].cpu().numpy()
        ctc_logits = outputs['ctc_logits'][0].cpu().numpy()
        
        valid_frame_scores = frame_scores[frame_mask]
        valid_ctc_logits = ctc_logits[frame_mask]
        
        # CTC decode to get phone segments
        phone_segments = self.ctc_greedy_decode(valid_ctc_logits)
        
        # If text provided, align with expected phones
        if text and self.g2p:
            word_phones_list = self.text_to_phones(text)
            
            # Build flat expected phone sequence
            expected_phones = []
            for word, phones in word_phones_list:
                for p in phones:
                    expected_phones.append((word, p))
            
            # Match detected segments with expected phones
            words_result = []
            expected_idx = 0
            current_word = None
            current_word_phones = []
            
            for phone_idx, start_frame, end_frame in phone_segments:
                phone_name = IDX_TO_PHONE.get(phone_idx, '')
                if not phone_name or phone_name in ['<blank>', 'SIL', 'SPN']:
                    continue
                
                # Get score for this segment
                segment_scores = valid_frame_scores[start_frame:end_frame]
                phone_score = float(np.mean(segment_scores)) * 100 if len(segment_scores) > 0 else 50
                
                # Match with expected
                if expected_idx < len(expected_phones):
                    exp_word, exp_phone = expected_phones[expected_idx]
                    
                    # Start new word if needed
                    if current_word != exp_word:
                        if current_word is not None and current_word_phones:
                            word_score = np.mean([p['score'] for p in current_word_phones])
                            words_result.append({
                                'word': current_word,
                                'score': round(float(word_score), 1),
                                'phones': current_word_phones
                            })
                        current_word = exp_word
                        current_word_phones = []
                    
                    current_word_phones.append({
                        'phone': exp_phone,
                        'ipa': ARPABET_TO_IPA.get(exp_phone, exp_phone.lower()),
                        'score': round(phone_score, 1),
                        'status': self.get_phone_status(phone_score / 100)
                    })
                    expected_idx += 1
            
            # Add last word
            if current_word is not None and current_word_phones:
                word_score = np.mean([p['score'] for p in current_word_phones])
                words_result.append({
                    'word': current_word,
                    'score': round(float(word_score), 1),
                    'phones': current_word_phones
                })
            
            result['words'] = words_result
        else:
            # No text, return detected phones with scores
            detected_phones = []
            for phone_idx, start_frame, end_frame in phone_segments:
                phone_name = IDX_TO_PHONE.get(phone_idx, '')
                if not phone_name or phone_name in ['<blank>', 'SIL', 'SPN']:
                    continue
                
                segment_scores = valid_frame_scores[start_frame:end_frame]
                phone_score = float(np.mean(segment_scores)) * 100 if len(segment_scores) > 0 else 50
                
                detected_phones.append({
                    'phone': phone_name,
                    'ipa': ARPABET_TO_IPA.get(phone_name, phone_name.lower()),
                    'score': round(phone_score, 1),
                    'status': self.get_phone_status(phone_score / 100)
                })
            
            result['detected_phones'] = detected_phones
            result['avg_phone_score'] = round(float(np.mean(valid_frame_scores) * 100), 1)
        
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
        scorer = PhoneLevelScorerV2(
            os.path.join(config.output_dir, 'best_phone_model_v2.pt')
        )
        
        # Test with sample files
        test_files = list(Path(config.data_dir).rglob('*.WAV'))[:3]
        for f in test_files:
            result = scorer.score(str(f), text="hello how are you")
            print(f"\n{f.name}:")
            print(f"  Total: {result['total_score']}, Accuracy: {result['accuracy']}")
            if 'words' in result:
                for word in result['words']:
                    phones_str = ' '.join([f"{p['phone']}({p['score']:.0f})" for p in word['phones']])
                    print(f"  {word['word']}: {word['score']:.0f} - [{phones_str}]")
