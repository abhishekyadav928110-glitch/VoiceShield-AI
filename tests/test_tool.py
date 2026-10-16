import io
import unittest

import numpy as np
import soundfile as sf

from tool import InvalidAudioError, decode_audio


def make_wav(sample_rate, duration_seconds):
    time = np.arange(int(sample_rate * duration_seconds), dtype=np.float32)
    samples = 0.1 * np.sin(2 * np.pi * 200 * time / sample_rate)
    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    return buffer.getvalue()


class DecodeAudioTests(unittest.TestCase):
    def test_resamples_audio_to_model_sample_rate(self):
        samples, duration = decode_audio(make_wav(8_000, 1), "clip.wav")

        self.assertEqual(samples.shape[0], 16_000)
        self.assertAlmostEqual(duration, 1)

    def test_rejects_unsupported_format(self):
        with self.assertRaisesRegex(InvalidAudioError, "WAV or FLAC"):
            decode_audio(b"audio", "clip.mp3")

    def test_rejects_audio_shorter_than_one_second(self):
        with self.assertRaisesRegex(InvalidAudioError, "at least 1 second"):
            decode_audio(make_wav(16_000, 0.5), "clip.wav")

    def test_rejects_silent_audio(self):
        buffer = io.BytesIO()
        sf.write(
            buffer,
            np.zeros(16_000, dtype=np.float32),
            16_000,
            format="WAV",
        )

        with self.assertRaisesRegex(InvalidAudioError, "too quiet or silent"):
            decode_audio(buffer.getvalue(), "silent.wav")


if __name__ == "__main__":
    unittest.main()
