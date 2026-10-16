import os

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

MODEL_ID = os.environ.get(
    "MODEL_ID",
    "MelodyMachine/Deepfake-audio-detection-V2",
)
SAMPLE_RATE = 16_000


class VoiceShieldModel:
    def __init__(self):
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
        self.model = AutoModelForAudioClassification.from_pretrained(MODEL_ID)
        self.model.eval()
        self._class_indices = self._get_class_indices()

    def _get_class_indices(self):
        labels = {
            str(label).casefold(): int(index)
            for index, label in self.model.config.id2label.items()
        }
        fake_index = next(
            (
                index
                for label, index in labels.items()
                if "fake" in label or "synthetic" in label
            ),
            None,
        )
        real_index = next(
            (
                index
                for label, index in labels.items()
                if "real" in label or "human" in label
            ),
            None,
        )
        if fake_index is None or real_index is None:
            raise ValueError(
                f"The configured model has unsupported class labels: {labels}"
            )
        return fake_index, real_index

    def analyze(self, audio):
        inputs = self.feature_extractor(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
            padding=True,
        )

        with torch.inference_mode():
            logits = self.model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)[0].tolist()

        fake_index, real_index = self._class_indices
        return probabilities[fake_index], probabilities[real_index]
