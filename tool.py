from io import BytesIO
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SUPPORTED_AUDIO_FORMATS = {".wav", ".flac"}
MAX_AUDIO_BYTES = 4 * 1024 * 1024
MAX_AUDIO_DURATION_SECONDS = 60
TARGET_SAMPLE_RATE = 16_000


class InvalidAudioError(ValueError):
    pass


def validate_audio_file(file_path):
    path = Path(file_path) if file_path else None
    return bool(
        path
        and path.is_file()
        and path.suffix.lower() in SUPPORTED_AUDIO_FORMATS
    )


def get_audio_duration(file_path):
    if not validate_audio_file(file_path):
        return 0.0

    try:
        return round(sf.info(file_path).duration, 2)
    except (RuntimeError, ValueError):
        return 0.0


def decode_audio(audio_bytes, filename):
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_AUDIO_FORMATS:
        raise InvalidAudioError("Upload a WAV or FLAC audio file.")
    if not audio_bytes:
        raise InvalidAudioError("The uploaded audio file is empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise InvalidAudioError("The audio file must be 4 MB or smaller.")

    try:
        samples, sample_rate = sf.read(
            BytesIO(audio_bytes),
            dtype="float32",
            always_2d=True,
        )
    except (RuntimeError, ValueError) as exc:
        raise InvalidAudioError("The audio file could not be decoded.") from exc

    if samples.size == 0 or sample_rate <= 0:
        raise InvalidAudioError("The audio file contains no usable audio.")
    if not np.isfinite(samples).all():
        raise InvalidAudioError("The audio file contains invalid sample values.")

    duration = samples.shape[0] / sample_rate
    if duration < 1:
        raise InvalidAudioError("Audio must be at least 1 second long.")
    if duration > MAX_AUDIO_DURATION_SECONDS:
        raise InvalidAudioError("Audio must be 60 seconds or shorter.")

    mono = samples.mean(axis=1)
    if np.sqrt(np.mean(np.square(mono))) < 1e-4:
        raise InvalidAudioError("The audio is too quiet or silent to analyze.")

    if sample_rate != TARGET_SAMPLE_RATE:
        divisor = gcd(sample_rate, TARGET_SAMPLE_RATE)
        mono = resample_poly(
            mono,
            TARGET_SAMPLE_RATE // divisor,
            sample_rate // divisor,
        ).astype(np.float32, copy=False)

    return mono, duration
